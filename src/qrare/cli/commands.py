"""
Command implementations for the QRare CLI.

Contains the actual command logic separated from argument parsing
for better testability and maintainability.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from ..core.converter import BinaryQRConverter
from ..core.config import QRConfig, CompressionLevel, ErrorCorrectionLevel
from ..utils.path_utils import get_image_paths
from ..utils.exceptions import QRareError, ValidationError

logger = logging.getLogger(__name__)


def encode_command(
    file_path: Union[str, Path],
    output_dir: Union[str, Path],
    chunk_size: int = 1024,
    qr_version: int = 40,
    compression_level: int = 9,
    preset: Optional[str] = None
) -> List[Path]:
    """
    Execute the encode command to convert a file to QR codes.
    
    Args:
        file_path: Path to the binary file to encode
        output_dir: Directory to save QR code images
        chunk_size: Size of binary chunks in bytes
        qr_version: QR code version (1-40)
        compression_level: Zlib compression level (0-9)
        preset: Optional preset configuration ('fast', 'compact', 'robust')
        
    Returns:
        List of paths to the generated QR code images
        
    Raises:
        QRareError: If encoding fails
        ValidationError: If parameters are invalid
    """
    logger.info(f"Starting encode operation for {file_path}")
    
    try:
        # Create converter based on preset or individual parameters
        if preset:
            converter = _create_converter_from_preset(preset, chunk_size)
        else:
            # Validate parameters
            _validate_encode_parameters(chunk_size, qr_version, compression_level)
            
            # Create configuration
            config = QRConfig(
                chunk_size=chunk_size,
                qr_version=qr_version,
                compression_level=CompressionLevel(compression_level)
            )
            converter = BinaryQRConverter(config=config)
        
        # Show estimation
        estimation = converter.estimate_qr_count(file_path)
        logger.info(
            f"Estimation: ~{estimation['estimated_chunks']} QR codes "
            f"({estimation['original_size']} → {estimation['estimated_compressed_size']} bytes)"
        )
        
        # Perform encoding
        qr_image_paths = converter.encode_file(file_path, output_dir)
        
        logger.info(f"Successfully created {len(qr_image_paths)} QR code images")
        return qr_image_paths
        
    except QRareError:
        raise
    except Exception as e:
        from ..utils.exceptions import EncodingError
        raise EncodingError(
            operation="command execution",
            file_path=str(file_path),
            details=f"Unexpected error: {str(e)}"
        ) from e


def decode_command(
    image_args: List[str],
    output_dir: Union[str, Path],
    analyze_only: bool = False
) -> Optional[Path]:
    """
    Execute the decode command to reconstruct a file from QR codes.
    
    Args:
        image_args: List of image paths, directories, or glob patterns
        output_dir: Directory to save the reconstructed file
        analyze_only: If True, only analyze QR codes without decoding
        
    Returns:
        Path to the reconstructed file if successful, None if failed
        
    Raises:
        QRareError: If decoding fails
        ValidationError: If parameters are invalid
    """
    logger.info(f"Starting decode operation with {len(image_args)} image arguments")
    
    try:
        # Get image paths
        image_paths = get_image_paths(image_args)
        logger.info(f"Found {len(image_paths)} image files")
        
        # Create converter
        converter = BinaryQRConverter()
        
        if analyze_only:
            # Perform analysis only
            analysis = converter.analyze_qr_images(image_paths)
            _report_analysis_results(analysis)
            return None
        
        # Perform analysis first for validation
        analysis = converter.analyze_qr_images(image_paths)
        _validate_analysis_results(analysis)
        
        # Perform decoding
        output_path = converter.decode_qr_images(image_paths, output_dir)
        
        if output_path:
            logger.info(f"Successfully reconstructed file: {output_path}")
        else:
            logger.error("Failed to reconstruct file")
        
        return output_path
        
    except QRareError:
        raise
    except Exception as e:
        from ..utils.exceptions import DecodingError
        raise DecodingError(
            operation="command execution",
            details=f"Unexpected error: {str(e)}"
        ) from e


def version_command() -> str:
    """
    Execute the version command to show version information.
    
    Returns:
        Version information string
    """
    # Import here to avoid circular imports
    from ... import __version__
    
    version_info = f"QRare Binary QR Converter version {__version__}"
    logger.info(version_info)
    return version_info


def analyze_command(image_args: List[str]) -> dict:
    """
    Execute the analyze command to examine QR codes without decoding.
    
    Args:
        image_args: List of image paths, directories, or glob patterns
        
    Returns:
        Analysis results dictionary
        
    Raises:
        QRareError: If analysis fails
    """
    logger.info(f"Starting analysis of QR codes")
    
    try:
        # Get image paths
        image_paths = get_image_paths(image_args)
        logger.info(f"Found {len(image_paths)} image files")
        
        # Create converter and analyze
        converter = BinaryQRConverter()
        analysis = converter.analyze_qr_images(image_paths)
        
        _report_analysis_results(analysis)
        return analysis
        
    except QRareError:
        raise
    except Exception as e:
        from ..utils.exceptions import DecodingError
        raise DecodingError(
            operation="QR code analysis",
            details=f"Unexpected error: {str(e)}"
        ) from e


def _create_converter_from_preset(preset: str, chunk_size: Optional[int] = None) -> BinaryQRConverter:
    """
    Create a converter instance from a preset configuration.
    
    Args:
        preset: Preset name ('fast', 'compact', 'robust')
        chunk_size: Optional custom chunk size
        
    Returns:
        Configured BinaryQRConverter instance
        
    Raises:
        ValidationError: If preset is invalid
    """
    preset = preset.lower()
    
    if preset == 'fast':
        return BinaryQRConverter.create_fast_converter(chunk_size)
    elif preset == 'compact':
        return BinaryQRConverter.create_compact_converter(chunk_size)
    elif preset == 'robust':
        return BinaryQRConverter.create_robust_converter(chunk_size)
    else:
        raise ValidationError(
            parameter="preset",
            value=preset,
            expected="'fast', 'compact', or 'robust'",
            details="Unknown preset configuration"
        )


def _validate_encode_parameters(chunk_size: int, qr_version: int, compression_level: int) -> None:
    """
    Validate encoding parameters.
    
    Args:
        chunk_size: Chunk size in bytes
        qr_version: QR code version
        compression_level: Compression level
        
    Raises:
        ValidationError: If any parameter is invalid
    """
    if chunk_size <= 0:
        raise ValidationError(
            parameter="chunk_size",
            value=chunk_size,
            expected="positive integer"
        )
    
    if not (1 <= qr_version <= 40):
        raise ValidationError(
            parameter="qr_version",
            value=qr_version,
            expected="integer between 1 and 40"
        )
    
    if not (0 <= compression_level <= 9):
        raise ValidationError(
            parameter="compression_level",
            value=compression_level,
            expected="integer between 0 and 9"
        )


def _validate_analysis_results(analysis: dict) -> None:
    """
    Validate analysis results and warn about potential issues.
    
    Args:
        analysis: Analysis results dictionary
        
    Raises:
        ValidationError: If critical issues are found
    """
    if analysis['failed_qrs'] > 0:
        logger.warning(f"Failed to read {analysis['failed_qrs']} QR codes")
    
    if analysis['readable_qrs'] == 0:
        raise ValidationError(
            parameter="qr_codes",
            value=f"{analysis['total_images']} images",
            expected="at least one readable QR code"
        )
    
    # Check for incomplete files
    incomplete_files = []
    for filename, info in analysis['chunk_info'].items():
        if not info['is_complete']:
            incomplete_files.append(filename)
            missing_chunks = set(range(info['total_chunks'])) - set(info['found_chunks'])
            logger.warning(
                f"File '{filename}' is incomplete: "
                f"missing chunks {sorted(missing_chunks)}"
            )
    
    if incomplete_files:
        raise ValidationError(
            parameter="qr_chunks",
            value=f"incomplete files: {', '.join(incomplete_files)}",
            expected="complete set of chunks for each file"
        )


def _report_analysis_results(analysis: dict) -> None:
    """
    Report analysis results to the user.
    
    Args:
        analysis: Analysis results dictionary
    """
    logger.info(f"QR Code Analysis Results:")
    logger.info(f"  Total images: {analysis['total_images']}")
    logger.info(f"  Readable QR codes: {analysis['readable_qrs']}")
    logger.info(f"  Failed QR codes: {analysis['failed_qrs']}")
    logger.info(f"  Unique files: {len(analysis['unique_files'])}")
    
    if analysis['unique_files']:
        for filename in analysis['unique_files']:
            info = analysis['chunk_info'][filename]
            status = "✓ Complete" if info['is_complete'] else "✗ Incomplete"
            logger.info(
                f"    {filename}: {len(info['found_chunks'])}/{info['total_chunks']} chunks - {status}"
            )
    
    if analysis['errors']:
        logger.warning("Errors encountered:")
        for error in analysis['errors'][:5]:  # Show first 5 errors
            logger.warning(f"  {error}")
        if len(analysis['errors']) > 5:
            logger.warning(f"  ... and {len(analysis['errors']) - 5} more errors")