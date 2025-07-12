"""
QRare - Binary QR Converter

Main package providing functionality for converting binary files to QR codes
and reconstructing them back to the original files.
"""

from .core.converter import BinaryQRConverter
from .core.encoder import QREncoder
from .core.decoder import QRDecoder
from .core.config import QRConfig, CompressionLevel, ErrorCorrectionLevel

__all__ = [
    "BinaryQRConverter",
    "QREncoder",
    "QRDecoder", 
    "QRConfig",
    "CompressionLevel",
    "ErrorCorrectionLevel",
]