# label-scan Usage Guide

## Overview

`label-scan` is a command-line tool that automatically extracts component information from distributor labels using AI vision, looks up missing data, and generates print-ready labels.

## Basic Workflow

### 1. Quick Scan (No Lookup)

Fastest option - uses only what's visible on the label:

```bash
label-scan ~/Downloads/parts/*.jpg --skip-lookup
```

### 2. Scan with Lookup

Enriches data with Mouser API (requires `MOUSER_API_KEY`):

```bash
label-scan ~/Downloads/parts/*.jpg -o labels.yaml
```

### 3. Interactive Edit + Print

Full workflow - scan, edit, approve, then print:

```bash
# Set your editor (bash/zsh)
export EDITOR=nano  # or vim, emacs, code --wait, etc.

# Scan, edit, and print with chain mode (saves tape)
label-scan ~/Downloads/parts/*.jpg --edit --print
```

## Command Options

```bash
label-scan [IMAGES...] [OPTIONS]

Arguments:
  IMAGES                One or more image files (supports glob patterns)

Options:
  -o, --output PATH     Output YAML file (default: labels.yaml)
  -e, --edit            Open YAML in $EDITOR after generation
  -p, --print           Print labels after editing (requires --edit)
  --skip-lookup         Skip distributor lookup (faster, uses only label OCR)
  --mouser-key TEXT     Mouser API key (or set MOUSER_API_KEY env var)
  -v, --verbose         Verbose logging
```

## YAML Format

After scanning, you'll get a YAML file like this:

```yaml
labels:
- part_number: AD8420ARMZ
  title: AD8420
  description: Instr amp, 250kHz BW, 100dB, R2R output
  url: https://www.mouser.com/ProductDetail/...
  image: /path/to/source/image.jpg

- part_number: NR6028T100M
  title: 10µH 1.9A
  description: Unshielded power inductor, 1.9A sat
  url: https://www.mouser.com/datasheet/...
  image: /path/to/source/image2.jpg
```

## Editing Labels

When using `--edit`, the YAML opens in your `$EDITOR`. You can:

- **Fix OCR errors** in part numbers
- **Adjust titles** (keep under ~20 chars for 12mm tape)
- **Modify descriptions** (keep under ~20 words)
- **Add/remove URLs** for QR codes
- **Reorder labels** (print order)
- **Delete labels** (remove entire entry)

**Save and exit** to continue, or exit without saving to abort.

## Printing

### With Interactive Edit:
```bash
label-scan images/*.jpg --edit --print
```
This will:
1. Scan all images
2. Open YAML in editor
3. Wait for you to edit and save
4. Print all labels in sequence with chain mode

### Manual Two-Step:
```bash
# Step 1: Generate and edit YAML
label-scan images/*.jpg --edit

# Step 2: Print from YAML later
for label in $(yq '.labels[] | .part_number + " " + .title' labels.yaml); do
  label-print "$label" --chain
done
```

## Examples

### Example 1: Quick scan for inventory

```bash
# Scan without API calls (fastest)
label-scan inventory/*.jpg --skip-lookup -o inventory.yaml
```

### Example 2: Mouser order labels

```bash
# Scan Mouser labels with enriched data
export MOUSER_API_KEY="your-key"
label-scan mouser-order/*.jpg -o mouser-parts.yaml
```

### Example 3: Mixed distributor batch

```bash
# Scan mixed labels, edit, print
label-scan digi-key/*.jpg mouser/*.jpg lcsc/*.jpg --edit --print
```

### Example 4: Re-scan with different settings

```bash
# First scan to see results
label-scan parts/*.jpg -o review.yaml

# Review, then re-run with lookup
label-scan parts/*.jpg --edit
```

## Tips

### Label Quality
- **Good lighting**: Avoid shadows on labels
- **Focus**: Ensure text is sharp
- **Orientation**: Any orientation works, OCR handles rotation
- **Cropping**: Not required, OCR finds the label

### Title Optimization
The AI generates concise titles, but you can customize:
- **Passives**: Value + rating (e.g., "100nF 50V", "10µH 1.9A")
- **ICs**: Part number without package suffix (e.g., "AD8420" not "AD8420ARMZ")
- **MOSFETs**: Channel + specs (e.g., "N-Ch 60V 30A")
- **Regulators**: Part + voltage (e.g., "LM1117 3.3V")

### Chain Printing
Using `--print` automatically enables chain mode (no cuts between labels) to save tape. The last label will cut automatically.

## Troubleshooting

### "No EDITOR set"
Set your editor:
```bash
export EDITOR=nano  # or vim, code --wait, etc.
```

### "Mouser API key not configured"
Either:
- Pass `--mouser-key your-key`, or
- Set environment: `export MOUSER_API_KEY=your-key`, or
- Add to `.env` file: `MOUSER_API_KEY=your-key`

### "OCR got wrong part number"
- Check image quality (lighting, focus)
- Edit the YAML manually to fix
- Use `--skip-lookup` if you'll edit anyway

### "Wrong part from Mouser search"
This happens with generic part numbers. Solutions:
- Use `--skip-lookup` and edit manually
- Check the YAML before printing
- Add the correct URL manually

## Environment Variables

All options can be set via environment with `LP_` prefix:

```bash
export LP_DRY_RUN=1              # Don't actually print
export LP_SAVE_IMAGE=/tmp/       # Save label images
export LP_CHAIN=1                # Chain mode
export LP_VERBOSE=1              # Verbose logging
export MOUSER_API_KEY=xxx        # Mouser API access
```

## Advanced: Customizing Prompts

Edit `/label_print/prompts.py` to customize:
- **LABEL_EXTRACTION_PROMPT**: How OCR extracts data from images
- **LABEL_CLEANUP_PROMPT**: How AI formats labels
- **COMPONENT_MATCH_VERIFICATION_PROMPT**: Fuzzy matching logic

See prompts.py for detailed guidelines.
