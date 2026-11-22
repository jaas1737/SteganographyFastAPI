
from fastapi import FastAPI, HTTPException

from app.api.v1.router import api_router
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.core.logging import setup_logging

logger = setup_logging()

app = FastAPI(
    title="Secure Steganography API",
    description="An API for hiding and extracting messages from images.",
    version="1.0.0"
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "application": "Secure Steganography API"
    }
