import qrcode
import zxing
import qrtools
from compress import Compressor

def bin_to_qr(data, chunk_size=100, filename_prefix="qr_code", box_size=10, border=4):
    compressed_data = compress_bytes(data)
    hex_data = compressed_data.hex()    
    chunks = [hex_data[i:i+chunk_size] for i in range(0, len(hex_data), chunk_size)]
    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks, 1):
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=box_size, border=border)
        qr.add_data(f"{i}/{total_chunks}:{chunk}")
        qr.make(fit=True)
        print(f"Generating QR code {i}", end="")
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"{filename_prefix}_{i}.png")
        print(f"[OK]")

    print(f"Generated {total_chunks} QR codes.")
    print(f"Each QR code except the last one will contain {chunk_size} bytes of data.")
    print(f"The last QR code will contain the remaining bytes of data ({len(chunks[-1]  )} bytes).")

def qr_to_bin(filename_prefix="qr_code"):
    chunks = {}
    i = 1
    reader = zxing.BarCodeReader()
    fallback_reader = qrtools.QR()

    while True:
        try:
            filename = f"{filename_prefix}_{i}.png"
            print(f"Decoding QR code {i}...", end="")
            barcode = reader.decode(filename)
            print(f"decoded...", end="")
            if barcode and barcode.parsed:
                decoded = barcode.parsed
            else:
                print(f"Could not decode QR code {i}: {barcode.raw} with zxing, trying fallback reader...")
                fallback_reader.decode(filename)
                decoded = fallback_reader.data
            # split the decoded string into chunk_info and chunk_data
            chunk_info, chunk_data = decoded.split(':', 1)
            chunk_num, total_chunks = map(int, chunk_info.split('/'))
            chunks[chunk_num] = chunk_data
            # print(chunk_data)
            print(f"binary data extracted [OK]")
            if chunk_num == total_chunks:
                break
                # print(fallback_reader.data)
            if not chunks[i]:
                print(f"Error decoding QR code {i}: {barcode.raw}")
                exit(-1)
            print(f"binary data extracted [OK]")

            i += 1
        except FileNotFoundError:
            break
        except Exception as e:
            print(f"Error decoding QR code {i}: {e}")
            exit(-1)

    if not chunks:
        print("No QR codes found.")
        return None

    hex_data_compressed = ''.join(chunks[i] for i in range(1, len(chunks) + 1))
    bytes_compressed = bytes.fromhex(hex_data_compressed)
    return decompress_bytes(bytes_compressed)

# Compressing as much as possible

def compress_bytes(data):
    compressor = Compressor()
    compressor.use_gzip()
    return compressor.compress(data)

def decompress_bytes(data):
    compressor = Compressor()
    compressor.use_gzip()
    return compressor.decompress(data)