#!/bin/bash

# Exit script on any error
set -e

echo "Building ArtCloak Frontend..."

# Make sure npm is installed
which npm > /dev/null || (echo "npm is not installed. Please install Node.js and npm first." && exit 1)

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

# Clean and recreate the dist directory
echo "Cleaning dist directory..."
rm -rf dist
mkdir -p dist

# Compile TypeScript files
echo "Compiling TypeScript..."
npx tsc

# Copy static files to dist directory
echo "Copying static files to dist directory..."
cp index.html dist/
cp style.css dist/
cp logger.js dist/

echo "Build complete. Frontend files are in dist/"
echo "To test the build, run: cd dist && python -m http.server 3000"