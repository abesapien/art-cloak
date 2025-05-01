#!/usr/bin/env python3
"""
Integration tests for ArtCloak application.
Tests the API endpoints and their interactions with dependent services.
"""

import unittest
import requests
import os
import sys
import time
import io
import logging
import subprocess
import atexit
import signal
from PIL import Image
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArtCloakIntegrationTests(unittest.TestCase):
    """Integration tests for ArtCloak API endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Start the application server for testing."""
        cls.port = 8080  # Hard-coded port for testing
        logger.info(f"Starting test server on port {cls.port}")
        
        # Start the server in a separate process
        cmd = f"python3 -c \"import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port={cls.port})\""
        cls.server_process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
        
        # Register cleanup function to ensure server is terminated
        atexit.register(cls._stop_server)
        
        # Wait for server to start
        logger.info("Waiting for server to start...")
        time.sleep(3)
        
        # Set base URL for API calls
        cls.base_url = f"http://localhost:{cls.port}"
        
        # Check if server is running
        try:
            response = requests.get(f"{cls.base_url}/health")
            response.raise_for_status()
            logger.info("Server is running and responding to health checks")
        except Exception as e:
            logger.error(f"Server failed to start: {e}")
            cls._stop_server()
            raise
    
    @classmethod
    def tearDownClass(cls):
        """Stop the application server after tests complete."""
        cls._stop_server()
    
    @classmethod
    def _stop_server(cls):
        """Stop the server process."""
        if hasattr(cls, 'server_process') and cls.server_process:
            logger.info("Stopping server...")
            try:
                os.killpg(os.getpgid(cls.server_process.pid), signal.SIGTERM)
                cls.server_process.wait(timeout=5)
                logger.info("Server stopped")
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
                # Force kill if needed
                try:
                    os.killpg(os.getpgid(cls.server_process.pid), signal.SIGKILL)
                except:
                    pass
    
    def _create_test_image(self, width=800, height=600, color='white') -> Tuple[bytes, str]:
        """Create a test image for upload testing."""
        img = Image.new('RGB', (width, height), color=color)
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        return img_io.getvalue(), "test_image.png"
    
    def _check_openai_api_key(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(os.getenv("OPENAI_API_KEY"))

    def test_health_endpoint(self):
        """Test the health endpoint."""
        response = requests.get(f"{self.base_url}/health")
        
        # Check response status code
        self.assertEqual(response.status_code, 200, "Health endpoint should return 200 OK")
        
        # Check response content
        data = response.json()
        self.assertIn("status", data, "Response should contain status field")
        self.assertEqual(data["status"], "ok", "Status should be 'ok'")
        self.assertIn("message", data, "Response should contain message field")
    
    def test_generate_endpoint(self):
        """Test the generate endpoint."""
        # Skip test if OpenAI API key not available
        if not self._check_openai_api_key():
            self.skipTest("OpenAI API key not available - skipping test_generate_endpoint")
        
        # Create test image
        image_data, image_name = self._create_test_image()
        
        # Prepare request data
        files = {
            'file': (image_name, image_data, 'image/png')
        }
        data = {
            'prompt': 'studio ghibli style test image'
        }
        
        # Send request to generate endpoint
        response = requests.post(f"{self.base_url}/generate/", files=files, data=data)
        
        # Check response status code
        self.assertEqual(response.status_code, 200, "Generate endpoint should return 200 OK")
        
        # Check response content type
        self.assertEqual(response.headers['Content-Type'], 'image/png', 
                         "Response content type should be image/png")
        
        # Check that response contains image data
        image_response = response.content
        self.assertGreater(len(image_response), 1000, 
                         "Response should contain image data (expected > 1KB)")
        
        # Verify the response is a valid image
        try:
            with io.BytesIO(image_response) as img_io:
                img = Image.open(img_io)
                self.assertEqual(img.format, 'PNG', "Image format should be PNG")
                # Generated images from GPT-image-1 are typically 1024x1024
                self.assertEqual(img.size, (1024, 1024), "Image size should be 1024x1024")
        except Exception as e:
            self.fail(f"Response is not a valid image: {str(e)}")
            
        # Save the response to a temporary file for inspection if needed
        output_path = "generated_test_image.png"
        with open(output_path, 'wb') as f:
            f.write(image_response)
        logger.info(f"Generated image saved to: {output_path}")
    
    def test_create_endpoint(self):
        """Test the create endpoint."""
        # Skip test if OpenAI API key not available
        if not self._check_openai_api_key():
            self.skipTest("OpenAI API key not available - skipping test_create_endpoint")
        
        # Prepare request data with a descriptive prompt
        data = {
            'prompt': 'A serene lake surrounded by mountains at sunset in Studio Ghibli style'
        }
        
        # Send request to create endpoint
        response = requests.post(f"{self.base_url}/create/", data=data)
        
        # Check response status code
        self.assertEqual(response.status_code, 200, "Create endpoint should return 200 OK")
        
        # Check response content type
        self.assertEqual(response.headers['Content-Type'], 'image/png', 
                         "Response content type should be image/png")
        
        # Check that response contains image data
        image_response = response.content
        self.assertGreater(len(image_response), 1000, 
                         "Response should contain image data (expected > 1KB)")
        
        # Verify the response is a valid image
        try:
            with io.BytesIO(image_response) as img_io:
                img = Image.open(img_io)
                self.assertEqual(img.format, 'PNG', "Image format should be PNG")
                # DALL-E 3 images are typically 1024x1024
                self.assertEqual(img.size, (1024, 1024), "Image size should be 1024x1024")
        except Exception as e:
            self.fail(f"Response is not a valid image: {str(e)}")
            
        # Save the response to a temporary file for inspection if needed
        output_path = "created_test_image.png"
        with open(output_path, 'wb') as f:
            f.write(image_response)
        logger.info(f"Created image saved to: {output_path}")
    
    def test_error_handling(self):
        """Test error handling for invalid requests."""
        # Test 1: Generate endpoint with missing image
        response = requests.post(f"{self.base_url}/generate/", data={'prompt': 'test'})
        self.assertEqual(response.status_code, 422, "Should return 422 when file is missing")
        
        # Test 2: Generate endpoint with missing prompt
        image_data, image_name = self._create_test_image()
        files = {'file': (image_name, image_data, 'image/png')}
        response = requests.post(f"{self.base_url}/generate/", files=files)
        self.assertEqual(response.status_code, 422, "Should return 422 when prompt is missing")
        
        # Test 3: Generate endpoint with invalid file format
        # Create a text file instead of an image
        text_data = b"This is not an image file"
        files = {'file': ('test.txt', text_data, 'text/plain')}
        response = requests.post(
            f"{self.base_url}/generate/", 
            files=files, 
            data={'prompt': 'test'}
        )
        self.assertEqual(response.status_code, 400, "Should return 400 for invalid file format")
        
        # Test 4: Create endpoint with missing prompt
        response = requests.post(f"{self.base_url}/create/")
        self.assertEqual(response.status_code, 422, "Should return 422 when prompt is missing")
        
        # Test 5: Non-existent endpoint
        response = requests.get(f"{self.base_url}/nonexistent")
        self.assertEqual(response.status_code, 404, "Should return 404 for non-existent endpoint")

if __name__ == '__main__':
    unittest.main()