#!/usr/bin/env python3
"""
Basic usage example for QRare Binary QR Converter.

Demonstrates the core functionality of encoding a binary file to QR codes
and decoding them back to the original file.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the parent src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qrare import BinaryQRConverter


def demonstrate_basic_conversion():
    """Demonstrate basic file encoding and decoding."""
    print("=== QRare Basic Usage Example ===\n")
    
    # Create a temporary directory for our example
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        print(f"Working in temporary directory: {temp_dir_path}")
        
        # Create a test binary file with some recognizable content
        test_file_path = temp_dir_path / "test_document.bin"
        test_content = b"This is a test binary file for QRare demonstration. " * 100
        
        with open(test_file_path, 'wb') as f:
            f.write(test_content)
        
        print(f"✓ Created test file: {test_file_path} ({len(test_content)} bytes)")
        
        # Create output directories
        qr_output_dir = temp_dir_path / "qrcodes"
        decode_output_dir = temp_dir_path / "recovered"
        
        # Initialize converter with moderate settings
        converter = BinaryQRConverter(chunk_size=500, compression_level=6)
        print(f"✓ Initialized converter: {converter}")
        
        # Show estimation
        estimation = converter.estimate_qr_count(test_file_path)
        print(f"\n📊 Encoding estimation:")
        print(f"   Original size: {estimation['original_size']} bytes")
        print(f"   Estimated compressed: {estimation['estimated_compressed_size']} bytes")
        print(f"   Estimated QR codes: {estimation['estimated_chunks']}")
        
        # Encode the test file to QR codes
        print(f"\n🔄 Encoding file to QR codes...")
        qr_image_paths = converter.encode_file(test_file_path, qr_output_dir)
        
        print(f"✓ Created {len(qr_image_paths)} QR code images:")
        for i, path in enumerate(qr_image_paths[:3]):  # Show first 3
            print(f"   {i+1}. {path.name}")
        if len(qr_image_paths) > 3:
            print(f"   ... and {len(qr_image_paths) - 3} more")
        
        # Analyze the QR codes
        print(f"\n🔍 Analyzing QR codes...")
        analysis = converter.analyze_qr_images(qr_image_paths)
        print(f"   Readable QR codes: {analysis['readable_qrs']}/{analysis['total_images']}")
        print(f"   Unique files detected: {len(analysis['unique_files'])}")
        
        for filename, info in analysis['chunk_info'].items():
            status = "Complete" if info['is_complete'] else "Incomplete"
            print(f"   File '{filename}': {len(info['found_chunks'])}/{info['total_chunks']} chunks - {status}")
        
        # Decode the QR codes back to a file
        print(f"\n🔄 Decoding QR codes back to file...")
        decoded_file_path = converter.decode_qr_images(qr_image_paths, decode_output_dir)
        
        if decoded_file_path:
            print(f"✓ Successfully decoded to: {decoded_file_path}")
            
            # Verify the decoded file matches the original
            with open(test_file_path, 'rb') as f1, open(decoded_file_path, 'rb') as f2:
                original_data = f1.read()
                decoded_data = f2.read()
                
                if original_data == decoded_data:
                    print("✅ Verification successful: Decoded file matches the original!")
                    print(f"   Both files are {len(original_data)} bytes")
                else:
                    print("❌ Verification failed: Decoded file does not match the original.")
                    print(f"   Original: {len(original_data)} bytes, Decoded: {len(decoded_data)} bytes")
        else:
            print("❌ Decoding failed.")


def demonstrate_preset_configurations():
    """Demonstrate different preset configurations."""
    print("\n\n=== Preset Configuration Examples ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create a larger test file
        test_file_path = temp_dir_path / "large_test.bin"
        test_content = os.urandom(50000)  # 50KB of random data
        
        with open(test_file_path, 'wb') as f:
            f.write(test_content)
        
        print(f"Created test file: {test_file_path} ({len(test_content)} bytes)")
        
        # Test different presets
        presets = {
            'fast': BinaryQRConverter.create_fast_converter(),
            'compact': BinaryQRConverter.create_compact_converter(), 
            'robust': BinaryQRConverter.create_robust_converter()
        }
        
        print("\n📊 Preset comparison:")
        for preset_name, converter in presets.items():
            estimation = converter.estimate_qr_count(test_file_path)
            config = converter.get_configuration_summary()
            
            print(f"\n   {preset_name.upper()} preset:")
            print(f"     Chunk size: {config['chunk_size']} bytes")
            print(f"     Compression level: {config['compression_level']}")
            print(f"     QR version: {config['qr_version']}")
            print(f"     Estimated QR codes: {estimation['estimated_chunks']}")


def demonstrate_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n\n=== Error Handling Examples ===\n")
    
    from qrare.utils.exceptions import ValidationError, FileOperationError
    
    # Test file not found
    try:
        converter = BinaryQRConverter()
        converter.encode_file("nonexistent_file.bin", "output")
    except (ValidationError, FileOperationError) as e:
        print(f"✓ Correctly caught file not found error: {e}")
    
    # Test invalid configuration
    try:
        from qrare.core.config import QRConfig
        invalid_config = QRConfig(chunk_size=-1)  # Invalid chunk size
    except ValueError as e:
        print(f"✓ Correctly caught invalid configuration: {e}")
    
    print("✓ Error handling is working correctly")


def main():
    """Main example function."""
    print("QRare Binary QR Converter - Examples\n")
    
    try:
        # Run demonstrations
        demonstrate_basic_conversion()
        demonstrate_preset_configurations()
        demonstrate_error_handling()
        
        print("\n🎉 All examples completed successfully!")
        print("\nFor more advanced usage, see the other example files in this directory.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Example interrupted by user")
        return 1
        
    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())