
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, UnidentifiedImageError

from app.services.steganography import (
    encode_message,
    decode_message,
    calculate_capacity
)


from app.core.exceptions import AppException

from app.core.service_exceptions import (
    CapacityExceededError,
    InvalidImageError,
    CorruptedPayloadError
)

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PIXELS = 25_000_000
ALLOWED_FORMATS = {"PNG", "BMP","JPEG", "JPG"}




def validate_image(data: bytes):
    try:
        with Image.open(BytesIO(data)) as image:

            if image.format not in ALLOWED_FORMATS:
                raise AppException(
                    status_code=415,
                    error_code="UNSUPPORTED_FORMAT",
                    message="Only PNG, BMP, and JPEG images are supported."
                )

            if image.width * image.height > MAX_PIXELS:
                raise AppException(
                    status_code=413,
                    error_code="IMAGE_TOO_LARGE",
                    message="Image dimensions exceed the allowed limit."
                )

            image.verify()

    except AppException:
        raise

    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError
    ):
        raise AppException(
            status_code=400,
            error_code="INVALID_IMAGE",
            message="The uploaded image is invalid or corrupted."
        )





async def read_image(file: UploadFile) -> bytes:
    data = await file.read(MAX_FILE_SIZE + 1)

    if not data:
        raise AppException(
            status_code=400,
            error_code="EMPTY_UPLOAD",
            message="Uploaded image is empty."
        )

    if len(data) > MAX_FILE_SIZE:
        raise AppException(
            status_code=413,
            error_code="FILE_TOO_LARGE",
            message="Maximum upload size is 10 MB."
        )

    validate_image(data)
    return data




@router.post("/encode")
async def encode(
    image: UploadFile = File(...),
    message: str = Form(...)
):
    if not message:
        raise AppException(
            status_code=400,
            error_code="EMPTY_MESSAGE",
            message="Message cannot be empty."
        )

    image_data = await read_image(image)

    with TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "input.png"
        output_path = Path(temp_dir) / "encoded.png"

        input_path.write_bytes(image_data)

        try:
            encode_message(
                str(input_path),
                message,
                str(output_path)
            )

        except CapacityExceededError as exc:
            raise AppException(
                status_code=400,
                error_code="CAPACITY_EXCEEDED",
                message=str(exc)
            ) from exc

        except InvalidImageError as exc:
            raise AppException(
                status_code=400,
                error_code="INVALID_IMAGE",
                message=str(exc)
            ) from exc

        encoded_data = output_path.read_bytes()

    logger.info("Image encoding completed successfully")

    return StreamingResponse(
        BytesIO(encoded_data),
        media_type="image/png",
        headers={
            "Content-Disposition": 'attachment; filename="encoded.png"'
        }
    )




@router.post("/decode")
async def decode(image: UploadFile = File(...)):
    image_data = await read_image(image)

    with TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "encoded.png"
        input_path.write_bytes(image_data)

        try:
            message = decode_message(str(input_path))

        except CorruptedPayloadError as exc:
            raise AppException(
                status_code=400,
                error_code="CORRUPTED_PAYLOAD",
                message=str(exc)
            ) from exc

        except InvalidImageError as exc:
            raise AppException(
                status_code=400,
                error_code="INVALID_IMAGE",
                message=str(exc)
            ) from exc

    logger.info("Image encoding completed successfully")


    return {
        "success": True,
        "message": message
    }




@router.post("/capacity")
async def capacity(image: UploadFile = File(...)):
    image_data = await read_image(image)

    with TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "input.png"
        input_path.write_bytes(image_data)

        try:
            available_bytes = calculate_capacity(str(input_path))

        except InvalidImageError as exc:
            raise AppException(
                status_code=400,
                error_code="INVALID_IMAGE",
                message=str(exc)
            ) from exc


    logger.info("Image capacity calculated successfully")
    
    return {
        "unit": "bytes",
        "maximum_message_bytes": available_bytes
    }



import logging

logger = logging.getLogger("steganography-api")
