
import pytest
from io import BytesIO
from PIL import Image


@pytest.fixture
def sample_image():

    image = Image.new("RGB", (200, 200), color="white")

    buffer = BytesIO()

    image.save(buffer, format="PNG")

    buffer.seek(0)

    return buffer
