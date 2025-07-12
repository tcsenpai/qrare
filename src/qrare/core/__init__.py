"""
Core functionality for binary QR conversion.

Contains the main converter class and supporting modules for encoding,
decoding, and configuration management.
"""

from .converter import BinaryQRConverter
from .encoder import QREncoder
from .decoder import QRDecoder
from .config import QRConfig

__all__ = ["BinaryQRConverter", "QREncoder", "QRDecoder", "QRConfig"]