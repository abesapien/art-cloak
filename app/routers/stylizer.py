from fastapi import APIRouter, UploadFile, HTTPException, File, BackgroundTasks, Form
from fastapi.responses import Response, JSONResponse, PlainTextResponse
import os
import io
import logging
import uuid
from typing import Optional, List

from app.utils.image_processor import ImageProcessor
from app.utils.openai_client import OpenAIClient
from PIL import Image

router = APIRouter(tags=["Image Stylization"])
logger = logging.getLogger(__name__)
openai_client = None

# Initialize OpenAI client lazily to avoid startup errors if API key is not set
def get_openai_client():
    global openai_client
    if openai_client is None:
        try:
            openai_client = OpenAIClient()
        except ValueError as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise HTTPException(status_code=500, detail="OpenAI API key not configured properly")
    return openai_client

# Background task to clean up temporary files
def cleanup_temp_files(file_path: Optional[str] = None):
    if file_path and os.path.exists(file_path):
        ImageProcessor.cleanup_temp_file(file_path)

@router.post("/analyze/", response_class=JSONResponse, summary="Analyze an image and return description as JSON", include_in_schema=False)
async def analyze_image_json(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    return await _analyze_image(background_tasks, file, "json")

@router.post("/analyze/text/", response_class=PlainTextResponse, summary="Analyze an image and return plain text description", include_in_schema=False)
async def analyze_image_text(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    return await _analyze_image(background_tasks, file, "text")

async def _analyze_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    response_type: str = "json",
):
    """
    Upload an image to be analyzed with GPT-4 Vision.
    
    - **file**: JPG or PNG image file
    
    Returns a JSON object containing the detailed description of the image.
    """
    temp_path = None
    
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1]
        if not file_ext or not ImageProcessor.validate_image_format(file_ext):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Only JPG and PNG are accepted."
            )
        
        # Read the file
        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Process the image (resize and convert to PNG if needed)
        logger.info(f"Processing image: {file.filename}, size: {len(image_data)} bytes")
        processed_image, new_filename = ImageProcessor.process_input_image(image_data, file.filename)
        logger.info(f"Image processed successfully as {new_filename}, size: {len(processed_image)} bytes")
        
        # Save the processed image for debugging
        debug_path = ImageProcessor.save_temp_image(processed_image)
        logger.info(f"Saved processed image for debugging at: {debug_path}")
        background_tasks.add_task(cleanup_temp_files, debug_path)
        
        # Get OpenAI client
        client = get_openai_client()
        logger.info("Sending image to OpenAI for analysis")
        
        # Call OpenAI API to analyze the image
        try:
            logger.info("Calling OpenAI API to analyze image")
            analysis_result = client.stylize_image(processed_image)
            
            # Get the description from the analysis
            if not analysis_result:
                logger.error("Failed to get analysis from OpenAI (empty response)")
                raise HTTPException(status_code=500, detail="Failed to get analysis from API")
            
            # Determine response type based on parameter
            if response_type == "text":
                # Return as plain text
                return PlainTextResponse(
                    content=f"ANALYSIS OF IMAGE: {file.filename}\n\n{client.last_analysis}",
                    status_code=200
                )
            else:
                # Return as JSON
                return JSONResponse(
                    content={
                        "filename": file.filename,
                        "analysis": client.last_analysis,
                        "analysis_file": client.last_analysis_file
                    },
                    status_code=200
                )
                
        except Exception as api_err:
            logger.error(f"Error calling OpenAI API: {api_err}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"API error: {str(api_err)}")
    
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
        
    except Exception as e:
        logger.exception(f"Error in analyze_image: {e}")
        # Clean up any temporary files if an exception occurs
        if temp_path:
            background_tasks.add_task(cleanup_temp_files, temp_path)
        raise HTTPException(status_code=500, detail="Failed to analyze image")

@router.post("/stylize/", response_class=Response, summary="Process an image with GPT-4 Vision", include_in_schema=False)
async def stylize_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload an image to be analyzed with GPT-4 Vision.
    
    - **file**: JPG or PNG image file
    
    Returns the original image and saves a detailed description to a text file.
    """
    temp_path = None
    
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1]
        if not file_ext or not ImageProcessor.validate_image_format(file_ext):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Only JPG and PNG are accepted."
            )
        
        # Read the file
        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Process the image (resize and convert to PNG if needed)
        logger.info(f"Processing image: {file.filename}, size: {len(image_data)} bytes")
        processed_image, new_filename = ImageProcessor.process_input_image(image_data, file.filename)
        logger.info(f"Image processed successfully as {new_filename}, size: {len(processed_image)} bytes")
        
        # Save the processed image for debugging
        debug_path = ImageProcessor.save_temp_image(processed_image)
        logger.info(f"Saved processed image for debugging at: {debug_path}")
        
        # Get OpenAI client
        client = get_openai_client()
        logger.info("Sending image to OpenAI for stylization")
        
        # Call OpenAI API to stylize the image
        try:
            logger.info("Calling OpenAI API to stylize image")
            stylized_image = client.stylize_image(processed_image)
            
            # Verify we got a valid response from OpenAI
            if not stylized_image:
                logger.error("Failed to get stylized image back from OpenAI (empty response)")
                raise HTTPException(status_code=500, detail="Failed to get stylized image from API")
                
            # Check if the response is a valid image
            try:
                with io.BytesIO(stylized_image) as check_stream:
                    check_img = Image.open(check_stream)
                    logger.info(f"Verified stylized image is valid: {check_img.format}, Size: {check_img.size}")
            except Exception as img_err:
                logger.error(f"Received invalid image data from API: {img_err}")
                raise HTTPException(status_code=500, detail="Invalid image data received from API")
                
        except Exception as api_err:
            logger.error(f"Error calling OpenAI API: {api_err}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"API error: {str(api_err)}")
        
        logger.info(f"Successfully received stylized image, size: {len(stylized_image)} bytes")
        
        # Return the stylized image from DALL-E
        # The analysis is also stored separately in text files
        
        # Print success message with information
        print("\n=== IMAGE STYLIZATION SUCCESSFUL ===")
        print(f"Stylized image size: {len(stylized_image)} bytes")
        print(f"Description saved to file")
        print("===================================\n")
        
        # Save both images for comparison
        orig_debug_path = os.path.join(os.getcwd(), "temp", f"original_{uuid.uuid4()}.png")
        style_debug_path = os.path.join(os.getcwd(), "temp", f"styled_{uuid.uuid4()}.png")
        
        # Create temp directory if it doesn't exist
        os.makedirs(os.path.dirname(orig_debug_path), exist_ok=True)
        
        # Save both images for comparison
        with open(orig_debug_path, "wb") as f:
            f.write(processed_image)
        with open(style_debug_path, "wb") as f:
            f.write(stylized_image)
            
        logger.info(f"Saved original image at: {orig_debug_path}")
        logger.info(f"Saved stylized image at: {style_debug_path}")
        
        # Add cleanup task
        background_tasks.add_task(cleanup_temp_files, orig_debug_path)
        background_tasks.add_task(cleanup_temp_files, style_debug_path)
        
        # Return the original image as response with analysis info in header
        response = Response(
            content=stylized_image,
            media_type="image/png"
        )
        
        # Add headers with analysis information
        response.headers["X-Image-Analysis"] = "Image was analyzed successfully"
        response.headers["X-Analysis-File"] = os.path.basename(client.last_analysis_file) if client.last_analysis_file else "unknown"
        
        # Add a sanitized truncated version of the analysis
        if client.last_analysis:
            # Remove newlines, asterisks, and other problematic characters, then truncate
            sanitized_analysis = client.last_analysis.replace("\n", " ").replace("*", "")
            # Replace any other problematic characters
            import re
            sanitized_analysis = re.sub(r'[^\w\s\-\.,;:]', '', sanitized_analysis)
            analysis_summary = sanitized_analysis[:200] + "..." if len(sanitized_analysis) > 200 else sanitized_analysis
        else:
            analysis_summary = "No analysis"
        
        response.headers["X-Analysis-Summary"] = analysis_summary
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
        
    except Exception as e:
        logger.exception(f"Error in stylize_image: {e}")
        # Clean up any temporary files if an exception occurs
        if temp_path:
            background_tasks.add_task(cleanup_temp_files, temp_path)
        raise HTTPException(status_code=500, detail="Failed to process image")

@router.get("/health", summary="Check if the API is healthy")
async def health_check():
    """
    Simple health check endpoint to verify the API is running correctly.
    """
    return {"status": "healthy"}

@router.post("/generate/", response_class=Response, summary="Generate an image by editing a reference image")
async def generate_image(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
    """
    Generate a new image by editing a reference image using GPT-image-1.
    
    - **file**: JPG or PNG image file to use as reference
    - **prompt**: The generation prompt describing what to create
    
    Returns the generated image based on edits to the reference image.
    """
    temp_path = None
    
    # Enhanced debug logging
    logger.info(f"Request received to /generate/ endpoint")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"File info: name={file.filename}, content_type={file.content_type}")
    
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1]
        logger.info(f"Detected file extension: {file_ext}")
        
        if not file_ext or not ImageProcessor.validate_image_format(file_ext):
            logger.error(f"Unsupported file format: {file_ext}")
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format for {file.filename}. Only JPG and PNG are accepted."
            )
        
        # Read the file
        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail=f"Empty file uploaded: {file.filename}")
        
        # Process the image (resize and convert to PNG if needed)
        logger.info(f"Processing image: {file.filename}, size: {len(image_data)} bytes")
        processed_image, new_filename = ImageProcessor.process_input_image(image_data, file.filename)
        logger.info(f"Image processed successfully as {new_filename}, size: {len(processed_image)} bytes")
        
        # Save the processed image for debugging
        debug_path = ImageProcessor.save_temp_image(processed_image)
        logger.info(f"Saved processed image for debugging at: {debug_path}")
        temp_path = debug_path
        background_tasks.add_task(cleanup_temp_files, debug_path)
        
        # Get OpenAI client
        client = get_openai_client()
        
        # Generate image from reference
        try:
            logger.info(f"Calling OpenAI to generate image with prompt: {prompt[:100]}...")
            processed_images = [processed_image]  # For compatibility with existing method
            generated_image = client.generate_image_from_references(processed_images, prompt)
            
            # Verify we got a valid response
            if not generated_image:
                logger.error("Failed to generate image (empty response)")
                raise HTTPException(status_code=500, detail="Failed to generate image from API")
            
            # Check if the response is a valid image
            try:
                with io.BytesIO(generated_image) as check_stream:
                    check_img = Image.open(check_stream)
                    logger.info(f"Verified generated image is valid: {check_img.format}, Size: {check_img.size}")
            except Exception as img_err:
                logger.error(f"Received invalid image data from API: {img_err}")
                raise HTTPException(status_code=500, detail="Invalid image data received from API")
                
        except Exception as api_err:
            logger.error(f"Error calling OpenAI API: {api_err}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"API error: {str(api_err)}")
        
        logger.info(f"Successfully received generated image, size: {len(generated_image)} bytes")
        
        # Save generated image for reference
        gen_debug_path = os.path.join(os.getcwd(), "temp", f"generated_{uuid.uuid4()}.png")
        
        # Create temp directory if it doesn't exist
        os.makedirs(os.path.dirname(gen_debug_path), exist_ok=True)
        
        # Save generated image
        with open(gen_debug_path, "wb") as f:
            f.write(generated_image)
        logger.info(f"Saved generated image at: {gen_debug_path}")
        
        # Add cleanup task
        background_tasks.add_task(cleanup_temp_files, gen_debug_path)
        
        # Return the generated image as response
        response = Response(
            content=generated_image,
            media_type="image/png"
        )
        
        print("\n=== IMAGE GENERATION SUCCESSFUL ===")
        print(f"Generated image size: {len(generated_image)} bytes")
        print(f"Used {len(processed_images)} reference images")
        print("===================================\n")
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
        
    except Exception as e:
        logger.exception(f"Error in generate_image: {e}")
        # Clean up any temporary files if an exception occurs
        if temp_path:
            background_tasks.add_task(cleanup_temp_files, temp_path)
        raise HTTPException(status_code=500, detail="Failed to generate image")

@router.post("/create/", response_class=Response, summary="Create a new image from a text description")
async def create_image(
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
):
    """
    Generate a completely new image from a text prompt using DALL-E 3.
    
    - **prompt**: A detailed text description of the image you want to create
    
    Returns a high-quality image generated based on your text description.
    """
    try:
        # Get OpenAI client
        client = get_openai_client()
        
        # Generate the image from the prompt
        try:
            logger.info(f"Calling OpenAI to generate image with prompt: {prompt[:100]}...")
            generated_image = client.generate_image(prompt)
            
            # Verify we got a valid response
            if not generated_image:
                logger.error("Failed to generate image (empty response)")
                raise HTTPException(status_code=500, detail="Failed to generate image from API")
            
            # Check if the response is a valid image
            try:
                with io.BytesIO(generated_image) as check_stream:
                    check_img = Image.open(check_stream)
                    logger.info(f"Verified generated image is valid: {check_img.format}, Size: {check_img.size}")
            except Exception as img_err:
                logger.error(f"Received invalid image data from API: {img_err}")
                raise HTTPException(status_code=500, detail="Invalid image data received from API")
                
        except Exception as api_err:
            logger.error(f"Error calling OpenAI API: {api_err}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"API error: {str(api_err)}")
        
        logger.info(f"Successfully received generated image, size: {len(generated_image)} bytes")
        
        # Save generated image for reference
        gen_debug_path = os.path.join(os.getcwd(), "temp", f"generated_{uuid.uuid4()}.png")
        
        # Create temp directory if it doesn't exist
        os.makedirs(os.path.dirname(gen_debug_path), exist_ok=True)
        
        # Save generated image
        with open(gen_debug_path, "wb") as f:
            f.write(generated_image)
        logger.info(f"Saved generated image at: {gen_debug_path}")
        
        # Add cleanup task
        background_tasks.add_task(cleanup_temp_files, gen_debug_path)
        
        # Return the generated image as response
        response = Response(
            content=generated_image,
            media_type="image/png"
        )
        
        print("\n=== IMAGE GENERATION SUCCESSFUL ===")
        print(f"Generated image size: {len(generated_image)} bytes")
        print(f"Used prompt: {prompt[:50]}...")
        print("===================================\n")
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
        
    except Exception as e:
        logger.exception(f"Error in create_image: {e}")
        raise HTTPException(status_code=500, detail="Failed to create image")