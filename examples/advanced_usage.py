#!/usr/bin/env python3
"""
Advanced usage example for QRare Binary QR Converter.

Demonstrates advanced features including custom configurations,
error recovery, and integration patterns.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the parent src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qrare import BinaryQRConverter, QRConfig, CompressionLevel, ErrorCorrectionLevel
from qrare.core.encoder import QREncoder
from qrare.core.decoder import QRDecoder
from qrare.utils.exceptions import QRareError


def demonstrate_custom_configuration():
    """Demonstrate creating custom configurations."""
    print("=== Custom Configuration Example ===\n")
    
    # Create a custom configuration
    custom_config = QRConfig(
        chunk_size=2048,
        qr_version=30,
        compression_level=CompressionLevel.BALANCED,
        error_correction=ErrorCorrectionLevel.QUARTILE,
        box_size=8,
        border=2,
        fill_color="darkblue",
        back_color="lightgray"
    )
    
    print(f"✓ Created custom configuration:")
    print(f"   Chunk size: {custom_config.chunk_size} bytes")
    print(f"   QR version: {custom_config.qr_version}")
    print(f"   Compression: {custom_config.compression_level.name}")
    print(f"   Error correction: {custom_config.error_correction.name}")
    print(f"   Appearance: {custom_config.fill_color} on {custom_config.back_color}")
    
    # Use the custom configuration
    converter = BinaryQRConverter(config=custom_config)
    print(f"✓ Created converter with custom config")
    print(f"   Configuration summary: {converter.get_configuration_summary()}")


def demonstrate_modular_usage():
    """Demonstrate using encoder and decoder separately."""
    print("\n\n=== Modular Usage Example ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create test file
        test_file = temp_dir_path / "modular_test.txt"
        test_content = b"Modular usage demonstration with separate encoder and decoder classes."
        test_file.write_bytes(test_content)
        
        print(f"✓ Created test file: {test_file} ({len(test_content)} bytes)")
        
        # Create separate encoder and decoder with different configs
        encoder_config = QRConfig.create_compact_config(chunk_size=100)
        decoder_config = QRConfig()  # Default config
        
        encoder = QREncoder(encoder_config)
        decoder = QRDecoder(decoder_config)
        
        print("✓ Created separate encoder and decoder instances")
        
        # Encode using the encoder
        qr_dir = temp_dir_path / "qr_codes"
        qr_paths = encoder.encode_file(test_file, qr_dir)
        print(f"✓ Encoded to {len(qr_paths)} QR codes using encoder")
        
        # Analyze using the decoder
        analysis = decoder.analyze_qr_images(qr_paths)
        print(f"✓ Analysis: {analysis['readable_qrs']} readable QR codes")
        
        # Decode using the decoder
        output_dir = temp_dir_path / "decoded"
        decoded_file = decoder.decode_qr_images(qr_paths, output_dir)
        
        if decoded_file:
            print(f"✓ Decoded to: {decoded_file}")
            
            # Verify content
            if decoded_file.read_bytes() == test_content:
                print("✅ Modular encoding/decoding successful!")
            else:
                print("❌ Content mismatch in modular usage")
        else:
            print("❌ Modular decoding failed")


def demonstrate_error_recovery():
    """Demonstrate error recovery and partial decoding."""
    print("\n\n=== Error Recovery Example ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create test file
        test_file = temp_dir_path / "recovery_test.bin"
        test_content = os.urandom(5000)  # 5KB random data
        test_file.write_bytes(test_content)
        
        print(f"✓ Created test file: {test_file} ({len(test_content)} bytes)")
        
        # Encode with high error correction
        robust_config = QRConfig.create_robust_config(chunk_size=200)
        converter = BinaryQRConverter(config=robust_config)
        
        qr_dir = temp_dir_path / "qr_robust"
        qr_paths = converter.encode_file(test_file, qr_dir)
        print(f"✓ Encoded to {len(qr_paths)} QR codes with high error correction")
        
        # Simulate some QR codes being damaged/missing
        damaged_paths = qr_paths[:-2]  # Remove last 2 QR codes
        print(f"⚠️  Simulating damage: removed {len(qr_paths) - len(damaged_paths)} QR codes")
        
        # Try to analyze damaged set
        try:
            analysis = converter.analyze_qr_images(damaged_paths)
            print(f"📊 Analysis of damaged set:")
            
            for filename, info in analysis['chunk_info'].items():
                missing_count = info['total_chunks'] - len(info['found_chunks'])
                print(f"   File '{filename}': missing {missing_count} chunks")
                print(f"   Status: {'Complete' if info['is_complete'] else 'Incomplete'}")
        
        except QRareError as e:
            print(f"✓ Correctly detected incomplete QR set: {e}")
        
        # Now try with complete set
        print(f"\n🔄 Decoding complete set...")
        output_dir = temp_dir_path / "recovered"
        decoded_file = converter.decode_qr_images(qr_paths, output_dir)
        
        if decoded_file and decoded_file.read_bytes() == test_content:
            print("✅ Recovery example completed successfully!")
        else:
            print("❌ Recovery example failed")


def demonstrate_large_file_handling():
    """Demonstrate handling of larger files."""
    print("\n\n=== Large File Handling Example ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create a larger test file (1MB)
        large_file = temp_dir_path / "large_file.bin"
        chunk_size = 8192  # 8KB chunks for faster generation
        total_chunks = 128  # 1MB total
        
        print(f"📝 Creating large test file ({total_chunks * chunk_size // 1024}KB)...")
        
        with open(large_file, 'wb') as f:
            for i in range(total_chunks):
                # Create recognizable pattern for verification
                chunk_data = f"Chunk {i:04d} ".encode() * (chunk_size // 12)
                chunk_data = chunk_data[:chunk_size]  # Ensure exact size
                f.write(chunk_data)
        
        file_size = large_file.stat().st_size
        print(f"✓ Created large file: {large_file} ({file_size:,} bytes)")
        
        # Use fast preset for large files
        converter = BinaryQRConverter.create_fast_converter(chunk_size=4096)
        
        # Show estimation
        estimation = converter.estimate_qr_count(large_file)
        print(f"📊 Estimation for large file:")
        print(f"   Original size: {estimation['original_size']:,} bytes")
        print(f"   Estimated compressed: {estimation['estimated_compressed_size']:,} bytes")
        print(f"   Estimated QR codes: {estimation['estimated_chunks']:,}")
        
        # For demo purposes, only encode a portion
        print(f"\n⚠️  For demo, limiting to small sample encoding...")
        
        # Create smaller sample
        sample_file = temp_dir_path / "sample.bin"
        sample_file.write_bytes(large_file.read_bytes()[:10000])  # First 10KB
        
        qr_dir = temp_dir_path / "qr_large"
        qr_paths = converter.encode_file(sample_file, qr_dir)
        print(f"✓ Encoded sample to {len(qr_paths)} QR codes")
        
        # Decode sample
        output_dir = temp_dir_path / "decoded_large"
        decoded_file = converter.decode_qr_images(qr_paths, output_dir)
        
        if decoded_file:
            original_sample = sample_file.read_bytes()
            decoded_sample = decoded_file.read_bytes()
            
            if original_sample == decoded_sample:
                print("✅ Large file handling example completed successfully!")
                print(f"   Sample size: {len(original_sample):,} bytes")
            else:
                print("❌ Large file sample verification failed")
        else:
            print("❌ Large file sample decoding failed")


def demonstrate_batch_processing():
    """Demonstrate processing multiple files."""
    print("\n\n=== Batch Processing Example ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create multiple test files
        test_files = []
        file_contents = [
            b"First document content for batch processing test.",
            b"Second document with different content and length for variety.",
            b"Third file: " + os.urandom(1000)  # Binary content
        ]
        
        for i, content in enumerate(file_contents):
            file_path = temp_dir_path / f"batch_file_{i+1}.bin"
            file_path.write_bytes(content)
            test_files.append(file_path)
            print(f"✓ Created {file_path.name} ({len(content)} bytes)")
        
        # Process each file
        converter = BinaryQRConverter.create_compact_converter(chunk_size=200)
        qr_base_dir = temp_dir_path / "batch_qr"
        
        all_qr_paths = {}
        
        print(f"\n🔄 Encoding {len(test_files)} files...")
        for file_path in test_files:
            file_qr_dir = qr_base_dir / file_path.stem
            qr_paths = converter.encode_file(file_path, file_qr_dir)
            all_qr_paths[file_path.name] = qr_paths
            print(f"   {file_path.name}: {len(qr_paths)} QR codes")
        
        # Decode all files
        decode_base_dir = temp_dir_path / "batch_decoded"
        
        print(f"\n🔄 Decoding all files...")
        for filename, qr_paths in all_qr_paths.items():
            decoded_file = converter.decode_qr_images(qr_paths, decode_base_dir)
            
            if decoded_file:
                print(f"   ✓ {filename} → {decoded_file.name}")
            else:
                print(f"   ❌ {filename} failed to decode")
        
        print("✅ Batch processing example completed!")


def main():
    """Main advanced example function."""
    print("QRare Binary QR Converter - Advanced Examples\n")
    
    try:
        demonstrate_custom_configuration()
        demonstrate_modular_usage()
        demonstrate_error_recovery()
        demonstrate_large_file_handling()
        demonstrate_batch_processing()
        
        print("\n🎉 All advanced examples completed successfully!")
        print("\nThese examples demonstrate the flexibility and robustness")
        print("of the QRare Binary QR Converter system.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Advanced examples interrupted by user")
        return 1
        
    except Exception as e:
        print(f"\n❌ Advanced examples failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())