# Installation & Setup Guide

## What Was Built

A complete, production-ready Python CLI tool called `label-print` for the Brother PT-P700 label printer.

**Location:** `/home/node/.openclaw/workspace/label-print/`

## Installation Steps

### 1. Install the package (in editable mode for development):

```bash
cd /home/node/.openclaw/workspace/label-print
pip install -e .
```

Or for standard installation:

```bash
pip install .
```

### 2. Verify installation:

```bash
label-print --help
```

You should see the full CLI documentation.

### 3. Test printer discovery:

```bash
brother_ql discover
```

Look for output like:
```
Found Brother QL-700 (PT-P700) on usb://0x04f9:0x2015/000M6Z401370
```

## Quick Test

Print your first label:

```bash
label-print "C0603X5R1V106M030BC"
```

Or with custom info:

```bash
label-print "C0603X5R1V106M030BC" "100nF Capacitor"
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
│   ├── octopart.py           # Octopart API client
│   ├── part_number.py        # Part validation & distributor detection
│   ├── label_generator.py    # Label image generation (PIL)
│   └── printer.py            # Brother printer interface
│
└── tests/
    └── test_part_number.py   # Unit tests
```

## Key Components

### 1. **cli.py** - Command-line interface
   - Uses Click for argument parsing
   - Orchestrates entire workflow
   - Error handling with user-friendly messages

### 2. **octopart.py** - Part lookup
   - Queries Octopart API (free tier, no key required)
   - Gets part name, datasheet URL, manufacturer info
   - Graceful fallback if API unavailable

### 3. **part_number.py** - Distributor detection
   - Identifies part source: Digi-Key, Mouser, LCSC
   - Validates part number format
   - Regex patterns for each distributor

### 4. **label_generator.py** - Label image creation
   - PIL/Pillow for image generation
   - 24mm tape width optimization (206 pixels at 203 DPI)
   - QR code generation with qrcode library
   - Text wrapping and layout

### 5. **printer.py** - Printer interface
   - Wraps `brother_ql` CLI tool
   - Auto-discovers printers
   - Validates connection
   - Handles print job execution

## Dependencies

All dependencies are pip-installable:

| Package     | Purpose                    | Version  |
|------------|----------------------------|----------|
| brother-ql | Brother printer CLI        | >=0.9.4  |
| qrcode     | QR code generation        | >=7.3    |
| requests   | HTTP requests (Octopart)  | >=2.25.0 |
| click      | CLI framework             | >=8.0.0  |
| Pillow     | Image processing          | >=8.0.0  |

## Usage Examples

### Basic:
```bash
label-print "296-32654-ND"
```

### With custom text:
```bash
label-print "C0603X5R1V106M030BC" "100nF Capacitor"
```

### Dry run (no print):
```bash
label-print "296-32654-ND" --dry-run
```

### Save label image:
```bash
label-print "296-32654-ND" --save-image /tmp/label.png
```

### Specify printer manually:
```bash
label-print "296-32654-ND" --printer-id "usb://0x04f9:0x2015/000M6Z401370"
```

### With Octopart API key:
```bash
label-print "296-32654-ND" --api-key "YOUR_KEY_HERE"
```

### Verbose output:
```bash
label-print "296-32654-ND" -v
```

## Environment Variables

For convenience, set these in your shell profile:

```bash
# Printer auto-detection (optional)
export BROTHER_QL_PRINTER="usb://0x04f9:0x2015/000M6Z401370"
export BROTHER_QL_MODEL="PT-P700"

# Octopart API key (optional, free tier works without it)
export OCTOPART_API_KEY="your_api_key"
```

## Troubleshooting

### "No printers found"
```bash
# Check if printer is connected
brother_ql discover

# If not listed, try with explicit identifier
label-print "296-32654-ND" --printer-id "usb://0x04f9:0x2015/000M6Z401370"
```

### "brother_ql command not found"
```bash
pip install brother-ql
```

### "Part not found on Octopart"
Tool gracefully falls back to using the part number as the label name. This is normal for obscure or new parts.

### "QR code generation failed"
Label will print without QR code. This is handled gracefully.

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
