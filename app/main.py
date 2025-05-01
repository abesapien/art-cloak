from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from app.routers import stylizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY environment variable is not set. The application may not function correctly.")

# Initialize FastAPI app
app = FastAPI(
    title="ArtCloak Image Generator",
    description="An API that creates and edits images using OpenAI's GPT-image-1 and DALL-E 3 models",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stylizer.router)

# Global exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
    )

# API Info route
@app.get("/info")
async def api_info():
    return {
        "app_name": "ArtCloak Image Generator",
        "version": "1.0.0",
        "capabilities": [
            "Generate images by editing a reference image using GPT-image-1",
            "Create new images from text descriptions using DALL-E 3"
        ],
        "endpoints": [
            {"path": "/generate/", "description": "Edit a reference image"},
            {"path": "/create/", "description": "Create a new image from text"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
