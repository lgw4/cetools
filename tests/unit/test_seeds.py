import unicodedata
from unittest.mock import patch

from cetools.seeds import resolve_seed


def test_none_draws_64_bits_from_secrets():
    with patch("cetools.seeds.secrets.randbits", return_value=42) as randbits:
        assert resolve_seed(None) == 42
    randbits.assert_called_once_with(64)


def test_int_passes_through_unchanged():
    assert resolve_seed(7) == 7


def test_negative_int_passes_through_unchanged():
    assert resolve_seed(-5) == -5


def test_int_above_2_64_passes_through_unchanged():
    huge = 2**64 + 12345
    assert resolve_seed(huge) == huge


def test_digit_string_becomes_that_integer():
    assert resolve_seed("1") == 1
    assert resolve_seed("2026") == 2026


def test_signed_digit_string_becomes_that_integer():
    assert resolve_seed("+7") == 7
    assert resolve_seed("-7") == -7


def test_session_alpha_resolves_to_published_value():
    assert resolve_seed("session-alpha") == 14333185781139156525


def test_case_changes_resolve_differently():
    assert resolve_seed("session-alpha") != resolve_seed("Session-Alpha")


def test_surrounding_whitespace_resolves_differently():
    assert resolve_seed("session-alpha") != resolve_seed(" session-alpha ")


def test_nfc_and_nfd_forms_resolve_differently():
    nfc = unicodedata.normalize("NFC", "café")
    nfd = unicodedata.normalize("NFD", "café")
    assert nfc != nfd
    assert resolve_seed(nfc) != resolve_seed(nfd)
