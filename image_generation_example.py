"""
Standalone example of using OpenAI's GPT-image-1 for image generation.
This script demonstrates how to generate an image from a reference image.
"""

import os
import base64
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Generation prompt
prompt = """
Generate a photorealistic image of a gift basket on a white background 
labeled 'Relax & Unwind' with a ribbon and handwriting-like font,
using this reference image.
"""

# Find a reference image from the temp directory
ref_image_path = None
for file in os.listdir("temp"):
    if file.endswith(".png"):
        ref_image_path = os.path.join("temp", file)
        break

if not ref_image_path:
    raise ValueError("No PNG images found in the temp directory")

print(f"Using reference image: {ref_image_path}")

try:
    # Open the image with PIL to verify it's valid
    img = Image.open(ref_image_path)
    print(f"Image format: {img.format}, Size: {img.size}, Mode: {img.mode}")
    
    # Call the OpenAI API with the file directly
    print("Calling GPT-image-1 to generate image...")
    with open(ref_image_path, "rb") as img_file:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_file,  # Direct file handle
            prompt=prompt
        )
    
    # Get the image data
    if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
        print("Received base64-encoded image from GPT-image-1")
        image_base64 = response.data[0].b64_json
        generated_image_data = base64.b64decode(image_base64)
    else:
        print(f"Received image URL: {response.data[0].url}")
        # Download the image from the URL
        import requests
        url_response = requests.get(response.data[0].url)
        url_response.raise_for_status()
        generated_image_data = url_response.content
    
    # Save the generated image
    output_path = "example_generated.png"
    with open(output_path, "wb") as output_file:
        output_file.write(generated_image_data)
    
    print(f"Generated image saved to: {output_path}")
    
except Exception as e:
    print(f"Error generating image: {e}")
    raise