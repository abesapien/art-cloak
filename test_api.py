#!/usr/bin/env python3
"""
A simple script to test the API endpoint directly.
This helps identify any issues with the API without using the frontend.
"""

import argparse
import requests
import os
import sys
from pprint import pprint
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_health(base_url):
    """Test the health endpoint"""
    health_url = f"{base_url}/health"
    logger.info(f"Testing health endpoint: {health_url}")
    
    try:
        response = requests.get(health_url)
        response.raise_for_status()
        logger.info(f"Health check response: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

def test_generate(base_url, image_path, prompt="studio ghibli style"):
    """Test the generate endpoint"""
    generate_url = f"{base_url}/generate/"
    logger.info(f"Testing generate endpoint: {generate_url}")
    logger.info(f"Image path: {image_path}")
    logger.info(f"Prompt: {prompt}")
    
    # Ensure the image exists
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return False
    
    # Get the file extension
    _, file_ext = os.path.splitext(image_path)
    
    # Determine content type
    content_type = None
    if file_ext.lower() in ['.jpg', '.jpeg']:
        content_type = 'image/jpeg'
    elif file_ext.lower() == '.png':
        content_type = 'image/png'
    else:
        logger.error(f"Unsupported file format: {file_ext}")
        return False
    
    # Load the image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    logger.info(f"Image loaded: {len(image_data)} bytes, content_type: {content_type}")
    
    # Create the form data
    files = {
        'file': (os.path.basename(image_path), image_data, content_type)
    }
    data = {
        'prompt': prompt
    }
    
    try:
        # Make the request
        logger.info("Sending request to generate endpoint...")
        response = requests.post(generate_url, files=files, data=data)
        
        # Check for errors
        if not response.ok:
            logger.error(f"Request failed with status code {response.status_code}")
            try:
                logger.error(f"Error response: {response.json()}")
            except:
                logger.error(f"Error response text: {response.text}")
            return False
        
        # Get the image response
        image_response = response.content
        logger.info(f"Response received: {len(image_response)} bytes")
        
        # Save the response to a file
        output_path = f"generated_{os.path.basename(image_path)}"
        with open(output_path, 'wb') as f:
            f.write(image_response)
        
        logger.info(f"Generated image saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test the ArtCloak API')
    parser.add_argument('--url', default='http://localhost:8080', help='Base URL of the API')
    parser.add_argument('--image', required=True, help='Path to the image file to upload')
    parser.add_argument('--prompt', default='studio ghibli style', help='Prompt for image generation')
    
    args = parser.parse_args()
    
    # Test the health endpoint
    if not test_health(args.url):
        logger.error("Health check failed. Is the API running?")
        sys.exit(1)
    
    # Test the generate endpoint
    if test_generate(args.url, args.image, args.prompt):
        logger.info("Generate test successful!")
    else:
        logger.error("Generate test failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()