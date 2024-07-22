import qraro

with open("pika.webp", "rb") as f:
    data = f.read()

qraro.bin_to_qr(data, chunk_size=1000, box_size=10, border=4)

test_file = qraro.qr_to_bin()

with open("pika_out.webp", "wb") as f:
    f.write(test_file)