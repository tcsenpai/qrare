from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="binary-qr-converter",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Convert binary files to QR codes and back",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/binary-qr-converter",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "qrcode>=7.0",
        "pillow>=8.0.0",
        "pyzbar>=0.1.8",
    ],
    entry_points={
        "console_scripts": [
            "binary-qr=binary_qr_converter.binary_qr:main",
        ],
    },
) 