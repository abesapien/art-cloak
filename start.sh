#!/bin/bash

# ArtCloak Launcher with fixed ports
# Script that uses the precise ports needed

# Make sure the script exits on any error
set -e

# Set up colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}     ArtCloak Application Launcher     ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if the Python virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
  echo -e "${YELLOW}Python virtual environment is not activated.${NC}"
  echo -e "${YELLOW}Please activate a virtual environment with the required dependencies.${NC}"
  exit 1
fi

# Check if ports 8080 and 3080 are available
python3 -c "import socket; s = socket.socket(); s.bind(('', 8080)) and s.close()" &>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Port 8080 is already in use.${NC}"
    echo -e "${YELLOW}Please close the application using this port and try again.${NC}"
    exit 1
fi

python3 -c "import socket; s = socket.socket(); s.bind(('', 3080)) and s.close()" &>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Port 3080 is already in use.${NC}"
    echo -e "${YELLOW}Please close the application using this port and try again.${NC}"
    exit 1
fi

# Create temp directory if it doesn't exist
mkdir -p ./temp

# Build the frontend
echo -e "${BLUE}Building frontend...${NC}"
cd ./frontend
npm install --silent
npm run build
cd ..
echo -e "${GREEN}✓ Frontend built successfully${NC}"

# Start the backend server on port 8080
echo -e "${BLUE}Starting backend server on port 8080...${NC}"
python3 -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8080, reload=True)" &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started with PID: $BACKEND_PID${NC}"

# Wait a moment for the backend to start
sleep 2

# Test backend health
echo -e "${BLUE}Testing backend health...${NC}"
curl -s "http://localhost:8080/health" > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "${YELLOW}⚠️ Backend health check failed, but continuing...${NC}"
fi

# Start the frontend server on port 3080
echo -e "${BLUE}Starting frontend server on port 3080...${NC}"
cd ./frontend/dist
python3 -m http.server 3080 &
FRONTEND_PID=$!
cd ../..
echo -e "${GREEN}✓ Frontend started with PID: $FRONTEND_PID${NC}"

# Display application URLs
echo -e "\n${GREEN}✨ ArtCloak is now running!${NC}"
echo -e "${BLUE}Backend API:${NC} http://localhost:8080"
echo -e "${BLUE}Frontend:${NC} http://localhost:3080"
echo -e "${BLUE}API Documentation:${NC} http://localhost:8080/docs"
echo -e "\n${YELLOW}IMPORTANT:${NC} The backend is running on port 8080 as specified."
echo -e "${YELLOW}IMPORTANT:${NC} The frontend is hardcoded to use http://localhost:8080 for API access."
echo -e "\n${YELLOW}Press Ctrl+C to stop the application${NC}\n"

# Trap Ctrl+C to kill both servers
trap "kill $BACKEND_PID 2>/dev/null; kill $FRONTEND_PID 2>/dev/null; echo -e '\n${GREEN}Stopped ArtCloak servers${NC}'; exit" INT TERM

# Keep the script running
wait