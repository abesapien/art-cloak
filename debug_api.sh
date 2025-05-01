#!/bin/bash

# Script to debug API connectivity issues

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}     ArtCloak API Debugger            ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed.${NC}"
    echo -e "${YELLOW}Please install curl to run this script.${NC}"
    exit 1
fi

# Check if the API server is running
echo -e "${BLUE}Checking if API server is running...${NC}"
if curl -s "http://localhost:8080/health" > /dev/null; then
    echo -e "${GREEN}✓ API server is running${NC}"
else
    echo -e "${RED}✗ API server is not running${NC}"
    echo -e "${YELLOW}Please start the API server at http://localhost:8080${NC}"
    
    # Try to find the actual port
    echo -e "${BLUE}Checking common alternative ports...${NC}"
    for port in 8000 8080 5000 8888 3000; do
        if curl -s "http://localhost:$port/health" > /dev/null; then
            echo -e "${GREEN}Found API running at http://localhost:$port${NC}"
            echo -e "${YELLOW}You need to either:${NC}"
            echo -e "  1. Update the frontend to use http://localhost:$port instead of port 8080"
            echo -e "  2. Restart the backend on port 8080"
            exit 1
        fi
    done
    
    echo -e "${RED}Could not find an API server running on any common port${NC}"
    echo -e "${YELLOW}Start the backend using the command:${NC}"
    echo -e "  python3 -c \"import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8080)\""
    exit 1
fi

# Test the API with a curl request
echo -e "\n${BLUE}Testing API with a simple request...${NC}"
echo -e "${YELLOW}Finding a sample image to test with...${NC}"

# Find a sample image to test with
SAMPLE_IMG=""
for dir in "./temp" "."; do
    if [ -d "$dir" ]; then
        SAMPLE_IMG=$(find "$dir" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) | head -n 1)
        if [ -n "$SAMPLE_IMG" ]; then
            break
        fi
    fi
done

if [ -z "$SAMPLE_IMG" ]; then
    echo -e "${RED}Could not find a sample image to test with${NC}"
    echo -e "${YELLOW}Please provide a path to a sample image:${NC}"
    read -p "Image path: " SAMPLE_IMG
    
    if [ ! -f "$SAMPLE_IMG" ]; then
        echo -e "${RED}Invalid file path${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Using sample image: $SAMPLE_IMG${NC}"

# Test the API with curl
echo -e "${BLUE}Sending test request to API...${NC}"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -F "file=@$SAMPLE_IMG" -F "prompt=test prompt" http://localhost:8080/generate/)

if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ API responded with success (200 OK)${NC}"
else
    echo -e "${RED}✗ API responded with error code: $RESPONSE${NC}"
    echo -e "${YELLOW}Trying with more detailed output:${NC}"
    
    # Try again with more detailed output
    curl -v -F "file=@$SAMPLE_IMG" -F "prompt=test prompt" http://localhost:8080/generate/ > /dev/null
fi

echo -e "\n${BLUE}Testing API access from browser...${NC}"
echo -e "${YELLOW}Please try these test pages in your browser:${NC}"
echo -e "  1. ${GREEN}http://localhost:3000/test-api.html${NC} - JavaScript API test"
echo -e "  2. ${GREEN}http://localhost:3000/direct-test.html${NC} - Direct form submission test"

echo -e "\n${BLUE}Debug information:${NC}"
echo -e "${YELLOW}Current directory:${NC} $(pwd)"
echo -e "${YELLOW}Sample image:${NC} $SAMPLE_IMG"
echo -e "${YELLOW}API URL:${NC} http://localhost:8080/generate/"

echo -e "\n${GREEN}Debug complete. If issues persist, try:${NC}"
echo -e "1. Check backend logs for errors"
echo -e "2. Verify that the frontend is set to use http://localhost:8080"
echo -e "3. Check browser console for CORS or JavaScript errors"
echo -e "4. Try the Python test script: ./test_api.py --image=$SAMPLE_IMG"