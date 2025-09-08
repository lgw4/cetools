"""Utilities for handling Cepheus Engine pseudo-hexadecimal notation."""

from typing import Union

# Cepheus Engine pseudo-hexadecimal mapping tables
# Based on official SRD specification, excluding I and O
DEC_TO_PSEUDO_HEX = {
    0: "0",
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "A",
    11: "B",
    12: "C",
    13: "D",
    14: "E",
    15: "F",
    16: "G",
    17: "H",
    18: "J",
    19: "K",
    20: "L",
    21: "M",
    22: "N",
    23: "P",
    24: "Q",
    25: "R",
    26: "S",
    27: "T",
    28: "U",
    29: "V",
    30: "W",
    31: "X",
    32: "Y",
    33: "Z",
}

# Reverse mapping for pseudo-hex to decimal conversion
PSEUDO_HEX_TO_DEC = {
    v: k for k, v in DEC_TO_PSEUDO_HEX.items() if isinstance(v, str) and v.isalpha()
}


def dec_to_pseudo_hex(value: int) -> str:
    """
    Convert a decimal integer to Cepheus Engine pseudo-hexadecimal notation.

    In Cepheus Engine, values 0-9 remain as digits, values 10-33 are represented
    as A-Z (excluding I and O), and values 34+ are represented as actual numbers.

    Args:
        value: The decimal integer to convert

    Returns:
        The pseudo-hexadecimal string representation
    """
    if value < 0:
        raise ValueError("Cannot convert negative values to pseudo-hex")

    # Use dictionary lookup for values 0-33
    if value in DEC_TO_PSEUDO_HEX:
        return DEC_TO_PSEUDO_HEX[value]

    # Values 34+ remain as decimal
    return str(value)


def pseudo_hex_to_dec(value: str) -> int:
    """
    Convert a Cepheus Engine pseudo-hexadecimal notation to decimal integer.

    Args:
        value: The pseudo-hexadecimal string to convert

    Returns:
        The decimal integer representation
    """
    value = value.upper()

    # Handle single character pseudo-hex letters using dictionary lookup
    if len(value) == 1 and value in PSEUDO_HEX_TO_DEC:
        return PSEUDO_HEX_TO_DEC[value]

    # Handle numeric strings
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid pseudo-hex value: {value}")


def is_pseudo_hex(value: str) -> bool:
    """
    Check if a string is a valid Cepheus Engine pseudo-hexadecimal notation.

    Args:
        value: The string to check

    Returns:
        True if the string is a valid pseudo-hex notation, False otherwise
    """
    if not value:
        return False

    value = value.upper()

    # Check if it's a valid pseudo-hex letter using dictionary
    if len(value) == 1 and value in PSEUDO_HEX_TO_DEC:
        return True

    # Check if it's a valid number
    try:
        int(value)
        return True
    except ValueError:
        return False


def normalize_pseudo_hex(value: Union[str, int]) -> str:
    """
    Normalize a value to Cepheus Engine pseudo-hexadecimal notation.

    This function accepts either a string (which might be in decimal, hex, or
    pseudo-hex notation) or an integer, and normalizes it to pseudo-hex.

    Args:
        value: The value to normalize

    Returns:
        The normalized pseudo-hex string
    """
    if isinstance(value, int):
        return dec_to_pseudo_hex(value)

    # Handle hex notation (e.g., 0xC)
    if value.lower().startswith("0x"):
        try:
            return dec_to_pseudo_hex(int(value, 16))
        except ValueError:
            pass

    # Try as pseudo-hex
    if is_pseudo_hex(value):
        # If it's a single valid pseudo-hex character, normalize case using dictionary
        if len(value) == 1 and value.upper() in PSEUDO_HEX_TO_DEC:
            return value.upper()
        # For numeric strings that are valid pseudo-hex, preserve them as-is
        # (they're already in the correct format)
        return value

    raise ValueError(f"Cannot normalize value to pseudo-hex: {value}")


# This file contains GitHub Copilot generated content.
