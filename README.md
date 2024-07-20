# QR Code Encoder and Decoder

This Python module provides functionality to encode arbitrary binary data into a series of QR codes and decode them back into the original data. It uses the `qrcode` library for encoding and the `zxing` library for decoding.

## Dependencies

- Python 3.x
- qrcode
- Pillow (PIL)
- zxing

Install the required libraries using pip:

`pip install qrcode pillow zxing`

Or install the dependencies using:

`pip install -r requirements.txt`

## Functions

### bin_to_qr(data, chunk_size=100, filename_prefix="qr_code")

Encodes binary data into a series of QR code images.

Parameters:
- `data` (bytes): The binary data to encode.
- `chunk_size` (int, optional): The maximum number of hexadecimal characters per QR code. Default is 100.
- `filename_prefix` (str, optional): The prefix for the generated QR code image filenames. Default is "qr_code".

This function performs the following steps:
1. Converts the binary data to a hexadecimal string.
2. Splits the hex string into chunks of the specified size.
3. Creates a QR code for each chunk, including chunk number and total chunk count.
4. Saves each QR code as a PNG image.

### qr_to_bin(filename_prefix="qr_code")

Decodes a series of QR code images back into the original binary data.

Parameters:
- `filename_prefix` (str, optional): The prefix of the QR code image filenames to decode. Default is "qr_code".

Returns:
- `bytes`: The decoded binary data, or `None` if no QR codes were found.

This function performs the following steps:
1. Iterates through numbered QR code images with the given prefix.
2. Decodes each QR code using the zxing library.
3. Extracts chunk information and data from each decoded QR code.
4. Reconstructs the original hexadecimal string from the chunks.
5. Converts the hexadecimal string back to binary data.

## Usage Example

```python

# Encode binary data into QR codes
import qraro

original_data = b"This is a binary string \x00\x01\x02 with some non-printable characters.
qraro.bin_to_qr(original_data, chunk_size=50)

# Decode QR codes back into binary data
import qraro

decoded_data = qraro.qr_to_bin()
print("Decoded data:", decoded_data)
print("Original and decoded data match:", original_data == decoded_data)

```

## Notes

- The script automatically determines the appropriate QR code version based on the data size.
- Error correction level is set to LOW (L) to maximize data capacity.
- The script handles binary data, including non-printable characters.
- QR code images are saved and read from the current working directory.
- Ensure you have write permissions in the directory where the script is run.

## Error Handling

- The script includes basic error handling for file not found and decoding errors.
- If an error occurs during decoding, it will be printed to the console.

## Limitations

- The maximum data capacity depends on the QR code version and error correction level.
- Very large binary files may require a large number of QR codes.
- The script assumes that QR codes will be scanned in the correct order for decoding.