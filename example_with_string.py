import qrare

# Example usage
original_data = b"This is a binary string \x00\x01\x02 with some non-printable characters."
qrare.bin_to_qr(original_data, chunk_size=50)

decoded_data = qrare.qr_to_bin()
print("Decoded data:", decoded_data)
print("Original and decoded data match:", original_data == decoded_data)