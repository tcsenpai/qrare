"""
Core functionality for converting binary files to QR codes and back.
"""

import os
import base64
import zlib
import json
import logging
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol

# Configure logging
logger = logging.getLogger(__name__)

class BinaryQRConverter:
    """
    A class to convert binary files to QR codes and back.
    
    This class provides methods to:
    - Encode binary files into a series of QR code images
    - Decode QR code images back into the original binary file
    """
    
    def __init__(
        self,
        chunk_size: int = 1024,
        error_correction: int = ERROR_CORRECT_H,
        qr_version: int = 40,
        compression_level: int = 9
    ):
        """
        Initialize the BinaryQRConverter.
        
        Args:
            chunk_size: Size in bytes of each binary chunk to encode
            error_correction: QR code error correction level
            qr_version: QR code version (1-40, higher means more capacity)
            compression_level: Zlib compression level (0-9)
        """
        self.chunk_size = chunk_size
        self.error_correction = error_correction
        self.qr_version = qr_version
        self.compression_level = compression_level
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal string representation of the hash
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read and update hash in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest()
    
    def _compress_data(self, data: bytes) -> bytes:
        """
        Compress binary data using zlib.
        
        Args:
            data: Binary data to compress
            
        Returns:
            Compressed binary data
        """
        return zlib.compress(data, level=self.compression_level)
    
    def _decompress_data(self, compressed_data: bytes) -> bytes:
        """
        Decompress binary data using zlib.
        
        Args:
            compressed_data: Compressed binary data
            
        Returns:
            Decompressed binary data
        """
        return zlib.decompress(compressed_data)
    
    def _encode_chunk(
        self, 
        chunk: bytes, 
        chunk_index: int, 
        total_chunks: int,
        filename: str,
        file_hash: str
    ) -> str:
        """
        Encode a binary chunk with metadata as a JSON string.
        
        Args:
            chunk: Binary chunk data
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks
            filename: Original filename
            file_hash: Hash of the original file
            
        Returns:
            JSON string with chunk data and metadata
        """
        # Base64 encode the binary chunk
        b64_data = base64.b64encode(chunk).decode('utf-8')
        
        # Create a dictionary with chunk data and metadata
        chunk_dict = {
            'data': b64_data,
            'chunk_index': chunk_index,
            'total_chunks': total_chunks,
            'filename': filename,
            'file_hash': file_hash
        }
        
        # Convert to JSON
        return json.dumps(chunk_dict)
    
    def _create_qr_code(self, data: str) -> Image.Image:
        """
        Create a QR code image from data.
        
        Args:
            data: String data to encode in the QR code
            
        Returns:
            PIL Image object containing the QR code
        """
        qr = qrcode.QRCode(
            version=self.qr_version,
            error_correction=self.error_correction,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        return qr.make_image(fill_color="black", back_color="white")
    
    def encode_file(self, file_path: Path, output_dir: Path) -> List[Path]:
        """
        Encode a binary file into a series of QR code images.
        
        Args:
            file_path: Path to the binary file
            output_dir: Directory to save QR code images
            
        Returns:
            List of paths to the generated QR code images
        """
        file_path = Path(file_path)
        output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate file hash for integrity verification
        file_hash = self._calculate_file_hash(file_path)
        logger.info(f"File hash: {file_hash}")
        
        # Get file size and calculate number of chunks
        file_size = file_path.stat().st_size
        compressed_size = 0
        original_filename = file_path.name
        
        # Read and compress the entire file first to get accurate chunk count
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        compressed_data = self._compress_data(file_data)
        compressed_size = len(compressed_data)
        logger.info(f"Original size: {file_size} bytes, Compressed size: {compressed_size} bytes")
        
        total_chunks = (compressed_size + self.chunk_size - 1) // self.chunk_size
        logger.info(f"Splitting into {total_chunks} chunks")
        
        qr_image_paths = []
        
        for i in range(total_chunks):
            start_pos = i * self.chunk_size
            end_pos = min(start_pos + self.chunk_size, compressed_size)
            chunk = compressed_data[start_pos:end_pos]
            
            # Encode chunk with metadata
            chunk_data = self._encode_chunk(
                chunk, i, total_chunks, original_filename, file_hash
            )
            
            # Create QR code
            qr_img = self._create_qr_code(chunk_data)
            
            # Save QR code image
            image_filename = f"{original_filename}_chunk_{i+1}_of_{total_chunks}.png"
            image_path = output_dir / image_filename
            qr_img.save(image_path)
            qr_image_paths.append(image_path)
            
            logger.info(f"Created QR code {i+1}/{total_chunks}: {image_path}")
        
        return qr_image_paths
    
    def decode_qr_image(self, image_path: Path) -> Optional[Dict]:
        """
        Decode a QR code image to extract chunk data and metadata.
        
        Args:
            image_path: Path to the QR code image
            
        Returns:
            Dictionary with chunk data and metadata, or None if decoding fails
        """
        try:
            # Open the image
            img = Image.open(image_path)
            
            # Decode QR code
            decoded_objects = decode(img, symbols=[ZBarSymbol.QRCODE])
            
            if not decoded_objects:
                logger.error(f"No QR code found in {image_path}")
                return None
            
            # Get the data from the first QR code found
            qr_data = decoded_objects[0].data.decode('utf-8')
            
            # Parse JSON data
            chunk_data = json.loads(qr_data)
            
            return chunk_data
            
        except Exception as e:
            logger.error(f"Error decoding QR code {image_path}: {str(e)}")
            return None
    
    def decode_qr_images(self, image_paths: List[Path], output_dir: Path) -> Optional[Path]:
        """
        Decode a series of QR code images back to the original binary file.
        
        Args:
            image_paths: List of paths to QR code images
            output_dir: Directory to save the reconstructed file
            
        Returns:
            Path to the reconstructed file, or None if decoding fails
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Decode all QR codes
        chunk_data_list = []
        
        for image_path in image_paths:
            chunk_data = self.decode_qr_image(image_path)
            if chunk_data:
                chunk_data_list.append(chunk_data)
            else:
                logger.error(f"Failed to decode {image_path}")
                return None
        
        # Sort chunks by index
        chunk_data_list.sort(key=lambda x: x['chunk_index'])
        
        # Verify we have all chunks
        if not chunk_data_list:
            logger.error("No chunks were successfully decoded")
            return None
        
        # Get metadata from the first chunk
        first_chunk = chunk_data_list[0]
        total_chunks = first_chunk['total_chunks']
        original_filename = first_chunk['filename']
        file_hash = first_chunk['file_hash']
        
        if len(chunk_data_list) != total_chunks:
            logger.error(f"Missing chunks: got {len(chunk_data_list)}, expected {total_chunks}")
            return None
        
        # Verify all chunks have the same metadata
        for i, chunk in enumerate(chunk_data_list):
            if chunk['total_chunks'] != total_chunks:
                logger.error(f"Chunk {i} has inconsistent total_chunks")
                return None
            if chunk['filename'] != original_filename:
                logger.error(f"Chunk {i} has inconsistent filename")
                return None
            if chunk['file_hash'] != file_hash:
                logger.error(f"Chunk {i} has inconsistent file_hash")
                return None
            if chunk['chunk_index'] != i:
                logger.error(f"Expected chunk index {i}, got {chunk['chunk_index']}")
                return None
        
        # Reconstruct the compressed data
        compressed_data = b''
        for chunk in chunk_data_list:
            chunk_bytes = base64.b64decode(chunk['data'])
            compressed_data += chunk_bytes
        
        # Decompress the data
        try:
            original_data = self._decompress_data(compressed_data)
        except zlib.error as e:
            logger.error(f"Decompression failed: {str(e)}")
            return None
        
        # Write the reconstructed file
        output_path = output_dir / original_filename
        with open(output_path, 'wb') as f:
            f.write(original_data)
        
        # Verify file hash
        reconstructed_hash = self._calculate_file_hash(output_path)
        if reconstructed_hash != file_hash:
            logger.error(f"Hash verification failed: expected {file_hash}, got {reconstructed_hash}")
            return None
        
        logger.info(f"Successfully reconstructed {original_filename}")
        return output_path 