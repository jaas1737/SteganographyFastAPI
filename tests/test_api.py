
import pytest

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json()["status"] == "healthy"


def test_encode_endpoint(sample_image):

    response = client.post(
        "/api/v1/steganography/encode",
        files={
            "image": (
                "test.png",
                sample_image.getvalue(),
                "image/png"
            )
        },
        data={
            "message": "Hello FastAPI!"
        }
    )

    assert response.status_code == 200

    assert response.headers["content-type"] == "image/png"


def test_decode_endpoint(sample_image):

    encoded = client.post(
        "/api/v1/steganography/encode",
        files={
            "image": (
                "test.png",
                sample_image.getvalue(),
                "image/png"
            )
        },
        data={
            "message": "Hello FastAPI!"
        }
    )

    assert encoded.status_code == 200

    decoded = client.post(
        "/api/v1/steganography/decode",
        files={
            "image": (
                "encoded.png",
                (
                    encoded.content
                ),
                "image/png"
            )
        }
    )

    assert decoded.status_code == 200

    assert decoded.json()["message"] == "Hello FastAPI!"


def test_capacity_endpoint(sample_image):

    response = client.post(
        "/api/v1/steganography/capacity",
        files={
            "image": (
                "test.png",
                sample_image.getvalue(),
                "image/png"
            )
        }
    )

    assert response.status_code == 200

    assert response.json()["maximum_message_bytes"] > 0






from io import BytesIO


from PIL import Image
from fastapi.testclient import TestClient

import app.api.v1.endpoints.steganography as endpoint


client = TestClient(app)


def test_empty_file():
    response = client.post(
        "/api/v1/steganography/encode",
        files={"image": ("empty.png", b"", "image/png")},
        data={"message": "Hello"}
    )

    assert response.status_code == 400


def test_invalid_image():
    response = client.post(
        "/api/v1/steganography/encode",
        files={"image": ("invalid.png", b"not an image", "image/png")},
        data={"message": "Hello"}
    )

    assert response.status_code == 400


def test_unsupported_image_format():
    buffer = BytesIO()
    Image.new("RGB", (100, 100)).save(buffer, format="GIF")

    response = client.post(
        "/api/v1/steganography/encode",
        files={"image": ("test.gif", buffer.getvalue(), "image/gif")},
        data={"message": "Hello"}
    )

    assert response.status_code == 415


def test_oversized_file():
    data = b"x" * (endpoint.MAX_FILE_SIZE + 1)

    response = client.post(
        "/api/v1/steganography/encode",
        files={"image": ("large.png", data, "image/png")},
        data={"message": "Hello"}
    )

    assert response.status_code == 413


def test_excessive_image_dimensions(monkeypatch):
    monkeypatch.setattr(endpoint, "MAX_PIXELS", 100)

    buffer = BytesIO()
    Image.new("RGB", (11, 10)).save(buffer, format="PNG")

    response = client.post(
        "/api/v1/steganography/encode",
        files={"image": ("large.png", buffer.getvalue(), "image/png")},
        data={"message": "Hello"}
    )

    assert response.status_code == 413


def test_empty_message(sample_image):
    response = client.post(
        "/api/v1/steganography/encode",
        files={
            "image": (
                "test.png",
                sample_image.getvalue(),
                "image/png"
            )
        },
        data={"message": ""}
    )

    assert response.status_code == 400


def test_message_exceeds_capacity():
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")

    response = client.post(
        "/api/v1/steganography/encode",
        files={"image": ("small.png", buffer.getvalue(), "image/png")},
        data={"message": "This message is too long"}
    )

    assert response.status_code == 400


def test_decode_image_without_hidden_message(sample_image):
    response = client.post(
        "/api/v1/steganography/decode",
        files={
            "image": (
                "normal.png",
                sample_image.getvalue(),
                "image/png"
            )
        }
    )

    assert response.status_code == 400
