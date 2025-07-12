"""
Path handling utilities for QRare.

Provides functions for path validation, image file discovery,
and path manipulation with comprehensive error handling.
"""

import logging
from pathlib import Path
from typing import List, Union, Optional, Set

from .exceptions import ValidationError, FileOperationError
from ..core.config import SUPPORTED_IMAGE_FORMATS, DEFAULT_IMAGE_EXTENSION

logger = logging.getLogger(__name__)


def validate_file_path(file_path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate and normalize a file path.
    
    Args:
        file_path: Path to validate
        must_exist: Whether the file must exist
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    try:
        path = Path(file_path).resolve()
    except (ValueError, OSError) as e:
        raise ValidationError(
            parameter="file_path",
            value=str(file_path),
            expected="valid file path",
            details=f"Path resolution failed: {str(e)}"
        ) from e
    
    if must_exist:
        if not path.exists():
            raise ValidationError(
                parameter="file_path",
                value=str(file_path),
                expected="existing file",
                details="File does not exist"
            )
        
        if not path.is_file():
            raise ValidationError(
                parameter="file_path", 
                value=str(file_path),
                expected="file path",
                details="Path points to a directory, not a file"
            )
    
    logger.debug(f"Validated file path: {path}")
    return path


def validate_directory_path(dir_path: Union[str, Path], create_if_missing: bool = False) -> Path:
    """
    Validate and normalize a directory path.
    
    Args:
        dir_path: Path to validate
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid
        FileOperationError: If directory creation fails
    """
    try:
        path = Path(dir_path).resolve()
    except (ValueError, OSError) as e:
        raise ValidationError(
            parameter="dir_path",
            value=str(dir_path),
            expected="valid directory path",
            details=f"Path resolution failed: {str(e)}"
        ) from e
    
    if not path.exists():
        if create_if_missing:
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {path}")
            except (OSError, IOError) as e:
                raise FileOperationError(
                    operation="directory creation",
                    path=str(path),
                    original_error=e
                ) from e
        else:
            raise ValidationError(
                parameter="dir_path",
                value=str(dir_path),
                expected="existing directory",
                details="Directory does not exist"
            )
    
    elif not path.is_dir():
        raise ValidationError(
            parameter="dir_path",
            value=str(dir_path),
            expected="directory path",
            details="Path points to a file, not a directory"
        )
    
    logger.debug(f"Validated directory path: {path}")
    return path


def get_image_paths(image_args: List[str]) -> List[Path]:
    """
    Get a list of image file paths from command line arguments.
    
    Handles individual files, directories, and glob patterns.
    Filters results to only include supported image formats.
    
    Args:
        image_args: List of image paths, directories, or glob patterns
        
    Returns:
        List of validated image file paths, sorted by name
        
    Raises:
        ValidationError: If no valid image files are found
    """
    if not image_args:
        raise ValidationError(
            parameter="image_args",
            value="[]",
            expected="non-empty list of image paths",
            details="No image paths provided"
        )
    
    image_paths = []
    processed_paths = set()  # Avoid duplicates
    
    for path_str in image_args:
        logger.debug(f"Processing image argument: {path_str}")
        
        try:
            path = Path(path_str)
            
            if path.is_dir():
                # Directory: find all supported image files
                dir_images = _find_images_in_directory(path)
                for img_path in dir_images:
                    if img_path not in processed_paths:
                        image_paths.append(img_path)
                        processed_paths.add(img_path)
                        
            elif path.is_file():
                # Individual file: validate it's a supported image format
                if _is_supported_image_format(path):
                    if path not in processed_paths:
                        image_paths.append(path)
                        processed_paths.add(path)
                else:
                    logger.warning(f"Skipping unsupported image format: {path}")
                    
            else:
                # Glob pattern: expand and filter
                expanded_paths = list(Path().glob(path_str))
                if expanded_paths:
                    for expanded_path in expanded_paths:
                        if expanded_path.is_file() and _is_supported_image_format(expanded_path):
                            if expanded_path not in processed_paths:
                                image_paths.append(expanded_path)
                                processed_paths.add(expanded_path)
                else:
                    logger.warning(f"Glob pattern '{path_str}' matched no files")
                    
        except (ValueError, OSError) as e:
            logger.warning(f"Error processing path '{path_str}': {e}")
            continue
    
    if not image_paths:
        raise ValidationError(
            parameter="image_args",
            value=str(image_args),
            expected="paths that resolve to supported image files",
            details=f"No valid image files found. Supported formats: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
        )
    
    # Sort paths for consistent processing order
    sorted_paths = sorted(image_paths, key=lambda p: p.name)
    
    logger.info(f"Found {len(sorted_paths)} image files")
    return sorted_paths


def _find_images_in_directory(directory: Path) -> List[Path]:
    """
    Find all supported image files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of image file paths
    """
    image_files = []
    
    try:
        for file_path in directory.iterdir():
            if file_path.is_file() and _is_supported_image_format(file_path):
                image_files.append(file_path)
                
    except (OSError, IOError) as e:
        logger.warning(f"Error reading directory {directory}: {e}")
    
    return image_files


def _is_supported_image_format(file_path: Path) -> bool:
    """
    Check if a file has a supported image format extension.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file has supported image extension
    """
    suffix = file_path.suffix.upper().lstrip('.')
    return suffix in SUPPORTED_IMAGE_FORMATS


def generate_qr_filename(
    original_filename: str,
    chunk_index: int,
    total_chunks: int,
    extension: str = DEFAULT_IMAGE_EXTENSION
) -> str:
    """
    Generate a standardized filename for QR code images.
    
    Args:
        original_filename: Name of the original file
        chunk_index: Index of the chunk (0-based)
        total_chunks: Total number of chunks
        extension: File extension for the QR image
        
    Returns:
        Formatted filename for the QR code image
    """
    # Clean original filename of problematic characters
    clean_name = _sanitize_filename(original_filename)
    
    # Generate filename with zero-padded chunk numbers for proper sorting
    chunk_digits = len(str(total_chunks))
    filename = f"{clean_name}_chunk_{chunk_index+1:0{chunk_digits}d}_of_{total_chunks}{extension}"
    
    return filename


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing or replacing problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for file systems
    """
    # Characters that are problematic in filenames
    problematic_chars = '<>:"/\\|?*'
    
    # Replace problematic characters with underscores
    sanitized = filename
    for char in problematic_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure we have at least some content
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized


def get_safe_output_path(output_dir: Path, filename: str) -> Path:
    """
    Generate a safe output path, handling potential filename conflicts.
    
    Args:
        output_dir: Directory where file will be saved
        filename: Desired filename
        
    Returns:
        Path that is safe to write to (may have suffix added to avoid conflicts)
    """
    base_path = output_dir / filename
    
    if not base_path.exists():
        return base_path
    
    # If file exists, add a numeric suffix
    stem = base_path.stem
    suffix = base_path.suffix
    counter = 1
    
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = output_dir / new_name
        
        if not new_path.exists():
            logger.debug(f"Generated safe output path: {new_path}")
            return new_path
        
        counter += 1
        
        # Safety check to prevent infinite loops
        if counter > 10000:
            raise FileOperationError(
                operation="safe path generation",
                path=str(base_path),
                details="Too many existing files with similar names"
            )


def extract_chunk_info_from_filename(filename: str) -> Optional[dict]:
    """
    Extract chunk information from a QR code filename.
    
    Attempts to parse filenames in the format generated by generate_qr_filename.
    
    Args:
        filename: QR code filename to parse
        
    Returns:
        Dictionary with chunk info if parsing successful, None otherwise
    """
    try:
        # Remove extension
        name_without_ext = Path(filename).stem
        
        # Look for the pattern: _chunk_X_of_Y
        parts = name_without_ext.split('_')
        
        if len(parts) >= 4:
            # Find chunk pattern from the end
            for i in range(len(parts) - 3, -1, -1):
                if (parts[i] == 'chunk' and 
                    parts[i+2] == 'of' and 
                    parts[i+1].isdigit() and 
                    parts[i+3].isdigit()):
                    
                    chunk_num = int(parts[i+1])
                    total_chunks = int(parts[i+3])
                    original_name = '_'.join(parts[:i])
                    
                    return {
                        'original_name': original_name,
                        'chunk_number': chunk_num,
                        'total_chunks': total_chunks,
                        'chunk_index': chunk_num - 1  # Convert to 0-based index
                    }
        
        return None
        
    except (ValueError, IndexError):
        return None