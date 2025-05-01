#!/bin/bash

# Make sure the script exits on any error
set -e

# Check if the Python virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
  echo "Python virtual environment is not activated."
  echo "Please activate a virtual environment with the required dependencies."
  exit 1
fi

# Check for required dependencies
which uvicorn > /dev/null || (echo "uvicorn is not installed. Please install required dependencies." && exit 1)
which npm > /dev/null || (echo "npm is not installed. Please install npm." && exit 1)

# Create a dist directory for the frontend if it doesn't exist
mkdir -p ./frontend/dist

# Build the frontend
echo "Building the frontend..."
cd ./frontend
npm install
npm run build
cd ..

# Start the backend and frontend concurrently
echo "Starting the application..."

# Find an available port for the backend
find_available_port() {
    local start_port=$1
    local max_port=$2
    
    # First try some well-known ports
    for port in 8000 8080 3000 5000 8888 9000; do
        $PYTHON -c "import socket; s = socket.socket(); s.bind(('', $port)) and s.close()" &>/dev/null
        if [ $? -eq 0 ]; then
            echo $port
            return
        fi
    done
    
    # Try a much wider range of ports 
    local range_start=8000
    local range_end=9999
    
    # Try random ports first to reduce conflicts
    for i in {1..20}; do
        local random_port=$((range_start + RANDOM % (range_end - range_start + 1)))
        $PYTHON -c "import socket; s = socket.socket(); s.bind(('', $random_port)) and s.close()" &>/dev/null
        if [ $? -eq 0 ]; then
            echo $random_port
            return
        fi
    done
    
    # Methodically try ports in sequence as a fallback
    local port=$range_start
    while [ $port -le $range_end ]; do
        $PYTHON -c "import socket; s = socket.socket(); s.bind(('', $port)) and s.close()" &>/dev/null
        if [ $? -eq 0 ]; then
            echo $port
            return
        fi
        port=$((port + 1))
        
        # Only try every 10th port to speed up scan
        if [ $port -gt $((range_start + 100)) ]; then
            port=$((port + 9))
        fi
    done
    
    echo "Error: Could not find an available port. Please close some applications and try again." >&2
    return 1
}

# Find backend port
BACKEND_PORT=$(find_available_port 8000 8100)
if [ $? -ne 0 ]; then
    echo "Failed to find available port for backend server."
    exit 1
fi

# Try to start the backend in the background
echo "Attempting to start backend server at http://localhost:$BACKEND_PORT"
if uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT & 
then
  BACKEND_PID=$!
  echo "Backend server started with PID: $BACKEND_PID"
  # Wait a moment for the backend to start
  sleep 2
  echo "Backend server should be running at http://localhost:$BACKEND_PORT"
else
  echo "Warning: Failed to start backend server. The frontend will run in demo mode."
  BACKEND_PID=""
fi

# Build the frontend
echo "Building frontend..."
cd ./frontend
./build.sh

# Find an available port for the frontend
FRONTEND_PORT=$(find_available_port 3000 3100)
if [ $? -ne 0 ]; then
    echo "Failed to find available port for frontend server."
    exit 1
fi

# Start a simple HTTP server for the frontend
echo "Starting frontend server at http://localhost:$FRONTEND_PORT..."
cd dist
python -m http.server $FRONTEND_PORT &
FRONTEND_PID=$!

# Display application URLs
echo -e "\n\033[1;32mApplication is running at:\033[0m"
echo -e "  - Backend: \033[1;34mhttp://localhost:$BACKEND_PORT\033[0m"
echo -e "  - Frontend: \033[1;34mhttp://localhost:$FRONTEND_PORT\033[0m"

# Wait for user to press Ctrl+C
echo "Application is running."
echo "Press Ctrl+C to stop both servers."

# Trap Ctrl+C to kill both servers
trap "[ -n \"$BACKEND_PID\" ] && kill $BACKEND_PID 2>/dev/null; kill $FRONTEND_PID 2>/dev/null; echo 'Stopping servers...'; exit" INT

# Keep the script running
wait