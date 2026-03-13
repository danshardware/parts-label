# Quick Start Guide

## Installation

### 1. Install ptouch-print:
```bash
git clone https://git.familie-radermacher.ch/linux/ptouch-print.git
cd ptouch-print
mkdir build && cd build
cmake .. && make && sudo make install
```

### 2. Install label-print:
```bash
cd /path/to/label-print
pip install -e .
```

### Requirements:
- Python 3.7+
- Brother PT-P700 label printer (USB)
- 12mm continuous label tape
- USB permissions configured (see INSTALLATION.md)

## First Steps

### 1. Check your printer is detected:
```bash
ptouch-print --info
```

You should see:
```
PT-P700 found on USB bus 3, device 58
printer has 180 dpi, maximum printing width is 128 px
maximum printing width for this tape is 76px
```

### 2. Test a simple LCSC label:
```bash
label-print "C48974" "1A 30V Schottky"
```

This will:
- Look up the part on LCSC
- Generate a 150×76px label with QR code
- Print it to your PT-P700

### 3. Test a Mouser part:
```bash
label-print "821-MBS10" ".8A 1kV bridge"
```

### 4. Use custom URL:
```bash
label-print "MY-PART" "Description" --url "https://example.com/spec.pdf"
```

## Supported Part Numbers

### LCSC (automatic lookup):
```bash
label-print "C48974" "1A 30V Schottky"
label-print "C123456" "Capacitor"
```

### Mouser (automatic lookup with API key):
```bash
export MOUSER_API_KEY="your_key_here"
label-print "821-MBS10" ".8A 1kV bridge"
```

### Digi-Key (no API, use --url):
```bash
label-print "296-32654-ND" "100nF Cap" --url "https://www.digikey.com/..."
```

## Troubleshooting

### Printer not found:
```bash
# Check connection with ptouch-print
ptouch-print --info

# Or use brother_ql for discovery
brother_ql -b pyusb discover
```

### USB permission denied (Linux):
```bash
# Add udev rule
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="04f9", MODE="0666"' | sudo tee /etc/udev/rules.d/99-brother-printer.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
# Reconnect printer
```

### Blank labels:
- Verify ptouch-print is installed (`which ptouch-print`)
- Check image with `--save-image` option
- Ensure you're using 1-bit B&W images (not RGB)

### Testing without printing:
```bash
label-print "C48974" --dry-run
label-print "C48974" --dry-run --save-image /tmp/label.png
```

## Useful Commands

```bash
# Get printer info
ptouch-print --info

# Verbose debugging
label-print "C48974" -v

# With Mouser API key
export MOUSER_API_KEY="your_key_here"
label-print "821-MBS10" ".8A 1kV bridge"

# Save image for inspection
label-print "C48974" --save-image test.png --dry-run
```

## Tips

- Use 12mm continuous tape for best results
- QR codes link to datasheets or product pages
- Dynamic font sizing maximizes readability
- Use `--url` for custom parts or when automatic lookup fails
- Use `--save-image` to preview before printing

## Next Steps

- Read `README.md` for full documentation
- Check `examples.sh` for more usage examples
- Set up environment variables in your shell profile for convenience
