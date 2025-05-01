#!/bin/bash
# This script will help debug API errors by showing full response

curl -v -X POST \
  http://localhost:8001/stylize/ \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/image.jpg"