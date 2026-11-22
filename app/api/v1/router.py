
from fastapi import APIRouter

from app.api.v1.endpoints import steganography

api_router = APIRouter()

api_router.include_router(
    steganography.router,
    prefix="/steganography",
    tags=["Steganography"]
)
