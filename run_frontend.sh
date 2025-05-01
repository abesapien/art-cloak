#!/bin/bash

# Exit script on any error
set -e

echo "Starting ArtCloak Frontend in demo mode..."

# Navigate to the frontend directory
cd ./frontend

# Find a Python version to use for the simple HTTP server
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python is not installed. Please install Python to run the server."
    exit 1
fi

# Function to check if a port is available
is_port_available() {
    # Try to bind to the port directly using Python
    $PYTHON -c "import socket; s = socket.socket(); s.bind(('', $1)) and s.close()" &>/dev/null
    return $?
}

# Find an available port starting from 3000
PORT=3000
MAX_PORT=3100

# Add randomness to starting port to avoid conflicts
PORT=$((PORT + RANDOM % 100))
[ $PORT -ge $MAX_PORT ] && PORT=3000

while [ $PORT -lt $MAX_PORT ]; do
    if is_port_available $PORT; then
        # Found an available port
        break
    else
        echo "Port $PORT is already in use, trying next port..."
        PORT=$((PORT+1))
        # Add a brief pause to allow for any port releases
        sleep 0.1
    fi
done

if [ $PORT -ge $MAX_PORT ]; then
    echo "Error: Could not find an available port between 3000 and $MAX_PORT"
    exit 1
fi

# Start a simple HTTP server
echo "Starting server at http://localhost:$PORT"
echo "Press Ctrl+C to stop the server"

# Start the server
$PYTHON -m http.server $PORT