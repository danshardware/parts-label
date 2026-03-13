# label-print

A CLI tool to print component labels on a Brother PT-P700 label printer.

## Features

- Automatically identifies part distributors (Digi-Key, Mouser, LCSC)
- Queries Octopart API for part information and datasheets
- Generates QR codes linking to datasheets
- Creates professional labels with part name, info line, and QR code
- 24mm tape width compatible

## Installation

```bash
pip install label-print
```

Or install from source:

```bash
git clone <repo>
cd label-print
pip install -e .
```

## Usage

### Basic usage (with sensible default):

```bash
label-print "296-32654-ND"
label-print "C0603X5R1V106M030BC"
```

### With custom info line:

```bash
label-print "296-32654-ND" "100nF Capacitor"
label-print "C0603X5R1V106M030BC" "Power Supply"
```

### Supported Part Number Formats

- **Digi-Key**: `296-...-ND`, `[0-9]+-ND$`, etc.
- **Mouser**: Standard Mouser part numbers
- **LCSC**: `/C[0-9]{5,12}/` (e.g., `C0603X5R1V106M030BC`)

## Prerequisites

1. **Brother PT-P700 printer connected** and discovered by the system
2. **brother_ql** can discover your printer:
   ```bash
   brother_ql discover
   ```

## Environment Variables

- `BROTHER_QL_PRINTER`: Printer identifier (e.g., `usb://0x04f9:0x2015/000M6Z401370`)
- `BROTHER_QL_MODEL`: Printer model (default: `PT-P700`)
- `OCTOPART_API_KEY`: Octopart API key (optional, uses free tier without it)

## Behavior

1. **Validates** the part number format
2. **Detects** distributor from part number pattern
3. **Queries** Octopart API for:
   - Part name
   - Datasheet URL
   - Manufacturer
4. **Generates** a QR code from the datasheet URL
5. **Creates** a label image with:
   - Part name (large, top)
   - Info line (small, bottom)
   - QR code (right side)
6. **Prints** to the Brother PT-P700

### Error Handling

- If Octopart lookup fails, falls back to generic part name with distributor
- Validates printer is available before printing
- Gracefully handles missing QR code generation
- Clear error messages for invalid part numbers

## Example Output

```
┌────────────────────────────┐
│ STM32L476RG                │
│ Microcontroller            │
│           ▀▀▀▀▀▀▀▀▀▀▀▀   │
│           ▀▀░░░░░░░░▀▀   │
│           ▀▀░░▀▀░░░░▀▀   │
│           ▀▀░░░░░░░░▀▀   │
│           ▀▀▀▀▀▀▀▀▀▀▀▀   │
└────────────────────────────┘
```

## License

MIT
