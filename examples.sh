#!/bin/bash
# Example usage of label-print

# First, install the tool:
# pip install -e .

# Example 1: Simple Digi-Key part number (uses default info line)
label-print "296-32654-ND"

# Example 2: With custom info line
label-print "296-32654-ND" "100nF Capacitor"

# Example 3: LCSC part (uses default info line)
label-print "C0603X5R1V106M030BC"

# Example 4: LCSC with custom info
label-print "C0603X5R1V106M030BC" "Power Supply"

# Example 5: Dry run (doesn't print, useful for testing)
label-print "296-32654-ND" --dry-run

# Example 6: Save image without printing
label-print "296-32654-ND" --dry-run --save-image /tmp/label.png

# Example 7: With explicit printer (if not auto-detected)
label-print "296-32654-ND" --printer-id "usb://0x04f9:0x2015/000M6Z401370"

# Example 8: With API key for better Octopart results
label-print "296-32654-ND" --api-key "YOUR_OCTOPART_API_KEY"

# Example 9: Verbose output for debugging
label-print "296-32654-ND" -v

# Example 10: Discover available printers
brother_ql discover

# Example 11: Get printer info
brother_ql -p "usb://0x04f9:0x2015/000M6Z401370" -m PT-P700 info
