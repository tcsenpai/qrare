"""
Binary QR Converter Package

A comprehensive toolkit for converting binary files to QR codes and back.
Provides both programmatic API and command-line interface.
"""

__version__ = "0.2.0"
__author__ = "QRare Project"
__description__ = "Convert binary files to QR codes and back with compression and verification"

# Import main classes for easy access
from .qrare.core.converter import BinaryQRConverter
from .qrare.core.encoder import QREncoder
from .qrare.core.decoder import QRDecoder

__all__ = [
    "BinaryQRConverter",
    "QREncoder", 
    "QRDecoder",
]