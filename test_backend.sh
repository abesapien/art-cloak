#!/bin/bash

# A simple script to test the backend API

# Check if curl is installed
which curl > /dev/null || { echo "Error: curl is not installed."; exit 1; }

# Find an available port for the backend
find_available_port() {
    # Try a much wider range of ports 
    local range_start=8000
    local range_end=9999
    
    for port in 8000 8080 5000 8888 9000; do
        python3 -c "import socket; s = socket.socket(); s.bind(('', $port)) and s.close()" &>/dev/null
        if [ $? -eq 0 ]; then
            echo $port
            return
        fi
    done
    
    # Try random ports 
    for i in {1..5}; do
        local random_port=$((range_start + RANDOM % (range_end - range_start + 1)))
        python3 -c "import socket; s = socket.socket(); s.bind(('', $random_port)) and s.close()" &>/dev/null
        if [ $? -eq 0 ]; then
            echo $random_port
            return
        fi
    done
    
    # Nothing found
    echo 0
}

# Get an available port
PORT=$(find_available_port)
if [ $PORT -eq 0 ]; then
    echo "Error: Could not find an available port"
    exit 1
fi

echo "Starting backend server for testing on port $PORT..."

# Run the backend in background but with proper logging
python3 -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=$PORT)" &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Test the health endpoint
echo "Testing health endpoint..."
curl -s "http://localhost:$PORT/health" | grep -q "ok"

if [ $? -eq 0 ]; then
    echo "✅ Health check successful"
else
    echo "❌ Health check failed"
fi

# Test if CORS is properly configured 
echo "Testing CORS headers..."
curl -s -I -X OPTIONS -H "Origin: http://localhost:3000" "http://localhost:$PORT/health" | grep -q "Access-Control-Allow-Origin"

if [ $? -eq 0 ]; then
    echo "✅ CORS is properly configured"
else
    echo "❌ CORS might have issues"
fi

# For further debugging, check available routes
echo "Available routes:"
curl -s "http://localhost:$PORT/info" | python3 -m json.tool

# Stop the server
echo "Stopping server..."
kill $SERVER_PID

echo "Test complete"