"""Part number validation and distributor detection."""

import re
from enum import Enum
from typing import Optional


class Distributor(Enum):
    """Supported component distributors."""

    DIGI_KEY = "digi_key"
    MOUSER = "mouser"
    LCSC = "lcsc"
    UNKNOWN = "unknown"


def detect_distributor(part_number: str) -> Distributor:
    """
    Detect distributor from part number pattern.

    Args:
        part_number: Part number to analyze

    Returns:
        Distributor enum value
    """
    # Digi-Key patterns: 296-...-ND, [0-9]+-ND, etc.
    if re.match(r"^(296-)?[\w\-]+-ND$", part_number):
        return Distributor.DIGI_KEY

    # LCSC pattern: C[0-9]{5,12}
    if re.match(r"^C\d{5,12}$", part_number):
        return Distributor.LCSC

    # Mouser pattern: broad fallback for standard part numbers
    # This catches most patterns that aren't Digi-Key or LCSC (includes slashes)
    if re.match(r"^[\w\-/]+$", part_number) and len(part_number) >= 5:
        return Distributor.MOUSER

    return Distributor.UNKNOWN


def validate_part_number(part_number: str) -> bool:
    """
    Validate part number format.

    Args:
        part_number: Part number to validate

    Returns:
        True if valid, False otherwise
    """
    if not part_number or not isinstance(part_number, str):
        return False

    # Must be alphanumeric with dashes/underscores/spaces/slashes, 3-50 chars
    if not re.match(r"^[\w\-\s/]{3,50}$", part_number):
        return False

    return True


def get_distributor_name(distributor: Distributor) -> str:
    """
    Get human-readable distributor name.

    Args:
        distributor: Distributor enum

    Returns:
        Human-readable name
    """
    names = {
        Distributor.DIGI_KEY: "Digi-Key",
        Distributor.MOUSER: "Mouser",
        Distributor.LCSC: "LCSC",
        Distributor.UNKNOWN: "Unknown",
    }
    return names.get(distributor, "Unknown")
