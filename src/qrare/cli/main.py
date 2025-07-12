"""
Main CLI interface for QRare.

Handles argument parsing, command dispatch, and error reporting
with improved structure and validation.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .commands import encode_command, decode_command, version_command, analyze_command
from ..utils.exceptions import QRareError, ValidationError

# Import version from package root
try:
    from ... import __version__
except ImportError:
    __version__ = "0.2.0"

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """
    Configure logging based on verbosity settings.
    
    Args:
        verbose: Enable debug logging
        quiet: Suppress info logging (only warnings and errors)
    """
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Convert binary files to QR codes and back",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="""
Examples:
  # Encode a PDF file to QR codes
  qrare encode document.pdf -o qrcodes/
  
  # Decode QR codes back to file
  qrare decode qrcodes/ -o recovered/
  
  # Use fast preset for quick encoding
  qrare encode data.bin --preset fast
  
  # Analyze QR codes without decoding
  qrare analyze qrcodes/*.png
        """,
        add_help=True
    )
    
    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-q", "--quiet", 
        action="store_true",
        help="Suppress info messages"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"QRare {__version__}"
    )
    
    # Create subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )
    
    # Encode command
    _create_encode_parser(subparsers)
    
    # Decode command
    _create_decode_parser(subparsers)
    
    # Analyze command
    _create_analyze_parser(subparsers)
    
    # Version command (for compatibility)
    _create_version_parser(subparsers)
    
    return parser


def _create_encode_parser(subparsers) -> None:
    """Create the encode command parser."""
    encode_parser = subparsers.add_parser(
        "encode",
        help="Encode a binary file to QR codes",
        description="Convert a binary file into a series of QR code images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    encode_parser.add_argument(
        "file",
        type=str,
        help="Path to the binary file to encode"
    )
    
    encode_parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="./qrcodes",
        help="Directory to save QR code images"
    )
    
    # Configuration options
    config_group = encode_parser.add_argument_group("Configuration")
    
    config_group.add_argument(
        "-c", "--chunk-size",
        type=int,
        default=1024,
        help="Size of binary chunks in bytes"
    )
    
    config_group.add_argument(
        "--qr-version",
        type=int,
        default=40,
        choices=range(1, 41),
        metavar="1-40",
        help="QR code version (higher = more capacity)"
    )
    
    config_group.add_argument(
        "-z", "--compression-level",
        type=int,
        default=9,
        choices=range(0, 10),
        metavar="0-9",
        help="Zlib compression level (0=none, 9=best)"
    )
    
    # Preset options
    preset_group = encode_parser.add_argument_group("Presets")
    preset_group.add_argument(
        "--preset",
        choices=["fast", "compact", "robust"],
        help="Use preset configuration (overrides other settings)"
    )


def _create_decode_parser(subparsers) -> None:
    """Create the decode command parser."""
    decode_parser = subparsers.add_parser(
        "decode",
        help="Decode QR codes back to a binary file",
        description="Reconstruct the original binary file from QR code images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    decode_parser.add_argument(
        "images",
        type=str,
        nargs="+",
        help="Paths to QR code images, directories, or glob patterns"
    )
    
    decode_parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="./output",
        help="Directory to save the reconstructed file"
    )
    
    decode_parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze QR codes without reconstructing the file"
    )


def _create_analyze_parser(subparsers) -> None:
    """Create the analyze command parser.""" 
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze QR codes without decoding",
        description="Examine QR code images and report their status without reconstructing files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    analyze_parser.add_argument(
        "images",
        type=str,
        nargs="+",
        help="Paths to QR code images, directories, or glob patterns"
    )


def _create_version_parser(subparsers) -> None:
    """Create the version command parser for compatibility."""
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information",
        description="Display version and build information"
    )


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Args:
        args: Optional list of arguments (uses sys.argv if None)
        
    Returns:
        Parsed arguments namespace
    """
    parser = create_parser()
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Validate parsed arguments
    _validate_parsed_args(parsed_args, parser)
    
    return parsed_args


def _validate_parsed_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """
    Validate parsed arguments and show help if needed.
    
    Args:
        args: Parsed arguments
        parser: Argument parser for help display
        
    Raises:
        SystemExit: If validation fails
    """
    # Check if command was provided
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Validate encode-specific arguments
    if args.command == "encode":
        if hasattr(args, 'chunk_size') and args.chunk_size <= 0:
            parser.error("chunk-size must be positive")
        
        # Check for conflicting verbosity options
        if hasattr(args, 'verbose') and hasattr(args, 'quiet') and args.verbose and args.quiet:
            parser.error("--verbose and --quiet are mutually exclusive")


def execute_command(args: argparse.Namespace) -> int:
    """
    Execute the appropriate command based on parsed arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        if args.command == "encode":
            result = encode_command(
                file_path=args.file,
                output_dir=args.output_dir,
                chunk_size=args.chunk_size,
                qr_version=args.qr_version,
                compression_level=args.compression_level,
                preset=getattr(args, 'preset', None)
            )
            logger.info(f"Created {len(result)} QR code images in {args.output_dir}")
            return 0
            
        elif args.command == "decode":
            result = decode_command(
                image_args=args.images,
                output_dir=args.output_dir,
                analyze_only=getattr(args, 'analyze_only', False)
            )
            
            if getattr(args, 'analyze_only', False):
                logger.info("Analysis completed successfully")
                return 0
            elif result:
                logger.info(f"Successfully decoded to {result}")
                return 0
            else:
                logger.error("Decoding failed")
                return 1
                
        elif args.command == "analyze":
            analyze_command(args.images)
            return 0
            
        elif args.command == "version":
            print(version_command())
            return 0
            
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        if e.details:
            logger.error(f"Details: {e.details}")
        return 1
        
    except QRareError as e:
        logger.error(f"Operation failed: {e}")
        if e.details:
            logger.error(f"Details: {e.details}")
        return 1
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI application.
    
    Args:
        args: Optional list of command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        parsed_args = parse_args(args)
        
        # Setup logging
        setup_logging(
            verbose=getattr(parsed_args, 'verbose', False),
            quiet=getattr(parsed_args, 'quiet', False)
        )
        
        # Execute command
        return execute_command(parsed_args)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
        
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())