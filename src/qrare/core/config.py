"""
Configuration management for QRare.

Defines constants, enums, and configuration classes used throughout the application.
Centralizes all configurable parameters for easy maintenance and customization.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from qrcode.constants import (
    ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
)


class CompressionLevel(IntEnum):
    """
    Zlib compression levels.
    
    Higher values provide better compression but take more time.
    Level 0 disables compression entirely.
    """
    NONE = 0
    FASTEST = 1
    FAST = 3
    BALANCED = 6
    GOOD = 9
    BEST = 9


class ErrorCorrectionLevel(IntEnum):
    """
    QR Code error correction levels.
    
    Higher levels provide better error recovery but reduce data capacity.
    """
    LOW = ERROR_CORRECT_L      # ~7% error recovery
    MEDIUM = ERROR_CORRECT_M   # ~15% error recovery  
    QUARTILE = ERROR_CORRECT_Q # ~25% error recovery
    HIGH = ERROR_CORRECT_H     # ~30% error recovery


@dataclass
class QRConfig:
    """
    Configuration class for QR code generation and processing.
    
    Centralizes all configurable parameters with sensible defaults.
    Provides validation and ensures consistent configuration across components.
    
    Attributes:
        chunk_size: Size in bytes of each binary chunk to encode (default: 1024)
        error_correction: QR code error correction level (default: HIGH)
        qr_version: QR code version 1-40, higher means more capacity (default: 40)
        compression_level: Zlib compression level 0-9 (default: BEST)
        box_size: Size of each QR code box in pixels (default: 10)
        border: Border size around QR code in boxes (default: 4)
        fill_color: Foreground color for QR code (default: "black")
        back_color: Background color for QR code (default: "white")
        image_format: Output image format (default: "PNG")
    """
    
    # Core processing parameters
    chunk_size: int = 1024
    error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.HIGH
    qr_version: int = 40
    compression_level: CompressionLevel = CompressionLevel.BEST
    
    # QR code appearance
    box_size: int = 10
    border: int = 4
    fill_color: str = "black"
    back_color: str = "white"
    
    # Output format
    image_format: str = "PNG"
    
    def __post_init__(self):
        """
        Validate configuration parameters after initialization.
        
        Raises:
            ValueError: If any parameter is outside valid range
        """
        self._validate_chunk_size()
        self._validate_qr_version()
        self._validate_compression_level()
        self._validate_error_correction()
        self._validate_appearance_params()
    
    def _validate_chunk_size(self) -> None:
        """Validate chunk size parameter."""
        if not isinstance(self.chunk_size, int) or self.chunk_size <= 0:
            raise ValueError(f"chunk_size must be a positive integer, got {self.chunk_size}")
        
        if self.chunk_size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError(f"chunk_size too large: {self.chunk_size}, maximum is 10MB")
    
    def _validate_qr_version(self) -> None:
        """Validate QR version parameter."""
        if not isinstance(self.qr_version, int) or not (1 <= self.qr_version <= 40):
            raise ValueError(f"qr_version must be between 1 and 40, got {self.qr_version}")
    
    def _validate_compression_level(self) -> None:
        """Validate compression level parameter."""
        if not isinstance(self.compression_level, (int, CompressionLevel)):
            raise ValueError(f"compression_level must be int or CompressionLevel, got {type(self.compression_level)}")
        
        level_value = int(self.compression_level)
        if not (0 <= level_value <= 9):
            raise ValueError(f"compression_level must be between 0 and 9, got {level_value}")
    
    def _validate_error_correction(self) -> None:
        """Validate error correction level parameter."""
        valid_levels = {ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H}
        correction_value = int(self.error_correction)
        
        if correction_value not in valid_levels:
            raise ValueError(f"error_correction must be a valid qrcode error correction level, got {correction_value}")
    
    def _validate_appearance_params(self) -> None:
        """Validate appearance-related parameters."""
        if not isinstance(self.box_size, int) or self.box_size <= 0:
            raise ValueError(f"box_size must be a positive integer, got {self.box_size}")
        
        if not isinstance(self.border, int) or self.border < 0:
            raise ValueError(f"border must be a non-negative integer, got {self.border}")
        
        if not isinstance(self.fill_color, str) or not self.fill_color.strip():
            raise ValueError(f"fill_color must be a non-empty string, got {self.fill_color}")
        
        if not isinstance(self.back_color, str) or not self.back_color.strip():
            raise ValueError(f"back_color must be a non-empty string, got {self.back_color}")
    
    @classmethod
    def create_fast_config(cls, chunk_size: Optional[int] = None) -> 'QRConfig':
        """
        Create a configuration optimized for speed over compression.
        
        Args:
            chunk_size: Optional custom chunk size
            
        Returns:
            QRConfig instance optimized for fast processing
        """
        return cls(
            chunk_size=chunk_size or 2048,
            compression_level=CompressionLevel.FAST,
            error_correction=ErrorCorrectionLevel.LOW,
            qr_version=20
        )
    
    @classmethod  
    def create_compact_config(cls, chunk_size: Optional[int] = None) -> 'QRConfig':
        """
        Create a configuration optimized for minimal QR code count.
        
        Args:
            chunk_size: Optional custom chunk size
            
        Returns:
            QRConfig instance optimized for minimal output size
        """
        return cls(
            chunk_size=chunk_size or 2048,
            compression_level=CompressionLevel.BEST,
            error_correction=ErrorCorrectionLevel.LOW,
            qr_version=40
        )
    
    @classmethod
    def create_robust_config(cls, chunk_size: Optional[int] = None) -> 'QRConfig':
        """
        Create a configuration optimized for error recovery.
        
        Args:
            chunk_size: Optional custom chunk size
            
        Returns:
            QRConfig instance optimized for maximum error correction
        """
        return cls(
            chunk_size=chunk_size or 512,
            compression_level=CompressionLevel.GOOD,
            error_correction=ErrorCorrectionLevel.HIGH,
            qr_version=30
        )


# Default configuration instance
DEFAULT_CONFIG = QRConfig()


# Constants
MAX_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB
MIN_CHUNK_SIZE = 1  # 1 byte
MAX_QR_VERSION = 40
MIN_QR_VERSION = 1
SUPPORTED_IMAGE_FORMATS = {"PNG", "JPEG", "JPG", "BMP", "TIFF"}
DEFAULT_IMAGE_EXTENSION = ".png"
HASH_ALGORITHM = "sha256"
CHUNK_READ_SIZE = 4096  # For file hashing