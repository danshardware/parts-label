#!/bin/bash
# Example usage of label-print for Brother PT-P700

# First, install the tool:
# pip install -e .

# Example 1: LCSC part number (automatic lookup)
label-print "C48974" "1A 30V Schottky"

# Example 2: Mouser part number (automatic lookup)
label-print "821-MBS10" ".8A 1kV bridge"

# Example 2a: Using environment variables for batch chain printing
export LP_CHAIN=1  # Skip cutting between labels to save tape
label-print "C48974" "1A 30V Schottky"
label-print "821-MBS10" ".8A 1kV bridge"
label-print "C48974" "Another part"
unset LP_CHAIN  # Clean up

# Example 2b: Environment variable for dry-run mode
export LP_DRY_RUN=1  # Test without printing
label-print "C48974" "1A 30V Schottky"
unset LP_DRY_RUN

# Example 3: Digi-Key part (no API, uses part number as name)
label-print "296-32654-ND" "100nF Capacitor"

# Example 4: Custom part with URL (skip automatic lookup)
label-print "MY-PART-123" "Custom component" --url "https://example.com/datasheet.pdf"

# Example 5: Uses default info line
label-print "C48974"

# Example 6: Dry run (doesn't print, useful for testing)
label-print "C48974" --dry-run

# Example 7: Save image without printing
label-print "C48974" "1A 30V Schottky" --save-image /tmp/label.png --dry-run

# Example 8: With Mouser API key (optional, can use .env file)
label-print "821-MBS10" ".8A 1kV bridge" --mouser-key "YOUR_MOUSER_API_KEY"

# Example 9: Verbose output for debugging
label-print "C48974" -v

# Example 10: Discover available printers (for reference, uses brother_ql)
brother_ql -b pyusb discover

# Example 11: Get printer info (uses ptouch-print)
ptouch-print --info
