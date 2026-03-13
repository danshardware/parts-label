# Architecture

## Module Overview

```
label-print/
├── label_print/
│   ├── __init__.py          # Package exports
│   ├── cli.py               # Click CLI interface (main entry point)
│   ├── octopart.py          # Octopart API client
│   ├── part_number.py       # Part validation & distributor detection
│   ├── label_generator.py   # Label image generation
│   └── printer.py           # Brother printer interface
├── setup.py                 # Package setup
├── README.md
├── QUICKSTART.md
└── tests/
    └── test_part_number.py
```

## Component Breakdown

### `cli.py`
- Entry point via Click
- Orchestrates the entire workflow
- Handles user input and output
- Error handling and validation

### `part_number.py`
- Detects distributor from part number pattern
- Validates part number format
- Supports: Digi-Key, Mouser, LCSC

### `octopart.py`
- Queries Octopart API (free tier)
- Gets part name, datasheet URL, manufacturer
- Graceful fallback if API fails

### `label_generator.py`
- Generates PIL Image with:
  - Part name (large text, top)
  - Info line (small text, bottom)
  - QR code (right side)
- Respects 24mm tape width constraint
- 203 DPI for Brother standard

### `printer.py`
- Wraps `brother_ql` CLI
- Discovers/validates printers
- Prints images to device
- Handles cleanup

## Data Flow

```
User Input (CLI)
    ↓
Part Number Validation
    ↓
Distributor Detection
    ↓
Octopart API Query
    ↓
Label Image Generation
    ↓
Brother Printer Interface
    ↓
Print to Device
```

## Design Decisions

### Why separate modules?
Each module handles one concern. Easy to test, reuse, or swap implementations.

### Why Click for CLI?
- Mature, well-documented
- Automatic help generation
- Environment variable support
- Works cross-platform

### Why Octopart?
- Free tier available (no API key needed)
- Covers all distributors
- Returns datasheet URLs
- Widely used in electronics

### Why PIL/Pillow?
- Native Python image library
- No external dependencies beyond pip
- Works on all platforms
- Built-in font support

### Why brother_ql CLI wrapper?
- Official library handles printer communication
- CLI is stable and widely tested
- Easier than low-level USB/network
- Handles multiple printer types

## Error Handling Strategy

1. **Invalid Part Number** → Exit with error message
2. **Octopart API failure** → Fall back to part number as name, continue
3. **QR code generation failure** → Log warning, print label without QR
4. **Printer not found** → Exit with helpful debug message
5. **Print timeout** → Exit with error, temp file cleaned up

## Future Enhancements

- [ ] Batch printing (multiple part numbers)
- [ ] Custom templates/layouts
- [ ] Barcode support (Code128, EAN)
- [ ] Tape width auto-detection
- [ ] Label history/archive
- [ ] Web UI for label design
- [ ] Integration with KiCad/EasyEDA BOM
