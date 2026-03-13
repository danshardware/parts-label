# label-print

A CLI tool to print component labels on a Brother PT-P700 label printer with 12mm tape.

## Features

- **Automatic part lookup**: LCSC (web scraping) and Mouser (API)
- **QR code generation**: Links to datasheets or custom URLs
- **Dynamic font sizing**: Maximizes readability (10-20pt auto-scaling)
- **Custom URL support**: Use `--url` to skip automatic lookup
- **12mm tape optimized**: 76px width at 180 DPI (PT-P700 spec)
- **Professional labels**: Part name, description, and scannable QR code

## Installation

### Prerequisites

1. **ptouch-print** (PT-series printer driver):
```bash
git clone https://git.familie-radermacher.ch/linux/ptouch-print.git
cd ptouch-print
mkdir build && cd build
cmake ..
make
sudo make install
```

2. **Python package**:
```bash
git clone <repo>
cd label-print
pip install -e .
```

See [INSTALLATION.md](INSTALLATION.md) for detailed setup including USB permissions.

## Usage

### LCSC parts (automatic lookup):
```bash
label-print "C48974" "1A 30V Schottky"
```

### Mouser parts (automatic lookup):
```bash
label-print "821-MBS10" ".8A 1kV bridge"
```

### Custom parts with URL:
```bash
label-print "MY-PART" "Description" --url "https://example.com/datasheet.pdf"
```

### Other options:
```bash
label-print "C48974" --dry-run              # Test without printing
label-print "C48974" --save-image label.png  # Save image
label-print "C48974" -v                     # Verbose output
```

### Supported Part Number Formats

- **LCSC**: `C` followed by 5-12 digits (e.g., `C48974`, `C0603X5R1V106M030BC`)
- **Mouser**: Vendor ID + part number (e.g., `821-MBS10`)
- **Digi-Key**: Ends with `-ND` (e.g., `296-32654-ND`) - *Note: No API support, use `--url` for datasheets*

## Requirements

- **Brother PT-P700** label printer with 12mm tape
- **ptouch-print** utility installed (see Installation)
- **Python 3.7+**
- USB permissions configured (Linux)

## Environment Variables

Create a `.env` file or export:

```bash
MOUSER_API_KEY="your_api_key_here"  # Optional, for Mouser lookups
```

## How It Works

1. **Detects** distributor from part number pattern
2. **Looks up** part information:
   - **LCSC**: Scrapes product page for name and datasheet
   - **Mouser**: Queries API, falls back to product page URL
   - **Digi-Key**: Uses part number as-is (no API)
3. **Generates** a 1-bit B&W label image (150x76px landscape):
   - Part name with dynamic font sizing (10-20pt)
   - Info line (12pt)
   - QR code (60px, centered vertically)
4. **Prints** via ptouch-print utility

### Error Handling

- Graceful fallback if lookup fails (uses part number as name)
- No QR code if URL unavailable (more space for text)
- Validates printer connection before printing
- Clear error messages with suggested fixes

## Example Output

```
┌─────────────────────────────────────────────────┐
│ LMBR130T1G              ▄▄▄▄▄▄▄▄▄▄▄▄          │
│                         ▄█░░░░░░░░░█▄          │
│ 1A 30V Schottky        ▄█░█▄▄▄▄▄█░█▄          │
│                         ▄█░█░░░░░█░█▄          │
│                         ▄█░█░███░█░█▄          │
│                         ▄█░█░░░░░█░█▄          │
│                         ▄█░█▄▄▄▄▄█░█▄          │
│                         ▄█░░░░░░░░░█▄          │
│                         ▄▄▄▄▄▄▄▄▄▄▄▄          │
└─────────────────────────────────────────────────┘
       12mm tape (landscape orientation)
```

Actual label is 150×76 pixels at 180 DPI on 12mm tape.

## License

MIT
