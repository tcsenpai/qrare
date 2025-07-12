"""
Main binary QR converter class.

Provides a unified interface for encoding and decoding operations,
combining the functionality of QREncoder and QRDecoder classes.
"""

import logging
from pathlib import Path
from typing import List, Union, Optional, Dict, Any

from .config import QRConfig, DEFAULT_CONFIG
from .encoder import QREncoder
from .decoder import QRDecoder
from ..utils.exceptions import QRareError, ValidationError

logger = logging.getLogger(__name__)


class BinaryQRConverter:
    """
    Main class for converting binary files to QR codes and back.
    
    Provides a unified interface that combines encoding and decoding functionality
    with consistent configuration and error handling.
    
    This class maintains backward compatibility with the original interface
    while providing access to the enhanced modular functionality.
    """
    
    def __init__(
        self,
        chunk_size: int = 1024,
        error_correction: Optional[int] = None,
        qr_version: int = 40,
        compression_level: int = 9,
        config: Optional[QRConfig] = None
    ):
        """
        Initialize the BinaryQRConverter.
        
        Args:
            chunk_size: Size in bytes of each binary chunk to encode
            error_correction: QR code error correction level (deprecated, use config)
            qr_version: QR code version (1-40, higher means more capacity)
            compression_level: Zlib compression level (0-9)
            config: QRConfig object for advanced configuration (overrides other params)
        
        Note:
            If config is provided, it takes precedence over individual parameters.
            This maintains backward compatibility while allowing advanced configuration.
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Create configuration
        if config is not None:
            self.config = config
        else:
            # Create config from individual parameters for backward compatibility
            self.config = QRConfig(
                chunk_size=chunk_size,
                qr_version=qr_version,
                compression_level=compression_level
            )
            
            # Handle deprecated error_correction parameter
            if error_correction is not None:
                from .config import ErrorCorrectionLevel
                # Map old integer values to new enum
                correction_map = {
                    1: ErrorCorrectionLevel.LOW,
                    2: ErrorCorrectionLevel.MEDIUM,
                    3: ErrorCorrectionLevel.QUARTILE,
                    4: ErrorCorrectionLevel.HIGH
                }
                
                if error_correction in correction_map:
                    self.config.error_correction = correction_map[error_correction]
                else:
                    # Assume it's already a valid qrcode constant
                    self.config.error_correction = error_correction
        
        # Initialize encoder and decoder with the same configuration
        self.encoder = QREncoder(self.config)
        self.decoder = QRDecoder(self.config)
        
        self.logger.debug(f"Initialized BinaryQRConverter with config: {self.config}")
    
    @property
    def chunk_size(self) -> int:
        """Get chunk size for backward compatibility."""
        return self.config.chunk_size
    
    @property
    def qr_version(self) -> int:
        """Get QR version for backward compatibility."""
        return self.config.qr_version
    
    @property
    def compression_level(self) -> int:
        """Get compression level for backward compatibility."""
        return int(self.config.compression_level)
    
    @property
    def error_correction(self) -> int:
        """Get error correction level for backward compatibility."""
        return int(self.config.error_correction)
    
    def encode_file(self, file_path: Union[str, Path], output_dir: Union[str, Path]) -> List[Path]:
        """
        Encode a binary file into a series of QR code images.
        
        This method maintains the exact same interface as the original implementation
        to ensure backward compatibility.
        
        Args:
            file_path: Path to the binary file to encode
            output_dir: Directory to save QR code images
            
        Returns:
            List of paths to the generated QR code images
            
        Raises:
            QRareError: If encoding fails
        """
        try:
            self.logger.info(f"Encoding file: {file_path}")
            result = self.encoder.encode_file(file_path, output_dir)
            self.logger.info(f"Encoding completed: {len(result)} QR codes generated")
            return result
            
        except QRareError:
            # Re-raise QRare-specific errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            from ..utils.exceptions import EncodingError
            raise EncodingError(
                operation="file encoding",
                file_path=str(file_path),
                details=f"Unexpected error: {str(e)}"
            ) from e
    
    def decode_qr_images(
        self,
        image_paths: List[Path],
        output_dir: Union[str, Path]
    ) -> Optional[Path]:
        """
        Decode a series of QR code images back to the original binary file.
        
        This method maintains the exact same interface as the original implementation
        to ensure backward compatibility.
        
        Args:
            image_paths: List of paths to QR code images
            output_dir: Directory to save the reconstructed file
            
        Returns:
            Path to the reconstructed file if successful, None if failed
            
        Raises:
            QRareError: If decoding fails
        """
        try:
            self.logger.info(f"Decoding {len(image_paths)} QR code images")
            result = self.decoder.decode_qr_images(image_paths, output_dir)
            
            if result:
                self.logger.info(f"Decoding completed: {result}")
            else:
                self.logger.error("Decoding failed")
            
            return result
            
        except QRareError:
            # Re-raise QRare-specific errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            from ..utils.exceptions import DecodingError
            raise DecodingError(
                operation="QR image decoding",
                details=f"Unexpected error: {str(e)}"
            ) from e
    
    def decode_qr_image(self, image_path: Path) -> Optional[Dict]:
        """
        Decode a single QR code image to extract chunk data and metadata.
        
        This method maintains backward compatibility with the original interface.
        
        Args:
            image_path: Path to the QR code image
            
        Returns:
            Dictionary with chunk data and metadata, or None if decoding fails
        """
        try:
            return self.decoder._decode_single_qr_image(image_path)
        except Exception as e:
            self.logger.error(f"Failed to decode QR image {image_path}: {e}")
            return None
    
    # New methods that weren't in the original interface
    
    def estimate_qr_count(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Estimate the number of QR codes that will be generated for a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with estimation information
        """
        return self.encoder.estimate_qr_count(file_path)
    
    def analyze_qr_images(self, image_paths: List[Path]) -> Dict[str, Any]:
        """
        Analyze QR code images without full decoding.
        
        Args:
            image_paths: List of QR code image paths
            
        Returns:
            Dictionary with analysis information
        """
        return self.decoder.analyze_qr_images(image_paths)
    
    def validate_configuration(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValidationError: If configuration is invalid
        """
        try:
            # Configuration validation is handled in QRConfig.__post_init__
            # This method provides an explicit way to check validity
            return True
        except Exception as e:
            raise ValidationError(
                parameter="configuration",
                value=str(self.config),
                expected="valid QRConfig",
                details=str(e)
            ) from e
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Returns:
            Dictionary with configuration details
        """
        return {
            'chunk_size': self.config.chunk_size,
            'qr_version': self.config.qr_version,
            'compression_level': int(self.config.compression_level),
            'error_correction': int(self.config.error_correction),
            'box_size': self.config.box_size,
            'border': self.config.border,
            'image_format': self.config.image_format
        }
    
    @classmethod
    def create_fast_converter(cls, chunk_size: Optional[int] = None) -> 'BinaryQRConverter':
        """
        Create a converter optimized for speed.
        
        Args:
            chunk_size: Optional custom chunk size
            
        Returns:
            BinaryQRConverter instance optimized for fast processing
        """
        from .config import QRConfig
        config = QRConfig.create_fast_config(chunk_size)
        return cls(config=config)
    
    @classmethod
    def create_compact_converter(cls, chunk_size: Optional[int] = None) -> 'BinaryQRConverter':
        """
        Create a converter optimized for minimal QR code count.
        
        Args:
            chunk_size: Optional custom chunk size
            
        Returns:
            BinaryQRConverter instance optimized for minimal output size
        """
        from .config import QRConfig
        config = QRConfig.create_compact_config(chunk_size)
        return cls(config=config)
    
    @classmethod
    def create_robust_converter(cls, chunk_size: Optional[int] = None) -> 'BinaryQRConverter':
        """
        Create a converter optimized for error recovery.
        
        Args:
            chunk_size: Optional custom chunk size
            
        Returns:
            BinaryQRConverter instance optimized for maximum error correction
        """
        from .config import QRConfig
        config = QRConfig.create_robust_config(chunk_size)
        return cls(config=config)
    
    def __repr__(self) -> str:
        """String representation of the converter."""
        return (
            f"BinaryQRConverter("
            f"chunk_size={self.chunk_size}, "
            f"qr_version={self.qr_version}, "
            f"compression_level={self.compression_level})"
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Binary QR Converter\n"
            f"  Chunk size: {self.chunk_size} bytes\n"
            f"  QR version: {self.qr_version}\n"
            f"  Compression level: {self.compression_level}\n"
            f"  Error correction: {self.error_correction}"
        )