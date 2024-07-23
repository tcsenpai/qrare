import qrare

with open("pika.webp", "rb") as f:
    data = f.read()

qrare.bin_to_qr(data, chunk_size=1000, box_size=10, border=4)

test_file = qrare.qr_to_bin()

with open("pika_out.webp", "wb") as f:
    f.write(test_file)