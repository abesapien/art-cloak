import os
import io
import logging
import uuid
import requests
from openai import OpenAI
from typing import Optional, List
import base64
from PIL import Image

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for interacting with OpenAI's API to generate and edit images."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.prompt = """Re-create this exact image in Studio Ghibli style. 
        
DO NOT change the composition, subjects or elements.
DO NOT add new elements that weren't in the original.
DO KEEP all subjects in their exact positions.
DO KEEP the same lighting, time of day, and weather as the original.
DO APPLY Studio Ghibli's distinctive hand-drawn animation style, soft watercolor backgrounds, and attention to natural details.
        
The result should look like a frame from a Studio Ghibli film while being immediately recognizable as the same image."""
        
        # Keep track of the last analysis
        self.last_analysis = None
        self.last_analysis_file = None
    
    def stylize_image(self, image_data: bytes) -> Optional[bytes]:
        """
        Analyzes an image using GPT-4 Vision and then generates a stylized version with DALL-E.
        Returns the stylized image.
        """
        try:
            # Debug the image
            logger.info(f"Image data length: {len(image_data)} bytes")
            
            # Try to open and verify the image using PIL first
            try:
                with io.BytesIO(image_data) as check_stream:
                    check_img = Image.open(check_stream)
                    logger.info(f"Image verified: {check_img.format}, Size: {check_img.size}, Mode: {check_img.mode}")
            except Exception as e:
                logger.error(f"Invalid image data: {e}")
                raise ValueError("Invalid image data received")
                
            # Encode image to base64 for GPT-4 Vision
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Use GPT-4 Vision to analyze the image and get a detailed description
            logger.info("Using GPT-4 Vision to analyze the image")
            vision_prompt = """
            Analyze this image in extreme detail and provide a thorough description that includes:

            1. COMPOSITION: Describe the exact layout, framing, perspective, and spatial arrangement of all elements
            2. SUBJECTS: Identify all main subjects, their positions, proportions, poses, and relationships
            3. COLORS: Note the specific color palette, tones, saturation, and any color themes or gradients
            4. LIGHTING: Detail the light sources, shadows, highlights, time of day, and overall illumination
            5. BACKGROUND: Describe all background elements, landscapes, architecture, natural features
            6. ATMOSPHERE: Explain the mood, emotional tone, weather conditions, and atmospheric effects
            7. DETAILS: Catalog all small details, textures, patterns, and distinctive features

            Make your description extremely detailed so it could be used to recreate the image.
            Focus only on what is actually visible in the image, not what might be implied.
            """
            
            vision_messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
            
            # Try with gpt-4-vision-preview first, fallback to gpt-4o if needed
            try:
                vision_response = self.client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=vision_messages,
                    max_tokens=2000
                )
            except Exception as vision_err:
                # Fall back to gpt-4o if vision-preview is not available
                logger.warning(f"Error with gpt-4-vision-preview: {vision_err}. Falling back to gpt-4o.")
                vision_response = self.client.chat.completions.create(
                    model="gpt-4o",  # Fallback to GPT-4o which also has vision capabilities
                    messages=vision_messages,
                    max_tokens=2000
                )
            
            # Extract and save the image description
            image_description = vision_response.choices[0].message.content
            logger.info(f"Image description generated: {len(image_description)} chars")
            logger.info(f"Full GPT-4 Vision description: \n{image_description}\n")
            
            # Save the description to a file
            log_file_path = os.path.join(os.getcwd(), "temp", f"image_description_{uuid.uuid4()}.txt")
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            
            with open(log_file_path, "w") as f:
                f.write(f"IMAGE ANALYSIS:\n{image_description}")
            
            # Store the analysis for API access
            self.last_analysis = image_description
            self.last_analysis_file = log_file_path
            
            # Print the image description
            print("\n=== IMAGE ANALYSIS RESULT ===")
            print(f"Description saved to: {log_file_path}")
            print("\nIMAGE DESCRIPTION:")
            print(image_description[:500] + "..." if len(image_description) > 500 else image_description)
            print("\n==============================\n")
            
            # Step 2: Generate a stylized version using the latest models
            logger.info("Generating stylized image with latest OpenAI models")
            
            # Create a prompt for image generation including the original image description
            stylize_prompt = f"{self.prompt}\n\nReference details from the original image: {image_description[:500]}"
            
            # Log the prompt for debugging
            prompt_log_path = os.path.join(os.getcwd(), "temp", f"prompt_log_{uuid.uuid4()}.txt")
            with open(prompt_log_path, "w") as f:
                f.write(f"IMAGE GENERATION PROMPT:\n{stylize_prompt}")
            
            # Use GPT-image-1 model with images.edit
            logger.info("Generating stylized image with GPT-image-1 using images.edit")
            
            # Create BytesIO objects from the image data
            image_io = io.BytesIO(image_data)
            
            # Call the OpenAI API with images.edit
            try:
                edit_response = self.client.images.edit(
                    model="gpt-image-1",
                    image=image_io,  # Pass the BytesIO object directly
                    prompt=stylize_prompt
                )
                
                # Extract the base64-encoded image data
                if hasattr(edit_response.data[0], 'b64_json') and edit_response.data[0].b64_json:
                    logger.info("Received base64-encoded image from GPT-image-1")
                    image_base64 = edit_response.data[0].b64_json
                    stylized_image_data = base64.b64decode(image_base64)
                # If we got a URL instead
                elif hasattr(edit_response.data[0], 'url') and edit_response.data[0].url:
                    logger.info(f"Received image URL: {edit_response.data[0].url}")
                    response = requests.get(edit_response.data[0].url)
                    response.raise_for_status()
                    stylized_image_data = response.content
                else:
                    logger.error("No image data or URL found in response")
                    raise ValueError("Invalid response from GPT-image-1: no image data")
                
                logger.info("Successfully generated image with GPT-image-1")
            except Exception as e:
                logger.error(f"Error using GPT-image-1: {e}")
                # Re-raise the exception to be handled by the caller
                raise
            
            logger.info(f"Stylized image generated successfully, size: {len(stylized_image_data)} bytes")
            
            # Return the stylized image
            return stylized_image_data
            
        except Exception as e:
            logger.error(f"Error in stylize_image: {e}", exc_info=True)
            raise
            
    def generate_image_from_references(self, reference_images: List[bytes], prompt: str) -> Optional[bytes]:
        """
        Generates a new image by combining elements from multiple reference images.
        
        Args:
            reference_images: List of image data as bytes
            prompt: The generation prompt
            
        Returns:
            The generated image data as bytes
        """
        try:
            logger.info(f"Generating image from {len(reference_images)} reference images")
            
            # Log the prompt
            prompt_log_path = os.path.join(os.getcwd(), "temp", f"prompt_log_{uuid.uuid4()}.txt")
            os.makedirs(os.path.dirname(prompt_log_path), exist_ok=True)
            with open(prompt_log_path, "w") as f:
                f.write(f"IMAGE GENERATION PROMPT:\n{prompt}")
            
            logger.info(f"Saved generation prompt to: {prompt_log_path}")
            
            # Save the image to a temporary file with proper format
            # Make sure it's a square PNG to ensure compatibility
            try:
                # Open the image with PIL
                image_data = reference_images[0]
                img = Image.open(io.BytesIO(image_data))
                logger.info(f"Original image: {img.format}, {img.size}, {img.mode}")
                
                # Convert to RGB if needed
                if img.mode != "RGB":
                    img = img.convert("RGB")
                    logger.info("Converted image to RGB mode")
                
                # Resize to 1024x1024
                width, height = img.size
                if width != 1024 or height != 1024:
                    # Create a new white background
                    new_img = Image.new("RGB", (1024, 1024), (255, 255, 255))
                    # Calculate position to paste (center)
                    x = (1024 - width) // 2
                    y = (1024 - height) // 2
                    # Paste the resized image
                    new_img.paste(img, (x, y))
                    img = new_img
                    logger.info("Resized image to 1024x1024 with white background")
                
                # Save as PNG
                temp_image_path = os.path.join(os.getcwd(), "temp", f"temp_image_{uuid.uuid4()}.png")
                img.save(temp_image_path, format="PNG")
                
                logger.info(f"Saved temporary image for OpenAI API at: {temp_image_path}")
                
                # File size check
                file_size = os.path.getsize(temp_image_path)
                logger.info(f"Temporary file size: {file_size} bytes")
                
                # Verify the file was saved correctly
                verify_img = Image.open(temp_image_path)
                logger.info(f"Verified saved image: {verify_img.format}, {verify_img.size}, {verify_img.mode}")
                
            except Exception as e:
                logger.error(f"Error preparing image: {e}")
                raise ValueError(f"Failed to prepare image: {e}")
            
            # Call the OpenAI API with images.edit
            try:
                logger.info("Calling GPT-image-1 to generate image")
                
                # Use OpenAI's file handling
                # Create an edit request
                try:
                    # Use a context manager to ensure the file is properly opened and closed
                    with open(temp_image_path, "rb") as img_file:
                        logger.info("Sending file to OpenAI API")
                        edit_response = self.client.images.edit(
                            model="gpt-image-1",
                            image=img_file,
                            prompt=prompt
                        )
                except Exception as api_error:
                    logger.error(f"OpenAI API error: {api_error}")
                    # Print more details about the error
                    import traceback
                    logger.error(traceback.format_exc())
                    raise
                
                # Clean up temporary file
                os.remove(temp_image_path)
                logger.info(f"Removed temporary image file: {temp_image_path}")
                
                # Extract the base64-encoded image data
                if hasattr(edit_response.data[0], 'b64_json') and edit_response.data[0].b64_json:
                    logger.info("Received base64-encoded image from GPT-image-1")
                    image_base64 = edit_response.data[0].b64_json
                    generated_image_data = base64.b64decode(image_base64)
                # If we got a URL instead
                elif hasattr(edit_response.data[0], 'url') and edit_response.data[0].url:
                    logger.info(f"Received image URL: {edit_response.data[0].url}")
                    response = requests.get(edit_response.data[0].url)
                    response.raise_for_status()
                    generated_image_data = response.content
                else:
                    logger.error("No image data or URL found in response")
                    raise ValueError("Invalid response from GPT-image-1: no image data")
                
                logger.info(f"Successfully generated image, size: {len(generated_image_data)} bytes")
                
                # Save generated image for debugging
                debug_path = os.path.join(os.getcwd(), "temp", f"generated_{uuid.uuid4()}.png")
                with open(debug_path, "wb") as f:
                    f.write(generated_image_data)
                logger.info(f"Saved generated image for debugging at: {debug_path}")
                
                return generated_image_data
                
            except Exception as e:
                logger.error(f"Error using GPT-image-1 for generation: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in generate_image_from_references: {e}", exc_info=True)
            raise
            
    def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Generates a new image based on a text prompt using DALL-E 3.
        
        Args:
            prompt: The generation prompt
            
        Returns:
            The generated image data as bytes
        """
        try:
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            
            # Log the prompt
            prompt_log_path = os.path.join(os.getcwd(), "temp", f"prompt_log_{uuid.uuid4()}.txt")
            os.makedirs(os.path.dirname(prompt_log_path), exist_ok=True)
            with open(prompt_log_path, "w") as f:
                f.write(f"IMAGE GENERATION PROMPT:\n{prompt}")
            
            logger.info(f"Saved generation prompt to: {prompt_log_path}")
            
            # Call the OpenAI API with DALL-E 3
            try:
                logger.info("Calling DALL-E 3 to generate image")
                
                # Generate the image
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                
                # Get the image URL or base64 data
                if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
                    logger.info("Received base64-encoded image from DALL-E 3")
                    image_base64 = response.data[0].b64_json
                    generated_image_data = base64.b64decode(image_base64)
                elif hasattr(response.data[0], 'url') and response.data[0].url:
                    # Download the image from the URL
                    logger.info(f"Downloading image from URL: {response.data[0].url}")
                    image_response = requests.get(response.data[0].url)
                    image_response.raise_for_status()
                    generated_image_data = image_response.content
                else:
                    logger.error("No image data or URL found in response")
                    raise ValueError("Invalid response from DALL-E 3: no image data")
                
                logger.info(f"Successfully generated image, size: {len(generated_image_data)} bytes")
                
                # Save generated image for debugging
                debug_path = os.path.join(os.getcwd(), "temp", f"generated_{uuid.uuid4()}.png")
                with open(debug_path, "wb") as f:
                    f.write(generated_image_data)
                logger.info(f"Saved generated image for debugging at: {debug_path}")
                
                return generated_image_data
                
            except Exception as e:
                logger.error(f"Error using DALL-E 3 for generation: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error in generate_image: {e}", exc_info=True)
            raise