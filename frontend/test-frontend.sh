#!/bin/bash

# Exit script on any error
set -e

# Build the frontend
echo "Building frontend..."
./build.sh

# Start a simple HTTP server for the frontend
echo "Starting frontend server at http://localhost:3000..."
cd dist
python -m http.server 3000

# Note: This script doesn't return until the server is stopped with Ctrl+C