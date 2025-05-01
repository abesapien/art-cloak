#!/bin/bash

# Integration test runner for ArtCloak

# Set execution flags
set -e  # Exit on error
set -u  # Fail on undefined variables

# Display test header
echo "===== ArtCloak Integration Tests ====="
echo "Starting test run: $(date)"
echo

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed"
    exit 1
fi

# Check required packages
echo "Checking required packages..."
python3 -c "import unittest, requests, PIL" 2>/dev/null || {
    echo "Installing missing dependencies..."
    pip install requests pillow
}

# Check for OpenAI API Key
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "Warning: OPENAI_API_KEY environment variable is not set."
    echo "API-dependent tests will be skipped."
else
    echo "OpenAI API key is configured."
fi

# Run the integration tests
echo
echo "Running integration tests..."
python3 test_integration.py -v

# Check the test result
if [ $? -eq 0 ]; then
    echo
    echo "✅ All integration tests passed!"
else
    echo
    echo "❌ Some integration tests failed!"
    exit 1
fi

# Display test footer
echo
echo "Integration test run completed: $(date)"
echo "====================================="