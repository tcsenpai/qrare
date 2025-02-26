#!/usr/bin/env python3
"""
Example usage of the Binary QR Converter.
"""

import os
import tempfile
from pathlib import Path

from converter import BinaryQRConverter

def main():
    """Run an example of encoding and decoding a binary file."""
    # Create a temporary directory for our example
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create a test binary file
        test_file_path = temp_dir_path / "test_file.bin"
        with open(test_file_path, 'wb') as f:
            f.write(os.urandom(1000000))  # 1MB of random data
        
        print(f"Created test file: {test_file_path}")
        
        # Create output directories
        qr_output_dir = temp_dir_path / "qrcodes"
        decode_output_dir = temp_dir_path / "output"
        
        # Create converter
        converter = BinaryQRConverter(chunk_size=500)
        
        # Encode the test file to QR codes
        print("Encoding file to QR codes...")
        qr_image_paths = converter.encode_file(test_file_path, qr_output_dir)
        
        print(f"Created {len(qr_image_paths)} QR code images:")
        for path in qr_image_paths:
            print(f"  - {path}")
        
        # Decode the QR codes back to a file
        print("\nDecoding QR codes back to file...")
        decoded_file_path = converter.decode_qr_images(qr_image_paths, decode_output_dir)
        
        if decoded_file_path:
            print(f"Successfully decoded to: {decoded_file_path}")
            
            # Verify the decoded file matches the original
            with open(test_file_path, 'rb') as f1, open(decoded_file_path, 'rb') as f2:
                original_data = f1.read()
                decoded_data = f2.read()
                
                if original_data == decoded_data:
                    print("Verification successful: Decoded file matches the original!")
                else:
                    print("Verification failed: Decoded file does not match the original.")
        else:
            print("Decoding failed.")

if __name__ == "__main__":
    main() 