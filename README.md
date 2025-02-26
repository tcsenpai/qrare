# Binary QR Converter

A simple CLI tool to convert binary files to QR codes and back.

## Features

- Convert any binary file to a series of QR codes
- Decode QR codes back to the original binary file
- Compression to reduce the number of QR codes needed
- Error correction for reliable decoding
- File integrity verification using SHA-256 hashing
- Cross-platform compatibility (Windows, macOS, Linux)

## Prerequisites

- Python 3.6 or higher
- For decoding QR codes, you need to install the ZBar library:
  - On Ubuntu/Debian: `sudo apt-get install libzbar0`
  - On macOS: `brew install zbar`
  - On Windows: Download from [SourceForge](https://sourceforge.net/projects/zbar/)

## Setup

1. Clone or download this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make the script executable (Linux/macOS):
   ```
   chmod +x binary_qr.py
   ```

## Usage

### Encoding a binary file to QR codes

```
python binary_qr.py encode path/to/file.bin -o output_directory
```

Options:
- `-o, --output-dir`: Directory to save QR code images (default: ./qrcodes)
- `-c, --chunk-size`: Size of binary chunks in bytes (default: 1024)
- `-v, --qr-version`: QR code version (1-40, higher means more capacity) (default: 40)
- `-z, --compression-level`: Zlib compression level (0-9) (default: 9)

### Decoding QR codes back to a binary file

```
python binary_qr.py decode path/to/qrcodes/*.png -o output_directory
```

or

```
python binary_qr.py decode path/to/qrcodes/ -o output_directory
```

Options:
- `-o, --output-dir`: Directory to save the reconstructed file (default: ./output)

### Show version information

```
python binary_qr.py version
```

## Examples

### Encode a PDF file to QR codes

```
python binary_qr.py encode document.pdf -o qrcodes/
```

### Decode QR codes back to the original PDF

```
python binary_qr.py decode qrcodes/ -o recovered/
```

### Run the example script

```
python example.py
```

## How it works

1. The binary file is compressed using zlib to reduce size
2. The compressed data is split into chunks
3. Each chunk is encoded with metadata (chunk index, total chunks, filename, file hash)
4. Each chunk with metadata is converted to a QR code image
5. When decoding, the QR codes are read, and the chunks are reassembled
6. The reassembled data is decompressed to recover the original file
7. The file hash is verified to ensure data integrity

## Tips for optimal use

- **Adjust chunk size**: For larger files, increasing the chunk size (`-c` option) can reduce the number of QR codes but may make them more complex and harder to scan.
- **QR code version**: Higher versions (up to 40) can store more data but require higher resolution scanning.
- **Compression level**: The default level (9) provides maximum compression but takes longer. Lower values (1-8) are faster but produce more QR codes.
- **Printing QR codes**: When printing, ensure high quality and sufficient size for reliable scanning.
- **Scanning**: Use a good camera in well-lit conditions for best results when scanning QR codes.

## Troubleshooting

- **Missing ZBar library**: If you get an error about missing ZBar, install it using the instructions in the Prerequisites section.
- **QR code decoding fails**: Make sure all QR codes are clearly visible and not damaged. Try increasing the error correction level.
- **File too large**: Try increasing the chunk size or QR code version to reduce the number of QR codes.
- **Invalid QR version**: Make sure to use a QR version between 1 and 40.

## License

MIT License 