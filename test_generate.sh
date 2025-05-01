#!/bin/bash

# Ensure the API server is running

# Set API endpoint
API_URL="http://localhost:8000/generate/"

# Define prompt
PROMPT="Generate a photorealistic image of a gift basket on a white background labeled 'Relax & Unwind' with a ribbon and handwriting-like font, based on this reference image."

# Get a single PNG file from the temp directory for testing
IMAGE_FILE=$(find ./temp -name "*.png" | head -1)

# Check if we found any images
if [ -z "$IMAGE_FILE" ]; then
  echo "Error: No PNG images found in the temp directory. Please ensure there is an image to use as reference."
  exit 1
fi

# Build the curl command with a single file
CURL_CMD="curl -X POST ${API_URL} -F \"prompt=${PROMPT}\" -F \"file=@${IMAGE_FILE}\""

# Add output redirection
CURL_CMD="${CURL_CMD} --output generated_output.png"

# Print the command
echo "Executing: ${CURL_CMD}"

# Execute the command
eval ${CURL_CMD}

# Check if the request was successful
if [ -f "generated_output.png" ]; then
  echo "Image successfully generated and saved to generated_output.png"
else
  echo "Failed to generate image"
fi