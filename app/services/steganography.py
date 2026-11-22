
from PIL import Image, UnidentifiedImageError

MAGIC = b"STEG"
HEADER_SIZE = 64  # 4-byte magic + 4-byte message length


from app.core.service_exceptions import (
    CapacityExceededError,
    InvalidImageError,
    CorruptedPayloadError
)

def calculate_capacity(image_path):
    try:
        with Image.open(image_path) as image:
            width, height = image.size
            total_bits = width * height * 3
            available_bytes = (total_bits - HEADER_SIZE) // 8
            return max(0, available_bytes)

    except (OSError, UnidentifiedImageError) as exc:
        raise InvalidImageError("Invalid or unsupported image")


def encode_message(image_path, message, output_path):
    try:
        with Image.open(image_path) as source:
            image = source.convert("RGB")

    except (OSError, UnidentifiedImageError) as exc:
        raise InvalidImageError("Invalid or unsupported image")

    message_bytes = message.encode("utf-8")

    payload = (
        MAGIC
        + len(message_bytes).to_bytes(4, byteorder="big")
        + message_bytes
    )

    binary_data = "".join(format(byte, "08b") for byte in payload)
    pixels = list(image.getdata())

    if len(binary_data) > len(pixels) * 3:
        raise CapacityExceededError("Message exceeds image capacity")

    new_pixels = []
    data_index = 0

    for pixel in pixels:
        channels = list(pixel)

        for i in range(3):
            if data_index < len(binary_data):
                channels[i] = (
                    (channels[i] & 254)
                    | int(binary_data[data_index])
                )
                data_index += 1

        new_pixels.append(tuple(channels))

    image.putdata(new_pixels)
    image.save(output_path, format="PNG")

    return output_path


def decode_message(image_path):
    try:
        with Image.open(image_path) as source:
            image = source.convert("RGB")

    except (OSError, UnidentifiedImageError) as exc:
        raise InvalidImageError("Invalid or unsupported image")

    pixels = list(image.getdata())
    total_bits = len(pixels) * 3

    if total_bits < HEADER_SIZE:
        raise ValueError("Image is too small")

    header_bits = []

    for pixel in pixels:
        for channel in pixel:
            header_bits.append(str(channel & 1))

            if len(header_bits) == HEADER_SIZE:
                break

        if len(header_bits) == HEADER_SIZE:
            break

    header = "".join(header_bits)

    magic_bits = header[:32]
    length_bits = header[32:64]

    magic = bytes(
        int(magic_bits[i:i + 8], 2)
        for i in range(0, 32, 8)
    )

    if magic != MAGIC:
        raise CorruptedPayloadError("No hidden message found in this image")

    message_length = int(length_bits, 2)
    required_bits = HEADER_SIZE + message_length * 8

    if required_bits > total_bits:
        raise CorruptedPayloadError("Invalid or corrupted hidden payload")

    bits = []

    for pixel in pixels:
        for channel in pixel:
            bits.append(str(channel & 1))

    message_bits = "".join(bits[HEADER_SIZE:required_bits])

    message_bytes = bytes(
        int(message_bits[i:i + 8], 2)
        for i in range(0, len(message_bits), 8)
    )

    try:
        return message_bytes.decode("utf-8")

    except UnicodeDecodeError as exc:
        raise CorruptedPayloadError("Hidden message is corrupted")



