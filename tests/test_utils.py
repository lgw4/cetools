"""Tests for the utils module."""

import pytest

from cetools.core.utils import (
    dec_to_pseudo_hex,
    is_pseudo_hex,
    normalize_pseudo_hex,
    pseudo_hex_to_dec,
)


class TestPseudoHex:
    """Tests for the pseudo-hexadecimal notation conversion functions."""

    def test_dec_to_pseudo_hex(self):
        """Test conversion from decimal to pseudo-hex."""
        assert dec_to_pseudo_hex(0) == "0"
        assert dec_to_pseudo_hex(9) == "9"
        assert dec_to_pseudo_hex(10) == "A"
        assert dec_to_pseudo_hex(15) == "F"
        assert dec_to_pseudo_hex(16) == "16"
        assert dec_to_pseudo_hex(100) == "100"

        with pytest.raises(ValueError):
            dec_to_pseudo_hex(-1)

    def test_pseudo_hex_to_dec(self):
        """Test conversion from pseudo-hex to decimal."""
        assert pseudo_hex_to_dec("0") == 0
        assert pseudo_hex_to_dec("9") == 9
        assert pseudo_hex_to_dec("A") == 10
        assert pseudo_hex_to_dec("a") == 10  # Case insensitive
        assert pseudo_hex_to_dec("F") == 15
        assert pseudo_hex_to_dec("16") == 16
        assert pseudo_hex_to_dec("100") == 100

        with pytest.raises(ValueError):
            pseudo_hex_to_dec("G")  # Invalid pseudo-hex
        with pytest.raises(ValueError):
            pseudo_hex_to_dec("1G")  # Invalid pseudo-hex

    def test_is_pseudo_hex(self):
        """Test validation of pseudo-hex strings."""
        assert is_pseudo_hex("0") is True
        assert is_pseudo_hex("9") is True
        assert is_pseudo_hex("A") is True
        assert is_pseudo_hex("a") is True  # Case insensitive
        assert is_pseudo_hex("F") is True
        assert is_pseudo_hex("16") is True
        assert is_pseudo_hex("100") is True

        assert is_pseudo_hex("") is False
        assert is_pseudo_hex("G") is False
        assert is_pseudo_hex("1G") is False

    def test_normalize_pseudo_hex(self):
        """Test normalization of various formats to pseudo-hex."""
        assert normalize_pseudo_hex(10) == "A"
        assert normalize_pseudo_hex("10") == "10"
        assert normalize_pseudo_hex("A") == "A"
        assert normalize_pseudo_hex("a") == "A"  # Case normalization
        assert normalize_pseudo_hex("0xA") == "A"  # Hex notation
        assert normalize_pseudo_hex("0xC") == "C"

        with pytest.raises(ValueError):
            normalize_pseudo_hex("invalid")


# This file contains GitHub Copilot generated content.
