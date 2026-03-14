#!/usr/bin/env python3
"""Setup for label-print CLI tool."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="label-print",
    version="0.1.0",
    author="Dan",
    description="CLI tool to print component labels on Brother PT-P700 label printer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/label-print",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "brother-ql>=0.9.4",
        "qrcode[pil]>=7.3",
        "requests>=2.25.0",
        "click>=8.0.0",
        "Pillow>=8.0.0",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
        "python-dotenv>=0.19.0",
        "boto3>=1.26.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "label-print=label_print.cli:main",
            "label-scan=label_print.scan_cli:main",
            "label-print-yaml=label_print.print_yaml:main",
        ],
    },
)
