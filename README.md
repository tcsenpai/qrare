# QRare - Binary QR Converter

A powerful and modular Python CLI tool for converting binary files to QR codes and reconstructing them back to the original files. Features compression, error correction, file integrity verification, and a comprehensive modular architecture.

## ✨ Features

- **🔄 Bidirectional Conversion**: Convert any binary file to QR codes and back
- **🗜️ Smart Compression**: Reduce QR code count with configurable zlib compression
- **🛡️ Error Correction**: Built-in QR code error correction for reliable scanning
- **🔒 Integrity Verification**: SHA-256 hash verification ensures data integrity
- **🎛️ Flexible Configuration**: Customizable chunk sizes, QR versions, and compression levels
- **⚡ Preset Modes**: Fast, compact, and robust presets for different use cases
- **🏗️ Modular Architecture**: Clean, maintainable codebase with separate concerns
- **🖥️ Cross-Platform**: Works on Windows, macOS, and Linux
- **📊 Progress Analysis**: Analyze QR codes before decoding for validation

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd qrare
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install ZBar library** (required for QR code reading):
   - **Ubuntu/Debian**: `sudo apt-get install libzbar0`
   - **macOS**: `brew install zbar`
   - **Windows**: Download from [SourceForge](https://sourceforge.net/projects/zbar/)

### Basic Usage

**Encode a file to QR codes**:
```bash
python src/qrare_cli.py encode document.pdf -o qrcodes/
```

**Decode QR codes back to file**:
```bash
python src/qrare_cli.py decode qrcodes/ -o recovered/
```

**Use preset configurations**:
```bash
# Fast encoding (lower compression, larger chunks)
python src/qrare_cli.py encode data.bin --preset fast

# Compact encoding (maximum compression, minimal QR codes)  
python src/qrare_cli.py encode data.bin --preset compact

# Robust encoding (maximum error correction)
python src/qrare_cli.py encode data.bin --preset robust
```

## 📖 Detailed Usage

### Command Line Interface

#### Encode Command
```bash
python src/qrare_cli.py encode FILE [OPTIONS]
```

**Options**:
- `-o, --output-dir DIR`: Directory to save QR code images (default: `./qrcodes`)
- `-c, --chunk-size BYTES`: Size of binary chunks (default: 1024)
- `--qr-version 1-40`: QR code version, higher = more capacity (default: 40)
- `-z, --compression-level 0-9`: Compression level, 0=none, 9=best (default: 9)
- `--preset {fast,compact,robust}`: Use preset configuration

#### Decode Command
```bash
python src/qrare_cli.py decode IMAGES... [OPTIONS]
```

**Options**:
- `-o, --output-dir DIR`: Directory to save reconstructed file (default: `./output`)
- `--analyze-only`: Only analyze QR codes without reconstructing

#### Analyze Command
```bash
python src/qrare_cli.py analyze IMAGES...
```

Examine QR codes and report their status without performing reconstruction.

### Examples

**Encode with custom settings**:
```bash
python src/qrare_cli.py encode large_file.bin \
  --chunk-size 2048 \
  --qr-version 30 \
  --compression-level 6 \
  -o qr_output/
```

**Decode from directory**:
```bash
python src/qrare_cli.py decode qr_output/ -o recovered/
```

**Decode from specific files**:
```bash
python src/qrare_cli.py decode qr_output/*.png -o recovered/
```

**Analyze QR codes first**:
```bash
python src/qrare_cli.py analyze qr_output/
```

## 🏗️ Architecture

The refactored codebase follows a clean, modular architecture:

```
src/qrare/
├── core/                   # Core functionality
│   ├── config.py          # Configuration management
│   ├── converter.py       # Main converter class
│   ├── encoder.py         # QR encoding logic
│   └── decoder.py         # QR decoding logic
├── cli/                   # Command-line interface
│   ├── main.py           # CLI entry point
│   └── commands.py       # Command implementations
└── utils/                 # Utility modules
    ├── exceptions.py      # Custom exception classes
    ├── file_ops.py       # File operations
    └── path_utils.py     # Path handling utilities
```

### Key Components

- **🔧 Config System**: Centralized configuration with validation and presets
- **⚡ Encoder/Decoder**: Separate, focused classes for encoding and decoding
- **🛠️ File Operations**: Robust file handling with comprehensive error management
- **🎯 Exception Handling**: Specific exception types for better error reporting
- **📝 CLI Interface**: Clean argument parsing and command execution

## 💻 Programmatic Usage

### Basic Example

```python
from qrare import BinaryQRConverter

# Create converter
converter = BinaryQRConverter(chunk_size=1024, compression_level=9)

# Encode file
qr_paths = converter.encode_file("document.pdf", "qr_output/")
print(f"Created {len(qr_paths)} QR codes")

# Decode back
reconstructed = converter.decode_qr_images(qr_paths, "recovered/")
print(f"Reconstructed: {reconstructed}")
```

### Advanced Configuration

```python
from qrare import BinaryQRConverter, QRConfig, CompressionLevel, ErrorCorrectionLevel

# Custom configuration
config = QRConfig(
    chunk_size=2048,
    qr_version=30,
    compression_level=CompressionLevel.BALANCED,
    error_correction=ErrorCorrectionLevel.HIGH,
    box_size=8,
    fill_color="darkblue"
)

converter = BinaryQRConverter(config=config)
```

### Preset Configurations

```python
# Optimized for speed
fast_converter = BinaryQRConverter.create_fast_converter()

# Optimized for minimal QR codes
compact_converter = BinaryQRConverter.create_compact_converter()

# Optimized for error recovery  
robust_converter = BinaryQRConverter.create_robust_converter()
```

### Modular Usage

```python
from qrare.core.encoder import QREncoder
from qrare.core.decoder import QRDecoder
from qrare.core.config import QRConfig

# Use encoder and decoder separately
encoder = QREncoder(QRConfig.create_compact_config())
decoder = QRDecoder()

# Encode
qr_paths = encoder.encode_file("data.bin", "qr_codes/")

# Analyze before decoding
analysis = decoder.analyze_qr_images(qr_paths)
print(f"Analysis: {analysis['readable_qrs']} readable QR codes")

# Decode
result = decoder.decode_qr_images(qr_paths, "output/")
```

## 📊 Configuration Options

### Chunk Size
- **Small (512-1024 bytes)**: More QR codes, better error recovery
- **Medium (1024-2048 bytes)**: Balanced approach
- **Large (2048-4096 bytes)**: Fewer QR codes, less error recovery

### QR Code Version
- **1-10**: Small capacity, simple codes
- **11-25**: Medium capacity, good balance
- **26-40**: High capacity, complex codes

### Compression Level
- **0**: No compression (fastest)
- **1-3**: Fast compression
- **4-6**: Balanced compression
- **7-9**: Best compression (slowest)

### Error Correction
- **LOW (~7%)**: Maximum data capacity
- **MEDIUM (~15%)**: Balanced
- **QUARTILE (~25%)**: Good error recovery
- **HIGH (~30%)**: Maximum error recovery

## 🧪 Examples

The `examples/` directory contains comprehensive usage examples:

- **`basic_usage.py`**: Core functionality demonstration
- **`advanced_usage.py`**: Advanced features and error handling

Run examples:
```bash
python examples/basic_usage.py
python examples/advanced_usage.py
```

## 🔍 How It Works

1. **📁 File Reading**: Binary file is read into memory
2. **🗜️ Compression**: Data is compressed using zlib to reduce size
3. **✂️ Chunking**: Compressed data is split into manageable chunks
4. **📝 Metadata**: Each chunk includes index, total count, filename, and hash
5. **🔳 QR Generation**: Each chunk becomes a QR code with embedded metadata
6. **💾 Storage**: QR codes are saved as PNG images with descriptive names

**Reconstruction reverses the process**:
1. **🔍 QR Reading**: QR codes are scanned and decoded
2. **✅ Validation**: Chunks are validated and sorted by index
3. **🔗 Assembly**: Chunks are reassembled into compressed data
4. **📦 Decompression**: Data is decompressed to original format
5. **🔒 Verification**: SHA-256 hash confirms file integrity

## 🎛️ Advanced Features

### Estimation
```bash
# Get encoding estimation before processing
python src/qrare_cli.py encode large_file.bin --analyze-only
```

### Batch Processing
```python
files = ["doc1.pdf", "doc2.bin", "doc3.txt"]
for file_path in files:
    qr_paths = converter.encode_file(file_path, f"qr_{file_path.stem}/")
    print(f"{file_path}: {len(qr_paths)} QR codes")
```

### Error Recovery
```python
# Analyze QR codes for completeness
analysis = converter.analyze_qr_images(qr_paths)
for filename, info in analysis['chunk_info'].items():
    if not info['is_complete']:
        missing = set(range(info['total_chunks'])) - set(info['found_chunks'])
        print(f"File {filename} missing chunks: {sorted(missing)}")
```

## 🛠️ Troubleshooting

### Common Issues

**❌ "Missing ZBar library"**
- Install ZBar using the instructions in the Prerequisites section

**❌ "QR code decoding fails"**
- Ensure QR codes are clear and undamaged
- Try increasing error correction level
- Check that all QR codes are present

**❌ "File too large"**
- Increase chunk size: `--chunk-size 4096`
- Use higher QR version: `--qr-version 40`
- Consider splitting large files

**❌ "Invalid QR version"**
- Use version between 1-40
- Higher versions support more data but need better scanning

### Performance Tips

- **For speed**: Use `--preset fast` or lower compression levels
- **For size**: Use `--preset compact` or higher compression levels  
- **For reliability**: Use `--preset robust` or higher error correction
- **For large files**: Increase chunk size to reduce QR code count

## 🏷️ Version History

### v0.2.0 (Current)
- ✨ Complete modular architecture refactoring
- ✨ New preset configurations (fast/compact/robust)
- ✨ Enhanced error handling and validation
- ✨ Separate encoder/decoder classes
- ✨ Comprehensive configuration system
- ✨ Analysis and estimation features
- ✨ Improved CLI with new commands
- ✨ Extensive documentation and examples
- 🔧 Backward compatibility maintained

### v0.1.0 (Legacy)
- 🎯 Basic encoding/decoding functionality
- 🔧 Simple CLI interface
- 📦 Compression and integrity verification

## 🤝 Contributing

Contributions are welcome! The modular architecture makes it easy to:

- Add new encoding/decoding formats
- Implement additional compression algorithms  
- Create new preset configurations
- Enhance error recovery mechanisms
- Improve CLI functionality

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **ZBar**: QR code reading functionality
- **qrcode**: QR code generation
- **Pillow**: Image processing
- **Original QRare**: Foundation for this enhanced version

---

**QRare v0.2.0** | Modular • Reliable • Extensible