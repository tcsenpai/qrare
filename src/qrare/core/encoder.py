"""
QR code encoding functionality for QRare.

Handles the conversion of binary files into QR code images, including
compression, chunking, metadata embedding, and image generation.
"""

import base64
import json
import logging
from pathlib import Path
from typing import List, Union, Dict, Any

import qrcode
from PIL import Image

from .config import QRConfig, DEFAULT_CONFIG
from ..utils.exceptions import EncodingError, QRCodeError, ValidationError
from ..utils.file_ops import FileManager, calculate_file_hash
from ..utils.path_utils import validate_file_path, validate_directory_path, generate_qr_filename

logger = logging.getLogger(__name__)


class QREncoder:
    """
    Handles encoding of binary files into QR code images.
    
    Provides methods to convert files into compressed, chunked QR codes
    with embedded metadata for reliable reconstruction.
    """
    
    def __init__(self, config: QRConfig = None):
        """
        Initialize QR encoder.
        
        Args:
            config: QR configuration object (uses default if not provided)
        """
        self.config = config or DEFAULT_CONFIG
        self.file_manager = FileManager(compression_level=int(self.config.compression_level))
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def encode_file(self, file_path: Union[str, Path], output_dir: Union[str, Path]) -> List[Path]:
        """
        Encode a binary file into a series of QR code images.
        
        Process:
        1. Validate input file and output directory
        2. Read and compress the file
        3. Split compressed data into chunks
        4. Generate QR code for each chunk with metadata
        5. Save QR code images to output directory
        
        Args:
            file_path: Path to the binary file to encode
            output_dir: Directory to save QR code images
            
        Returns:
            List of paths to the generated QR code images
            
        Raises:
            EncodingError: If encoding process fails
            ValidationError: If input parameters are invalid
        """
        # Validate inputs
        file_path = validate_file_path(file_path, must_exist=True)
        output_dir = validate_directory_path(output_dir, create_if_missing=True)
        
        self.logger.info(f"Starting encoding of {file_path}")
        
        try:
            # Get file information
            file_info = self._prepare_file_info(file_path)
            
            # Read and compress file
            compressed_data = self._read_and_compress_file(file_path)
            
            # Calculate chunk information
            chunk_info = self._calculate_chunk_info(compressed_data, file_info)
            
            # Generate QR codes for all chunks
            qr_image_paths = self._generate_qr_codes(
                compressed_data, chunk_info, output_dir
            )
            
            self.logger.info(
                f"Successfully encoded {file_path} into {len(qr_image_paths)} QR codes"
            )
            
            return qr_image_paths
            
        except (EncodingError, ValidationError):
            raise
        except Exception as e:
            raise EncodingError(
                operation="file encoding",
                file_path=str(file_path),
                details=f"Unexpected error: {str(e)}"
            ) from e
    
    def _prepare_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Prepare file information for encoding.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
            
        Raises:
            EncodingError: If file information cannot be gathered
        """
        try:
            file_info = self.file_manager.get_file_info(file_path)
            
            self.logger.debug(
                f"File info - Size: {file_info['size']} bytes, "
                f"Hash: {file_info['hash'][:16]}..."
            )
            
            return file_info
            
        except Exception as e:
            raise EncodingError(
                operation="file information gathering",
                file_path=str(file_path),
                details=f"Cannot access file: {str(e)}"
            ) from e
    
    def _read_and_compress_file(self, file_path: Path) -> bytes:
        """
        Read file and compress its contents.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Compressed file data
            
        Raises:
            EncodingError: If reading or compression fails
        """
        try:
            # Read file content
            file_data = self.file_manager.read_file(file_path)
            original_size = len(file_data)
            
            # Compress data
            compressed_data = self.file_manager.compress_data(file_data)
            compressed_size = len(compressed_data)
            
            compression_ratio = compressed_size / original_size if original_size > 0 else 0
            
            self.logger.info(
                f"Compression: {original_size} → {compressed_size} bytes "
                f"({compression_ratio:.2%})"
            )
            
            return compressed_data
            
        except Exception as e:
            raise EncodingError(
                operation="file reading and compression",
                file_path=str(file_path),
                details=f"Failed to process file: {str(e)}"
            ) from e
    
    def _calculate_chunk_info(self, compressed_data: bytes, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate chunking information.
        
        Args:
            compressed_data: Compressed file data
            file_info: File information dictionary
            
        Returns:
            Dictionary with chunk information
        """
        data_size = len(compressed_data)
        total_chunks = (data_size + self.config.chunk_size - 1) // self.config.chunk_size
        
        chunk_info = {
            'data_size': data_size,
            'total_chunks': total_chunks,
            'chunk_size': self.config.chunk_size,
            'filename': file_info['name'],
            'file_hash': file_info['hash']
        }
        
        self.logger.debug(
            f"Chunk info - Size: {data_size} bytes, "
            f"Chunks: {total_chunks}, Chunk size: {self.config.chunk_size}"
        )
        
        return chunk_info
    
    def _generate_qr_codes(
        self,
        compressed_data: bytes,
        chunk_info: Dict[str, Any],
        output_dir: Path
    ) -> List[Path]:
        """
        Generate QR code images for all chunks.
        
        Args:
            compressed_data: Compressed file data
            chunk_info: Chunk information
            output_dir: Directory to save QR images
            
        Returns:
            List of paths to generated QR code images
            
        Raises:
            EncodingError: If QR code generation fails
        """
        qr_image_paths = []
        total_chunks = chunk_info['total_chunks']
        
        for chunk_index in range(total_chunks):
            try:
                # Extract chunk data
                chunk_data = self._extract_chunk(compressed_data, chunk_index, chunk_info)
                
                # Create chunk metadata
                chunk_metadata = self._create_chunk_metadata(chunk_data, chunk_index, chunk_info)
                
                # Generate QR code
                qr_image = self._create_qr_code(chunk_metadata)
                
                # Save QR code image
                image_path = self._save_qr_image(qr_image, chunk_index, chunk_info, output_dir)
                qr_image_paths.append(image_path)
                
                self.logger.debug(f"Generated QR code {chunk_index + 1}/{total_chunks}")
                
            except Exception as e:
                raise EncodingError(
                    operation=f"QR code generation for chunk {chunk_index + 1}",
                    details=f"Failed to generate chunk: {str(e)}"
                ) from e
        
        return qr_image_paths
    
    def _extract_chunk(self, compressed_data: bytes, chunk_index: int, chunk_info: Dict[str, Any]) -> bytes:
        """
        Extract a specific chunk from compressed data.
        
        Args:
            compressed_data: Complete compressed data
            chunk_index: Index of chunk to extract (0-based)
            chunk_info: Chunk information
            
        Returns:
            Binary chunk data
        """
        chunk_size = chunk_info['chunk_size']
        start_pos = chunk_index * chunk_size
        end_pos = min(start_pos + chunk_size, len(compressed_data))
        
        return compressed_data[start_pos:end_pos]
    
    def _create_chunk_metadata(
        self,
        chunk_data: bytes,
        chunk_index: int,
        chunk_info: Dict[str, Any]
    ) -> str:
        """
        Create JSON metadata for a chunk.
        
        Args:
            chunk_data: Binary chunk data
            chunk_index: Index of this chunk (0-based)
            chunk_info: Chunk information
            
        Returns:
            JSON string with chunk data and metadata
        """
        # Base64 encode the binary chunk
        b64_data = base64.b64encode(chunk_data).decode('utf-8')
        
        # Create metadata dictionary
        metadata = {
            'data': b64_data,
            'chunk_index': chunk_index,
            'total_chunks': chunk_info['total_chunks'],
            'filename': chunk_info['filename'],
            'file_hash': chunk_info['file_hash'],
            'version': '1.0'  # Metadata format version for future compatibility
        }
        
        # Convert to JSON
        return json.dumps(metadata, separators=(',', ':'))  # Compact JSON
    
    def _create_qr_code(self, data: str) -> Image.Image:
        """
        Create a QR code image from data.
        
        Args:
            data: String data to encode in the QR code
            
        Returns:
            PIL Image object containing the QR code
            
        Raises:
            QRCodeError: If QR code creation fails
        """
        try:
            qr = qrcode.QRCode(
                version=self.config.qr_version,
                error_correction=int(self.config.error_correction),
                box_size=self.config.box_size,
                border=self.config.border,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            image = qr.make_image(
                fill_color=self.config.fill_color,
                back_color=self.config.back_color
            )
            
            return image
            
        except Exception as e:
            raise QRCodeError(
                operation="creation",
                qr_info={
                    'version': self.config.qr_version,
                    'error_correction': self.config.error_correction,
                    'data_length': len(data)
                },
                details=f"QR code generation failed: {str(e)}"
            ) from e
    
    def _save_qr_image(
        self,
        qr_image: Image.Image,
        chunk_index: int,
        chunk_info: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """
        Save QR code image to file.
        
        Args:
            qr_image: PIL Image object with QR code
            chunk_index: Index of the chunk (0-based)
            chunk_info: Chunk information
            output_dir: Directory to save the image
            
        Returns:
            Path to the saved image file
            
        Raises:
            EncodingError: If image saving fails
        """
        try:
            # Generate filename
            filename = generate_qr_filename(
                chunk_info['filename'],
                chunk_index,
                chunk_info['total_chunks']
            )
            
            image_path = output_dir / filename
            
            # Save image
            qr_image.save(image_path, format=self.config.image_format)
            
            self.logger.debug(f"Saved QR code: {image_path}")
            return image_path
            
        except Exception as e:
            raise EncodingError(
                operation="QR code image saving",
                details=f"Failed to save image: {str(e)}",
                context={
                    'chunk_index': chunk_index,
                    'output_dir': str(output_dir),
                    'filename': filename if 'filename' in locals() else 'unknown'
                }
            ) from e
    
    def estimate_qr_count(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Estimate the number of QR codes that will be generated for a file.
        
        Useful for providing user feedback before starting the encoding process.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with estimation information
            
        Raises:
            ValidationError: If file is invalid
            EncodingError: If estimation fails
        """
        file_path = validate_file_path(file_path, must_exist=True)
        
        try:
            # Get file size
            file_info = self.file_manager.get_file_info(file_path)
            original_size = file_info['size']
            
            # Estimate compressed size (rough approximation)
            # This is just an estimate; actual compression varies by content
            if int(self.config.compression_level) == 0:
                estimated_compressed_size = original_size
            else:
                # Conservative estimate: assume 70% compression ratio
                estimated_compressed_size = int(original_size * 0.7)
            
            # Calculate estimated chunk count
            estimated_chunks = (
                estimated_compressed_size + self.config.chunk_size - 1
            ) // self.config.chunk_size
            
            return {
                'original_size': original_size,
                'estimated_compressed_size': estimated_compressed_size,
                'estimated_chunks': estimated_chunks,
                'chunk_size': self.config.chunk_size,
                'compression_level': self.config.compression_level
            }
            
        except Exception as e:
            raise EncodingError(
                operation="QR count estimation",
                file_path=str(file_path),
                details=f"Failed to estimate: {str(e)}"
            ) from e