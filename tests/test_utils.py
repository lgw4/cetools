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
        assert dec_to_pseudo_hex(16) == "G"
        assert dec_to_pseudo_hex(17) == "H"
        assert dec_to_pseudo_hex(18) == "J"  # Skip I
        assert dec_to_pseudo_hex(24) == "Q"  # Q is at position 14 (24-10=14)
        assert dec_to_pseudo_hex(33) == "Z"  # Z is at position 23 (33-10=23)
        assert dec_to_pseudo_hex(34) == "34"
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
        assert pseudo_hex_to_dec("G") == 16
        assert pseudo_hex_to_dec("H") == 17
        assert pseudo_hex_to_dec("J") == 18  # Skip I
        assert pseudo_hex_to_dec("Q") == 24  # Q is at position 14 in the sequence
        assert pseudo_hex_to_dec("Z") == 33  # Z is at position 23 in the sequence
        assert pseudo_hex_to_dec("34") == 34
        assert pseudo_hex_to_dec("100") == 100

        with pytest.raises(ValueError):
            pseudo_hex_to_dec("I")  # Invalid pseudo-hex (excluded)
        with pytest.raises(ValueError):
            pseudo_hex_to_dec("O")  # Invalid pseudo-hex (excluded)
        with pytest.raises(ValueError):
            pseudo_hex_to_dec("1G")  # Invalid pseudo-hex (mixed)

    def test_is_pseudo_hex(self):
        """Test validation of pseudo-hex strings."""
        assert is_pseudo_hex("0") is True
        assert is_pseudo_hex("9") is True
        assert is_pseudo_hex("A") is True
        assert is_pseudo_hex("a") is True  # Case insensitive
        assert is_pseudo_hex("F") is True
        assert is_pseudo_hex("G") is True
        assert is_pseudo_hex("H") is True
        assert is_pseudo_hex("J") is True  # Skip I
        assert is_pseudo_hex("Q") is True
        assert is_pseudo_hex("Z") is True
        assert is_pseudo_hex("34") is True
        assert is_pseudo_hex("100") is True

        assert is_pseudo_hex("") is False
        assert is_pseudo_hex("I") is False  # Excluded letter
        assert is_pseudo_hex("O") is False  # Excluded letter
        assert is_pseudo_hex("1G") is False  # Mixed letters and numbers invalid

    def test_normalize_pseudo_hex(self):
        """Test normalization of various formats to pseudo-hex."""
        assert normalize_pseudo_hex(10) == "A"
        assert normalize_pseudo_hex(16) == "G"
        assert normalize_pseudo_hex(17) == "H"
        assert normalize_pseudo_hex(18) == "J"  # Skip I
        assert normalize_pseudo_hex(24) == "Q"  # Correct value for Q
        assert normalize_pseudo_hex(33) == "Z"
        assert normalize_pseudo_hex(34) == "34"
        assert normalize_pseudo_hex("34") == "34"
        assert normalize_pseudo_hex("A") == "A"
        assert normalize_pseudo_hex("a") == "A"  # Case normalization
        assert normalize_pseudo_hex("G") == "G"
        assert normalize_pseudo_hex("g") == "G"  # Case normalization
        assert normalize_pseudo_hex("J") == "J"
        assert normalize_pseudo_hex("j") == "J"  # Case normalization
        assert normalize_pseudo_hex("Q") == "Q"
        assert normalize_pseudo_hex("Z") == "Z"

        with pytest.raises(ValueError):
            normalize_pseudo_hex("invalid")
        with pytest.raises(ValueError):
            normalize_pseudo_hex("I")  # Excluded letter
        with pytest.raises(ValueError):
            normalize_pseudo_hex("O")  # Excluded letter
        with pytest.raises(ValueError):
            normalize_pseudo_hex("1G")  # Mixed letters and numbers


# This file contains GitHub Copilot generated content.
