#!/usr/bin/env python3
"""
QRare CLI Entry Point

Provides backward compatibility with the original binary_qr.py interface
while using the new modular architecture.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path to allow imports
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from qrare.cli.main import main

if __name__ == "__main__":
    sys.exit(main())