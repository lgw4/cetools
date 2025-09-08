"""Utilities for handling Cepheus Engine pseudo-hexadecimal notation."""

from typing import Union


def dec_to_pseudo_hex(value: int) -> str:
    """
    Convert a decimal integer to Cepheus Engine pseudo-hexadecimal notation.

    In Cepheus Engine, values 0-9 remain as digits, but values 10-15 are represented
    as A-F, and values 16+ are represented as actual numbers.

    Args:
        value: The decimal integer to convert

    Returns:
        The pseudo-hexadecimal string representation
    """
    if value < 0:
        raise ValueError("Cannot convert negative values to pseudo-hex")
    if value <= 9:
        return str(value)
    if value <= 15:
        # Map 10-15 to A-F
        return chr(ord("A") + (value - 10))
    # Values 16+ remain as decimal
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

    # Handle A-F (values 10-15)
    if len(value) == 1 and "A" <= value <= "F":
        return ord(value) - ord("A") + 10

    # Ensure it's a valid number
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

    # Single character A-F
    if len(value) == 1 and "A" <= value <= "F":
        return True

    # Try to parse as a number
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
        # If it's a single A-F character, normalize case
        if len(value) == 1 and value.upper() in "ABCDEF":
            return value.upper()
        # For numeric strings that are valid pseudo-hex, preserve them as-is
        # (they're already in the correct format)
        return value

    raise ValueError(f"Cannot normalize value to pseudo-hex: {value}")


# This file contains GitHub Copilot generated content.
