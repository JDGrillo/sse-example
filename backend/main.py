"""
Text Correction API - Main FastAPI application
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routes import corrections_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):  # Prefix with _ to indicate intentionally unused
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting Text Correction API...")
    logger.info("Environment: %s", settings.environment)
    logger.info("CORS Origins: %s", settings.get_cors_origins())
    yield
    logger.info("Shutting down Text Correction API...")


# Initialize FastAPI application
app = FastAPI(
    title="Text Correction API",
    description="Real-time text correction service using Microsoft Foundry GPT-4o",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(corrections_router)


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        dict: Health status information
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "text-correction-api",
            "version": "1.0.0",
            "environment": settings.environment,
        },
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {"message": "Text Correction API", "docs": "/docs", "health": "/api/health"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
