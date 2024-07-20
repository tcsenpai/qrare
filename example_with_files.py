import qraro

with open("input_test_file.txt", "rb") as f:
    data = f.read()

qraro.bin_to_qr(data, chunk_size=50)

test_file = qraro.qr_to_bin()

with open("output_test_file.txt", "wb") as f:
    f.write(test_file)