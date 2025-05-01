from PIL import Image
import io
import os
import uuid
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles image processing operations for the Ghibli Stylizer app."""
    
    @staticmethod
    def validate_image_format(file_extension: str) -> bool:
        """Validates if the image format is acceptable."""
        valid_extensions = [".jpg", ".jpeg", ".png"]
        return file_extension.lower() in valid_extensions
    
    @staticmethod
    def process_input_image(image_data: bytes, filename: str) -> tuple[bytes, str]:
        """Processes the input image: converts to PNG if needed and resizes."""
        try:
            # Open the image from bytes
            img = Image.open(io.BytesIO(image_data))
            logger.info(f"Original image: Format={img.format}, Size={img.size}, Mode={img.mode}")
            
            # Convert to RGB mode (DALL-E prefers RGB)
            if img.mode != "RGB":
                img = img.convert("RGB")
                logger.info(f"Converted image to RGB mode")
            
            # Resize image to 1024x1024 maintaining aspect ratio
            img = ImageProcessor._resize_image(img, 1024, 1024)
            logger.info(f"Resized image: Size={img.size}")
            
            # Check if the image dimensions are correct - DALL-E requires square images
            width, height = img.size
            if width != 1024 or height != 1024:
                logger.warning(f"Image dimensions {width}x{height} need adjustment to 1024x1024")
                # Create a new white background
                new_img = Image.new("RGB", (1024, 1024), (255, 255, 255))
                # Calculate position to paste (center)
                x = (1024 - width) // 2
                y = (1024 - height) // 2
                # Paste the resized image
                new_img.paste(img, (x, y))
                img = new_img
                logger.info("Image adjusted to 1024x1024 with white background")
            
            # Convert to PNG
            output = io.BytesIO()
            img.save(output, format="PNG")
            output.seek(0)
            
            # Log the size of the processed image data
            processed_data = output.getvalue()
            logger.info(f"Processed image data size: {len(processed_data)} bytes")
            
            # Generate a new filename with PNG extension
            new_filename = f"{os.path.splitext(filename)[0]}.png"
            
            return processed_data, new_filename
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            raise
    
    @staticmethod
    def save_temp_image(image_data: bytes) -> str:
        """Saves an image to a temporary file and returns the path."""
        temp_filename = f"{uuid.uuid4()}.png"
        temp_path = os.path.join(os.getcwd(), "temp", temp_filename)
        
        # Create temp directory if it doesn't exist
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        # Write image to file
        with open(temp_path, "wb") as f:
            f.write(image_data)
        
        return temp_path
    
    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        """Deletes a temporary file after use."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {file_path}: {e}")
    
    @staticmethod
    def _resize_image(img: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """Resizes an image to maintain aspect ratio within target dimensions."""
        width, height = img.size
        
        # Calculate aspect ratios
        aspect = width / height
        target_aspect = target_width / target_height
        
        # Resize based on aspect ratio comparison
        if aspect > target_aspect:
            # Width is the limiting factor
            new_width = target_width
            new_height = int(new_width / aspect)
        else:
            # Height is the limiting factor
            new_height = target_height
            new_width = int(new_height * aspect)
        
        # Resize the image with high quality
        logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img
