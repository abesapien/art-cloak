#!/bin/bash

# Ensure the API server is running

# Set API endpoint
API_URL="http://localhost:8000/create/"

# Define prompt
PROMPT="Generate a photorealistic image of a gift basket on a white background labeled 'Relax & Unwind' with a ribbon and handwriting-like font, containing bath bombs, soaps, and incense sticks."

# Build the curl command for direct image generation
CURL_CMD="curl -X POST ${API_URL} -F \"prompt=${PROMPT}\" --output created_image.png"

# Print the command
echo "Executing: ${CURL_CMD}"

# Execute the command
eval ${CURL_CMD}

# Check if the request was successful
if [ -f "created_image.png" ]; then
  echo "Image successfully created and saved to created_image.png"
else
  echo "Failed to create image"
fi