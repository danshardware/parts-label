"""Tests for part number validation and distributor detection."""

import sys
sys.path.insert(0, '..')

from label_print.part_number import (
    validate_part_number,
    detect_distributor,
    Distributor,
    get_distributor_name,
)


def test_digi_key_detection():
    """Test Digi-Key part number detection."""
    assert detect_distributor("296-32654-ND") == Distributor.DIGI_KEY
    assert detect_distributor("12345-ND") == Distributor.DIGI_KEY
    assert detect_distributor("ABC-123-ND") == Distributor.DIGI_KEY


def test_lcsc_detection():
    """Test LCSC part number detection."""
    assert detect_distributor("C0603X5R1V106M030BC") == Distributor.LCSC
    assert detect_distributor("C000001") == Distributor.LCSC
    assert detect_distributor("C123456789012") == Distributor.LCSC


def test_mouser_detection():
    """Test Mouser fallback detection."""
    assert detect_distributor("571-LM358N") == Distributor.MOUSER


def test_validation():
    """Test part number validation."""
    assert validate_part_number("296-32654-ND") is True
    assert validate_part_number("C0603X5R1V106M030BC") is True
    assert validate_part_number("ABC") is True  # Min 3 chars
    assert validate_part_number("AB") is False  # Too short
    assert validate_part_number("") is False  # Empty
    assert validate_part_number(None) is False  # None


def test_distributor_names():
    """Test human-readable distributor names."""
    assert get_distributor_name(Distributor.DIGI_KEY) == "Digi-Key"
    assert get_distributor_name(Distributor.LCSC) == "LCSC"
    assert get_distributor_name(Distributor.MOUSER) == "Mouser"
    assert get_distributor_name(Distributor.UNKNOWN) == "Unknown"


if __name__ == "__main__":
    test_digi_key_detection()
    test_lcsc_detection()
    test_mouser_detection()
    test_validation()
    test_distributor_names()
    print("✅ All tests passed!")
