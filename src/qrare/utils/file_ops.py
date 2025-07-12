"""
File operation utilities for QRare.

Provides robust file handling, hashing, compression, and path management
with comprehensive error handling and logging.
"""

import hashlib
import logging
import zlib
from pathlib import Path
from typing import Optional, BinaryIO, Iterator, Union

from .exceptions import FileOperationError, CompressionError
from ..core.config import HASH_ALGORITHM, CHUNK_READ_SIZE

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = HASH_ALGORITHM) -> str:
    """
    Calculate cryptographic hash of a file.
    
    Reads the file in chunks to handle large files efficiently without
    loading the entire file into memory.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string representation of the file hash
        
    Raises:
        FileOperationError: If file cannot be read or hash calculation fails
        ValidationError: If algorithm is not supported
    """
    file_path = Path(file_path)
    
    try:
        # Validate hash algorithm
        hash_obj = hashlib.new(algorithm)
    except ValueError as e:
        from .exceptions import ValidationError
        raise ValidationError(
            parameter="algorithm",
            value=algorithm,
            expected="supported hash algorithm",
            details=f"Available algorithms: {', '.join(hashlib.algorithms_available)}"
        ) from e
    
    try:
        with open(file_path, "rb") as f:
            # Read and update hash in chunks to handle large files
            for chunk in iter(lambda: f.read(CHUNK_READ_SIZE), b""):
                hash_obj.update(chunk)
        
        result = hash_obj.hexdigest()
        logger.debug(f"Calculated {algorithm} hash for {file_path}: {result}")
        return result
        
    except (OSError, IOError) as e:
        raise FileOperationError(
            operation="hashing",
            path=str(file_path),
            original_error=e,
            context={'algorithm': algorithm}
        ) from e


class FileManager:
    """
    Manages file operations with robust error handling and logging.
    
    Provides methods for reading, writing, compression, and validation
    of files with consistent error handling and progress reporting.
    """
    
    def __init__(self, compression_level: int = 9):
        """
        Initialize FileManager.
        
        Args:
            compression_level: Zlib compression level (0-9)
        """
        self.compression_level = compression_level
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def read_file(self, file_path: Union[str, Path]) -> bytes:
        """
        Read entire file content into memory.
        
        Args:
            file_path: Path to file to read
            
        Returns:
            File content as bytes
            
        Raises:
            FileOperationError: If file cannot be read
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.logger.debug(f"Read {len(content)} bytes from {file_path}")
            return content
            
        except (OSError, IOError) as e:
            raise FileOperationError(
                operation="reading",
                path=str(file_path),
                original_error=e
            ) from e
    
    def write_file(self, file_path: Union[str, Path], content: bytes, create_dirs: bool = True) -> None:
        """
        Write content to file.
        
        Args:
            file_path: Path where to write the file
            content: Binary content to write
            create_dirs: Whether to create parent directories if they don't exist
            
        Raises:
            FileOperationError: If file cannot be written
        """
        file_path = Path(file_path)
        
        try:
            # Create parent directories if requested and they don't exist
            if create_dirs and not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {file_path.parent}")
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            self.logger.debug(f"Wrote {len(content)} bytes to {file_path}")
            
        except (OSError, IOError) as e:
            raise FileOperationError(
                operation="writing",
                path=str(file_path),
                original_error=e,
                context={'content_size': len(content)}
            ) from e
    
    def compress_data(self, data: bytes) -> bytes:
        """
        Compress binary data using zlib.
        
        Args:
            data: Binary data to compress
            
        Returns:
            Compressed binary data
            
        Raises:
            CompressionError: If compression fails
        """
        try:
            compressed = zlib.compress(data, level=self.compression_level)
            
            compression_ratio = len(compressed) / len(data) if data else 0
            self.logger.debug(
                f"Compressed {len(data)} bytes to {len(compressed)} bytes "
                f"(ratio: {compression_ratio:.2f})"
            )
            
            return compressed
            
        except zlib.error as e:
            raise CompressionError(
                operation="compression",
                original_error=e,
                context={
                    'original_size': len(data),
                    'compression_level': self.compression_level
                }
            ) from e
    
    def decompress_data(self, compressed_data: bytes) -> bytes:
        """
        Decompress binary data using zlib.
        
        Args:
            compressed_data: Compressed binary data
            
        Returns:
            Decompressed binary data
            
        Raises:
            CompressionError: If decompression fails
        """
        try:
            decompressed = zlib.decompress(compressed_data)
            
            self.logger.debug(
                f"Decompressed {len(compressed_data)} bytes to {len(decompressed)} bytes"
            )
            
            return decompressed
            
        except zlib.error as e:
            raise CompressionError(
                operation="decompression",
                original_error=e,
                context={'compressed_size': len(compressed_data)}
            ) from e
    
    def get_file_info(self, file_path: Union[str, Path]) -> dict:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information including size, hash, etc.
            
        Raises:
            FileOperationError: If file cannot be accessed
        """
        file_path = Path(file_path)
        
        try:
            stat = file_path.stat()
            file_hash = calculate_file_hash(file_path)
            
            info = {
                'path': str(file_path),
                'name': file_path.name,
                'size': stat.st_size,
                'hash': file_hash,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'exists': True
            }
            
            self.logger.debug(f"Retrieved file info for {file_path}")
            return info
            
        except (OSError, IOError) as e:
            raise FileOperationError(
                operation="stat",
                path=str(file_path),
                original_error=e
            ) from e
    
    def validate_file_access(self, file_path: Union[str, Path], mode: str = 'r') -> bool:
        """
        Validate that a file can be accessed with the specified mode.
        
        Args:
            file_path: Path to the file
            mode: Access mode ('r' for read, 'w' for write)
            
        Returns:
            True if file can be accessed
            
        Raises:
            FileOperationError: If file cannot be accessed
        """
        file_path = Path(file_path)
        
        try:
            if mode == 'r':
                if not file_path.exists():
                    raise FileOperationError(
                        operation="validation",
                        path=str(file_path),
                        details="File does not exist"
                    )
                if not file_path.is_file():
                    raise FileOperationError(
                        operation="validation",
                        path=str(file_path),
                        details="Path is not a file"
                    )
                if not file_path.stat().st_size > 0:
                    raise FileOperationError(
                        operation="validation",
                        path=str(file_path),
                        details="File is empty"
                    )
            
            elif mode == 'w':
                # Check if parent directory exists or can be created
                if not file_path.parent.exists():
                    try:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                    except (OSError, IOError) as e:
                        raise FileOperationError(
                            operation="validation",
                            path=str(file_path.parent),
                            details="Cannot create parent directory",
                            original_error=e
                        ) from e
            
            self.logger.debug(f"File access validation passed for {file_path} (mode: {mode})")
            return True
            
        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(
                operation="validation",
                path=str(file_path),
                original_error=e,
                context={'mode': mode}
            ) from e
    
    def chunk_file_reader(self, file_path: Union[str, Path], chunk_size: int) -> Iterator[bytes]:
        """
        Read file in chunks as an iterator.
        
        Memory-efficient way to process large files without loading
        everything into memory at once.
        
        Args:
            file_path: Path to file to read
            chunk_size: Size of each chunk in bytes
            
        Yields:
            Binary chunks of the specified size
            
        Raises:
            FileOperationError: If file cannot be read
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
                        
        except (OSError, IOError) as e:
            raise FileOperationError(
                operation="chunked reading",
                path=str(file_path),
                original_error=e,
                context={'chunk_size': chunk_size}
            ) from e