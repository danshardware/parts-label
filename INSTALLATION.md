# Installation & Setup Guide

## What Was Built

A complete, production-ready Python CLI tool called `label-print` for the Brother PT-P700 label printer.

## Installation Steps

### 1. Install system dependencies

**ptouch-print** (required for PT-P700 printing):
```bash
git clone https://git.familie-radermacher.ch/linux/ptouch-print.git
cd ptouch-print
mkdir build && cd build
cmake ..
make
sudo make install
```

**brother_ql** (for printer discovery):
```bash
pip install brother-ql
```

### 2. Install the label-print package

```bash
cd /path/to/label-print
pip install -e .
```

Or for standard installation:
```bash
pip install .
```

### 3. Setup USB permissions (Linux)

Create `/etc/udev/rules.d/99-brother-printer.rules`:
```
SUBSYSTEM=="usb", ATTRS{idVendor}=="04f9", MODE="0666"
```

Reload udev rules:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Reconnect the printer.

### 4. Verify installation

```bash
label-print --help
```

### 5. Test printer detection

```bash
ptouch-print --info
```

Look for output like:
```
PT-P700 found on USB bus 3, device 58
printer has 180 dpi, maximum printing width is 128 px
maximum printing width for this tape is 76px
```

## Quick Test

Print your first label:

```bash
label-print "C48974" "1A 30V Schottky"
```

Or with Mouser part:

```bash
label-print "821-MBS10" ".8A 1kV bridge"
```

## Project Structure

```
label-print/
├── setup.py                    # Package installer
├── LICENSE                     # MIT License
├── README.md                   # Full documentation
├── QUICKSTART.md              # Quick start guide
├── INSTALLATION.md            # This file
├── ARCHITECTURE.md            # Technical design
├── examples.sh                # Usage examples
│
├── label_print/               # Main package
│   ├── __init__.py           # Package exports
│   ├── cli.py                # Click CLI interface ⭐ Entry point
│   ├── part_lookup.py        # LCSC/Mouser part lookup
│   ├── part_number.py        # Part validation & distributor detection
│   ├── label_generator.py    # Label image generation (PIL)
│   └── printer.py            # Brother PT-P700 interface (ptouch-print)
│
└── tests/
    └── test_part_number.py   # Unit tests
```

## Key Components

### 1. **cli.py** - Command-line interface
   - Uses Click for argument parsing
   - Orchestrates entire workflow
   - Error handling with user-friendly messages
   - Supports `--url` option to bypass automatic lookup

### 2. **part_lookup.py** - Part information lookup
   - **LCSC**: Web scraping for part name and datasheet
   - **Mouser**: REST API with fallback to ProductDetailUrl
   - **Digi-Key**: No API (requires OAuth), uses part number as-is
   - Graceful fallback if lookup fails

### 3. **part_number.py** - Distributor detection
   - Identifies part source: Digi-Key, Mouser, LCSC
   - Validates part number format
   - Regex patterns for each distributor

### 4. **label_generator.py** - Label image creation
   - PIL/Pillow for 1-bit B&W image generation
   - 12mm tape: 76px width at 180 DPI (PT-P700 spec)
   - Landscape orientation: 150x76 pixels
   - Dynamic font sizing (10-20pt) to maximize readability
   - QR code generation with qrcode library (60px)
   - Text wrapping and layout

### 5. **printer.py** - Printer interface
   - Uses `ptouch-print` for PT-series printers
   - Uses `brother_ql` for printer discovery only
   - Auto-discovers printers
   - Validates connection
   - Handles print job execution

## Dependencies

### System Dependencies
| Package        | Purpose                           | Installation |
|----------------|-----------------------------------|--------------|
| ptouch-print   | PT-series printer driver          | Build from source (see above) |
| brother-ql     | Printer discovery (pyusb backend) | `pip install brother-ql` |

