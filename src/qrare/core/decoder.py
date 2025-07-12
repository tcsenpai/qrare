"""
QR code decoding functionality for QRare.

Handles the reconstruction of binary files from QR code images, including
QR code reading, chunk validation, data decompression, and integrity verification.
"""

import base64
import json
import logging
from pathlib import Path
from typing import List, Union, Dict, Any, Optional, Set

from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol

from .config import QRConfig, DEFAULT_CONFIG
from ..utils.exceptions import (
    DecodingError, QRCodeError, ChunkError, IntegrityError, ValidationError
)
from ..utils.file_ops import FileManager, calculate_file_hash
from ..utils.path_utils import validate_directory_path, get_safe_output_path

logger = logging.getLogger(__name__)


class QRDecoder:
    """
    Handles decoding of QR code images back into binary files.
    
    Provides methods to read QR codes, validate chunks, reconstruct data,
    and verify file integrity.
    """
    
    def __init__(self, config: QRConfig = None):
        """
        Initialize QR decoder.
        
        Args:
            config: QR configuration object (uses default if not provided)
        """
        self.config = config or DEFAULT_CONFIG
        self.file_manager = FileManager(compression_level=int(self.config.compression_level))
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def decode_qr_images(
        self,
        image_paths: List[Path],
        output_dir: Union[str, Path]
    ) -> Optional[Path]:
        """
        Decode a series of QR code images back to the original binary file.
        
        Process:
        1. Validate input images and output directory
        2. Read and decode all QR code images
        3. Validate and sort chunks
        4. Reconstruct compressed data
        5. Decompress and save original file
        6. Verify file integrity
        
        Args:
            image_paths: List of paths to QR code images
            output_dir: Directory to save the reconstructed file
            
        Returns:
            Path to the reconstructed file if successful, None if failed
            
        Raises:
            DecodingError: If decoding process fails
            ValidationError: If input parameters are invalid
        """
        # Validate inputs
        output_dir = validate_directory_path(output_dir, create_if_missing=True)
        
        if not image_paths:
            raise ValidationError(
                parameter="image_paths",
                value="[]",
                expected="non-empty list of image paths"
            )
        
        self.logger.info(f"Starting decoding of {len(image_paths)} QR code images")
        
        try:
            # Decode all QR codes
            chunk_data_list = self._decode_all_qr_codes(image_paths)
            
            # Validate and organize chunks
            validated_chunks = self._validate_and_organize_chunks(chunk_data_list)
            
            # Reconstruct file data
            file_data = self._reconstruct_file_data(validated_chunks)
            
            # Save reconstructed file
            output_path = self._save_reconstructed_file(
                file_data, validated_chunks['metadata'], output_dir
            )
            
            # Verify file integrity
            self._verify_file_integrity(output_path, validated_chunks['metadata'])
            
            self.logger.info(f"Successfully decoded to: {output_path}")
            return output_path
            
        except (DecodingError, ValidationError, ChunkError, IntegrityError):
            raise
        except Exception as e:
            raise DecodingError(
                operation="QR image decoding",
                details=f"Unexpected error: {str(e)}"
            ) from e
    
    def _decode_all_qr_codes(self, image_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        Decode all QR code images and extract chunk data.
        
        Args:
            image_paths: List of QR code image paths
            
        Returns:
            List of chunk data dictionaries
            
        Raises:
            DecodingError: If any QR code cannot be decoded
        """
        chunk_data_list = []
        failed_images = []
        
        for image_path in image_paths:
            self.logger.debug(f"Decoding QR code: {image_path}")
            
            try:
                chunk_data = self._decode_single_qr_image(image_path)
                if chunk_data:
                    chunk_data_list.append(chunk_data)
                else:
                    failed_images.append(str(image_path))
                    
            except Exception as e:
                self.logger.error(f"Failed to decode {image_path}: {e}")
                failed_images.append(str(image_path))
        
        if failed_images:
            raise DecodingError(
                operation="QR code reading",
                details=f"Failed to decode {len(failed_images)} images: {', '.join(failed_images)}"
            )
        
        if not chunk_data_list:
            raise DecodingError(
                operation="QR code reading",
                details="No valid QR codes were found in the provided images"
            )
        
        self.logger.info(f"Successfully decoded {len(chunk_data_list)} QR codes")
        return chunk_data_list
    
    def _decode_single_qr_image(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """
        Decode a single QR code image to extract chunk data and metadata.
        
        Args:
            image_path: Path to the QR code image
            
        Returns:
            Dictionary with chunk data and metadata, or None if decoding fails
            
        Raises:
            DecodingError: If QR code cannot be read or parsed
        """
        try:
            # Open and decode the image
            with Image.open(image_path) as img:
                decoded_objects = decode(img, symbols=[ZBarSymbol.QRCODE])
            
            if not decoded_objects:
                raise QRCodeError(
                    operation="reading",
                    qr_info={'image_path': str(image_path)},
                    details="No QR code found in image"
                )
            
            # Get data from the first QR code found
            qr_data = decoded_objects[0].data.decode('utf-8')
            
            # Parse JSON data
            chunk_data = json.loads(qr_data)
            
            # Validate required fields
            self._validate_chunk_metadata(chunk_data, image_path)
            
            return chunk_data
            
        except json.JSONDecodeError as e:
            raise DecodingError(
                operation="JSON parsing",
                image_path=str(image_path),
                details=f"Invalid JSON data in QR code: {str(e)}"
            ) from e
        except Exception as e:
            raise DecodingError(
                operation="QR code reading",
                image_path=str(image_path),
                details=f"Failed to read QR code: {str(e)}"
            ) from e
    
    def _validate_chunk_metadata(self, chunk_data: Dict[str, Any], image_path: Path) -> None:
        """
        Validate that chunk metadata contains required fields.
        
        Args:
            chunk_data: Chunk data dictionary
            image_path: Path to the image (for error reporting)
            
        Raises:
            ChunkError: If metadata is invalid
        """
        required_fields = ['data', 'chunk_index', 'total_chunks', 'filename', 'file_hash']
        
        for field in required_fields:
            if field not in chunk_data:
                raise ChunkError(
                    issue=f"missing required field '{field}'",
                    chunk_info={'image_path': str(image_path)}
                )
        
        # Validate data types
        if not isinstance(chunk_data['chunk_index'], int):
            raise ChunkError(
                issue="chunk_index must be an integer",
                chunk_info={'image_path': str(image_path), 'chunk_index': chunk_data.get('chunk_index')}
            )
        
        if not isinstance(chunk_data['total_chunks'], int):
            raise ChunkError(
                issue="total_chunks must be an integer",
                chunk_info={'image_path': str(image_path), 'total_chunks': chunk_data.get('total_chunks')}
            )
        
        if chunk_data['chunk_index'] < 0 or chunk_data['chunk_index'] >= chunk_data['total_chunks']:
            raise ChunkError(
                issue="chunk_index out of range",
                chunk_info={
                    'image_path': str(image_path),
                    'chunk_index': chunk_data['chunk_index'],
                    'total_chunks': chunk_data['total_chunks']
                }
            )
    
    def _validate_and_organize_chunks(self, chunk_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate chunk consistency and organize them for reconstruction.
        
        Args:
            chunk_data_list: List of chunk data dictionaries
            
        Returns:
            Dictionary with organized chunks and metadata
            
        Raises:
            ChunkError: If chunks are inconsistent or incomplete
        """
        if not chunk_data_list:
            raise ChunkError(
                issue="no chunks provided",
                chunk_info={'chunk_count': 0}
            )
        
        # Get metadata from first chunk
        first_chunk = chunk_data_list[0]
        expected_total = first_chunk['total_chunks']
        expected_filename = first_chunk['filename']
        expected_hash = first_chunk['file_hash']
        
        # Validate we have the expected number of chunks
        if len(chunk_data_list) != expected_total:
            raise ChunkError(
                issue=f"chunk count mismatch: got {len(chunk_data_list)}, expected {expected_total}",
                chunk_info={
                    'received_chunks': len(chunk_data_list),
                    'expected_chunks': expected_total
                }
            )
        
        # Sort chunks by index and validate consistency
        sorted_chunks = sorted(chunk_data_list, key=lambda x: x['chunk_index'])
        validated_chunks = []
        seen_indices: Set[int] = set()
        
        for i, chunk in enumerate(sorted_chunks):
            # Check for duplicates
            if chunk['chunk_index'] in seen_indices:
                raise ChunkError(
                    issue=f"duplicate chunk index {chunk['chunk_index']}",
                    chunk_info={'duplicate_index': chunk['chunk_index']}
                )
            seen_indices.add(chunk['chunk_index'])
            
            # Validate expected index
            if chunk['chunk_index'] != i:
                raise ChunkError(
                    issue=f"missing chunk index {i}",
                    chunk_info={'expected_index': i, 'found_index': chunk['chunk_index']}
                )
            
            # Validate metadata consistency
            if chunk['total_chunks'] != expected_total:
                raise ChunkError(
                    issue=f"inconsistent total_chunks in chunk {i}",
                    chunk_info={
                        'chunk_index': i,
                        'chunk_total': chunk['total_chunks'],
                        'expected_total': expected_total
                    }
                )
            
            if chunk['filename'] != expected_filename:
                raise ChunkError(
                    issue=f"inconsistent filename in chunk {i}",
                    chunk_info={
                        'chunk_index': i,
                        'chunk_filename': chunk['filename'],
                        'expected_filename': expected_filename
                    }
                )
            
            if chunk['file_hash'] != expected_hash:
                raise ChunkError(
                    issue=f"inconsistent file_hash in chunk {i}",
                    chunk_info={
                        'chunk_index': i,
                        'chunk_hash': chunk['file_hash'],
                        'expected_hash': expected_hash
                    }
                )
            
            validated_chunks.append(chunk)
        
        return {
            'chunks': validated_chunks,
            'metadata': {
                'filename': expected_filename,
                'file_hash': expected_hash,
                'total_chunks': expected_total
            }
        }
    
    def _reconstruct_file_data(self, validated_chunks: Dict[str, Any]) -> bytes:
        """
        Reconstruct the original file data from validated chunks.
        
        Args:
            validated_chunks: Dictionary with validated chunks and metadata
            
        Returns:
            Decompressed original file data
            
        Raises:
            DecodingError: If reconstruction fails
        """
        try:
            # Reconstruct compressed data
            compressed_data = b''
            for chunk in validated_chunks['chunks']:
                chunk_bytes = base64.b64decode(chunk['data'])
                compressed_data += chunk_bytes
            
            self.logger.debug(f"Reconstructed {len(compressed_data)} bytes of compressed data")
            
            # Decompress the data
            original_data = self.file_manager.decompress_data(compressed_data)
            
            self.logger.info(
                f"Decompressed {len(compressed_data)} bytes to {len(original_data)} bytes"
            )
            
            return original_data
            
        except Exception as e:
            raise DecodingError(
                operation="data reconstruction",
                details=f"Failed to reconstruct file data: {str(e)}"
            ) from e
    
    def _save_reconstructed_file(
        self,
        file_data: bytes,
        metadata: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """
        Save reconstructed file data to disk.
        
        Args:
            file_data: Original file data
            metadata: File metadata
            output_dir: Directory to save the file
            
        Returns:
            Path to the saved file
            
        Raises:
            DecodingError: If file cannot be saved
        """
        try:
            # Generate safe output path
            output_path = get_safe_output_path(output_dir, metadata['filename'])
            
            # Save file
            self.file_manager.write_file(output_path, file_data)
            
            self.logger.debug(f"Saved reconstructed file: {output_path}")
            return output_path
            
        except Exception as e:
            raise DecodingError(
                operation="file saving",
                details=f"Failed to save reconstructed file: {str(e)}",
                context={
                    'filename': metadata['filename'],
                    'output_dir': str(output_dir),
                    'data_size': len(file_data)
                }
            ) from e
    
    def _verify_file_integrity(self, file_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Verify that the reconstructed file matches the original hash.
        
        Args:
            file_path: Path to the reconstructed file
            metadata: Original file metadata
            
        Raises:
            IntegrityError: If hash verification fails
        """
        try:
            reconstructed_hash = calculate_file_hash(file_path)
            expected_hash = metadata['file_hash']
            
            if reconstructed_hash != expected_hash:
                raise IntegrityError(
                    expected_hash=expected_hash,
                    actual_hash=reconstructed_hash,
                    file_path=str(file_path)
                )
            
            self.logger.info("File integrity verification passed")
            
        except IntegrityError:
            raise
        except Exception as e:
            raise DecodingError(
                operation="integrity verification",
                details=f"Failed to verify file integrity: {str(e)}",
                context={
                    'file_path': str(file_path),
                    'expected_hash': metadata['file_hash']
                }
            ) from e
    
    def analyze_qr_images(self, image_paths: List[Path]) -> Dict[str, Any]:
        """
        Analyze QR code images without full decoding.
        
        Provides information about the QR codes for validation and
        progress reporting without performing the full reconstruction.
        
        Args:
            image_paths: List of QR code image paths
            
        Returns:
            Dictionary with analysis information
            
        Raises:
            DecodingError: If analysis fails
        """
        try:
            analysis = {
                'total_images': len(image_paths),
                'readable_qrs': 0,
                'failed_qrs': 0,
                'unique_files': set(),
                'chunk_info': {},
                'errors': []
            }
            
            for image_path in image_paths:
                try:
                    chunk_data = self._decode_single_qr_image(image_path)
                    if chunk_data:
                        analysis['readable_qrs'] += 1
                        
                        filename = chunk_data['filename']
                        analysis['unique_files'].add(filename)
                        
                        if filename not in analysis['chunk_info']:
                            analysis['chunk_info'][filename] = {
                                'total_chunks': chunk_data['total_chunks'],
                                'found_chunks': [],
                                'file_hash': chunk_data['file_hash']
                            }
                        
                        analysis['chunk_info'][filename]['found_chunks'].append(
                            chunk_data['chunk_index']
                        )
                    else:
                        analysis['failed_qrs'] += 1
                        
                except Exception as e:
                    analysis['failed_qrs'] += 1
                    analysis['errors'].append(f"{image_path}: {str(e)}")
            
            # Convert set to list for JSON serialization
            analysis['unique_files'] = list(analysis['unique_files'])
            
            # Check completeness for each file
            for filename, info in analysis['chunk_info'].items():
                info['found_chunks'].sort()
                info['is_complete'] = (
                    len(info['found_chunks']) == info['total_chunks'] and
                    info['found_chunks'] == list(range(info['total_chunks']))
                )
            
            return analysis
            
        except Exception as e:
            raise DecodingError(
                operation="QR image analysis",
                details=f"Failed to analyze QR images: {str(e)}"
            ) from e