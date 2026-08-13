import unicodedata
from unittest.mock import patch

from cetools.seeds import resolve_seed, rng_seed


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


# --- rng_seed: the sign-preserving hand-off to `random.Random` (FR-002) ---


def test_rng_seed_passes_non_negative_seeds_through_unchanged():
    # Every published value in contracts/cli.md and every golden file depends on
    # this branch being the identity, so a fix for the negative case must not
    # move it.
    assert rng_seed(0) == 0
    assert rng_seed(1) == 1
    assert rng_seed(14333185781139156525) == 14333185781139156525


def test_rng_seed_does_not_alias_a_negative_seed_onto_its_positive_counterpart():
    # `random.Random` seeds an exact integer from its *absolute value*, which
    # would fold the sign away and halve the usable seed space. FR-002 forbids
    # that reduction, so the negative branch is folded rather than passed on.
    assert rng_seed(-5) != rng_seed(5)
    assert rng_seed(-(2**200 + 7)) != rng_seed(2**200 + 7)


def test_rng_seed_is_deterministic_for_the_same_negative_seed():
    assert rng_seed(-5) == rng_seed(-5)
    assert rng_seed(-12345678901234567890) == rng_seed(-12345678901234567890)


def test_rng_seed_distinguishes_negative_seeds_from_one_another():
    assert rng_seed(-5) != rng_seed(-6)