### Python Dependencies (pip-installable)
| Package        | Purpose                    | Version  |
|----------------|----------------------------|----------|
| qrcode[pil]    | QR code generation         | >=7.3    |
| requests       | HTTP requests (Mouser API) | >=2.25.0 |
| click          | CLI framework              | >=8.0.0  |
| Pillow         | Image processing           | >=8.0.0  |
| beautifulsoup4 | HTML parsing (LCSC)        | >=4.9.0  |
| lxml           | XML/HTML parser            | >=4.6.0  |
| python-dotenv  | Environment variables      | >=0.19.0 |

## Usage Examples

### LCSC part (automatic lookup):
```bash
label-print "C48974" "1A 30V Schottky"
```

### Mouser part (automatic lookup):
```bash
label-print "821-MBS10" ".8A 1kV bridge"
```

### Custom part with URL:
```bash
label-print "MY-PART" "Custom component" --url "https://example.com/datasheet"
```

### Dry run (no print):
```bash
label-print "C48974" --dry-run
```

### Save label image:
```bash
label-print "C48974" "1A 30V Schottky" --save-image /tmp/label.png
```

### With Mouser API key:
```bash
label-print "821-MBS10" ".8A 1kV bridge" --mouser-key "YOUR_KEY_HERE"
```

### Verbose output:
```bash
label-print "C48974" -v
```

## Environment Variables

Create a `.env` file in the project directory or set in your shell:

```bash
# Mouser API key (optional, for better part lookups)
MOUSER_API_KEY="your_mouser_api_key"

# Printer settings (optional, for manual override)
BROTHER_QL_PRINTER="usb://0x04f9:0x2061"
BROTHER_QL_MODEL="QL-700"  # Use QL-700 for PT-P700 compatibility
```

## Troubleshooting

### "ptouch-print command not found"
```bash
# Install ptouch-print from source (see Installation Steps above)
which ptouch-print  # Should return /usr/local/bin/ptouch-print
```

### "PT-P700 found" but red flashing light
- Check that image dimensions are correct (150x76 for 12mm tape)
- Ensure you're using 1-bit B&W images, not RGB
- Verify tape is loaded correctly

### "No printers found" during discovery
```bash
# Check USB connection
brother_ql -b pyusb discover

# Check ptouch-print can see it
ptouch-print --info
```

### USB permission denied (Linux)
```bash
# Add udev rule (see Installation Steps above)
sudo nano /etc/udev/rules.d/99-brother-printer.rules
# Add: SUBSYSTEM=="usb", ATTRS{idVendor}=="04f9", MODE="0666"
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### "Part not found" or "No datasheet found"
- LCSC: Part page must exist at `https://www.lcsc.com/product-detail/{part}.html`
- Mouser: Falls back to product page if no datasheet URL
- Digi-Key: Not supported (requires OAuth), use `--url` option
- Use `--url` to provide custom URLs for any part

### Blank labels printing
- Verify ptouch-print is installed (not using brother_ql for printing)
- Check image is 1-bit mode, not RGB
- Use `--save-image` to inspect generated image

## Running Tests

```bash
cd /home/node/.openclaw/workspace/label-print
python tests/test_part_number.py
```

Expected output:
```
✅ All tests passed!
```

## Development

The code is organized for easy extension:

- **Add new distributors:** Edit `part_number.py` with new regex patterns
- **Change label layout:** Modify `label_generator.py` 
- **Add barcode support:** Create `label_print/barcode.py`, import in `cli.py`
- **Support new printers:** Extend `printer.py` with additional models

All modules are designed to be independently testable.

## What's Next?

1. **For production use:** Run `pip install .` instead of `-e`
2. **For development:** Keep using `pip install -e .` for live editing
3. **For batch printing:** Extend `cli.py` to accept multiple part numbers
4. **For web interface:** Wrap CLI functions and add Flask/FastAPI layer

## License

MIT License - See LICENSE file

---

**Created:** 2024-03-12
**Version:** 0.1.0
**Status:** Production-ready but pragmatic (intentionally simple, no over-engineering)
