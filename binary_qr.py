#!/usr/bin/env python3
"""
Binary QR Converter - A utility to convert binary files to QR codes and back.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from converter import BinaryQRConverter

__version__ = '0.1.0'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert binary files to QR codes and back",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Encode command
    encode_parser = subparsers.add_parser("encode", help="Encode a binary file to QR codes")
    encode_parser.add_argument("file", type=str, help="Path to the binary file to encode")
    encode_parser.add_argument(
        "-o", "--output-dir", 
        type=str, 
        default="./qrcodes",
        help="Directory to save QR code images"
    )
    encode_parser.add_argument(
        "-c", "--chunk-size", 
        type=int, 
        default=1024,
        help="Size of binary chunks in bytes"
    )
    encode_parser.add_argument(
        "-v", "--qr-version", 
        type=int, 
        default=40,
        choices=range(1, 41),
        help="QR code version (1-40, higher means more capacity)"
    )
    encode_parser.add_argument(
        "-z", "--compression-level", 
        type=int, 
        default=9,
        help="Zlib compression level (0-9)"
    )
    
    # Decode command
    decode_parser = subparsers.add_parser("decode", help="Decode QR codes back to a binary file")
    decode_parser.add_argument(
        "images", 
        type=str, 
        nargs="+", 
        help="Paths to QR code images or directory containing QR code images"
    )
    decode_parser.add_argument(
        "-o", "--output-dir", 
        type=str, 
        default="./output",
        help="Directory to save the reconstructed file"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    return parser.parse_args()

def get_image_paths(image_args: List[str]) -> List[Path]:
    """
    Get a list of image paths from command line arguments.
    
    Args:
        image_args: List of image paths or directories from command line
        
    Returns:
        List of image file paths
    """
    image_paths = []
    
    for path_str in image_args:
        path = Path(path_str)
        
        if path.is_dir():
            # If path is a directory, find all PNG files in it
            image_paths.extend(sorted(path.glob("*.png")))
        elif path.is_file():
            # If path is a file, add it directly
            image_paths.append(path)
        else:
            # If path is a glob pattern, expand it
            expanded_paths = list(Path().glob(path_str))
            if expanded_paths:
                image_paths.extend(expanded_paths)
    
    return image_paths

def main():
    """Main entry point for the command-line interface."""
    args = parse_args()
    
    if args.command == "version":
        print(f"Binary QR Converter version {__version__}")
        return 0
    
    if args.command == "encode":
        file_path = Path(args.file)
        output_dir = Path(args.output_dir)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return 1
        
        converter = BinaryQRConverter(
            chunk_size=args.chunk_size,
            qr_version=args.qr_version,
            compression_level=args.compression_level
        )
        
        try:
            qr_image_paths = converter.encode_file(file_path, output_dir)
            logger.info(f"Created {len(qr_image_paths)} QR code images in {output_dir}")
            return 0
        except Exception as e:
            logger.error(f"Encoding failed: {str(e)}")
            return 1
    
    elif args.command == "decode":
        image_paths = get_image_paths(args.images)
        output_dir = Path(args.output_dir)
        
        if not image_paths:
            logger.error("No image files found")
            return 1
        
        logger.info(f"Found {len(image_paths)} image files")
        
        converter = BinaryQRConverter()
        
        try:
            output_path = converter.decode_qr_images(image_paths, output_dir)
            if output_path:
                logger.info(f"Successfully decoded to {output_path}")
                return 0
            else:
                logger.error("Decoding failed")
                return 1
        except Exception as e:
            logger.error(f"Decoding failed: {str(e)}")
            return 1
    
    else:
        logger.error("No command specified. Use --help for usage information.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 