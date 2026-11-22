
class SteganographyError(Exception):
    """Base exception for steganography operations."""


class CapacityExceededError(SteganographyError):
    """Raised when the message exceeds image capacity."""


class InvalidImageError(SteganographyError):
    """Raised when an image is invalid or unsupported."""


class CorruptedPayloadError(SteganographyError):
    """Raised when a hidden payload cannot be decoded."""
