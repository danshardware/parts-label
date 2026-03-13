# Quick Start Guide

## Installation

### From source:
```bash
git clone <repo>
cd label-print
pip install -e .
```

### Requirements:
- Python 3.7+
- Brother PT-P700 label printer (USB or network)
- 24mm label tape installed

## First Steps

### 1. Check your printer is detected:
```bash
brother_ql discover
```

You should see output like:
```
usb://0x04f9:0x2015/000M6Z401370
```

### 2. Test a simple label:
```bash
label-print "296-32654-ND"
```

This will:
- Validate the part number
- Query Octopart for the real part name
- Generate a label image with QR code
- Print it to your Brother printer

### 3. Add custom info:
```bash
label-print "296-32654-ND" "100nF Capacitor"
```

## Supported Part Numbers

### Digi-Key:
```bash
label-print "296-32654-ND"
label-print "12345-ND"
```

### LCSC (JLC):
```bash
label-print "C0603X5R1V106M030BC"
label-print "C123456"
```

### Mouser:
```bash
label-print "571-LM358N"
```

## Troubleshooting

### Printer not found:
```bash
# Check connection
brother_ql discover

# If still not found, specify manually:
label-print "296-32654-ND" --printer-id "usb://0x04f9:0x2015/000M6Z401370"

# Or set environment variable:
export BROTHER_QL_PRINTER="usb://0x04f9:0x2015/000M6Z401370"
label-print "296-32654-ND"
```

### Part not found on Octopart:
Falls back gracefully to using the part number as the label name.

### Testing without printing:
```bash
label-print "296-32654-ND" --dry-run
label-print "296-32654-ND" --dry-run --save-image /tmp/label.png
```

## Useful Commands

```bash
# Get printer status
brother_ql info

# List supported label sizes
brother_ql info labels

# Verbose debugging
label-print "296-32654-ND" -v

# With Octopart API key (better results)
export OCTOPART_API_KEY="your_key_here"
label-print "296-32654-ND"
```

## Tips

- Labels look best with 24mm (default) tape
- QR codes link to datasheets for easy reference
- If Octopart lookup is slow, use `--dry-run` first to test
- Use `--save-image` to archive labels you've printed

## Next Steps

- Read `README.md` for full documentation
- Check `examples.sh` for more usage examples
- Set up environment variables in your shell profile for convenience
