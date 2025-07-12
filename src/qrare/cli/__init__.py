"""
Command-line interface for QRare.

Provides argument parsing, validation, and execution of conversion operations
through a clean CLI interface.
"""

from .main import main, parse_args
from .commands import encode_command, decode_command, version_command

__all__ = ["main", "parse_args", "encode_command", "decode_command", "version_command"]