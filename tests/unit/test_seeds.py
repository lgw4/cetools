import unicodedata
from unittest.mock import patch

import pytest

from cetools.errors import DiceError
from cetools.seeds import derive_seed, resolve_seed, rng_seed


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


# --- FR-002: the accepted seed set is an integer, a text string, or None ---


@pytest.mark.parametrize("seed", [3.5, [1], {"seed": 1}, object(), b"1"])
def test_unsupported_seed_type_raises_dice_error_naming_the_parameter(seed):
    # Without this the value reaches the digit-string regex and comes back as
    # the regex module's own `TypeError: expected string or bytes-like object`,
    # which no `except CetoolsError` site catches and which names neither the
    # argument at fault nor what it should have been (FR-029).
    with pytest.raises(DiceError, match="seed"):
        resolve_seed(seed)


def test_bool_is_an_int_and_still_resolves_as_a_plain_int():
    # `bool` is a subclass of `int`, so the type check must stay narrow enough
    # not to break it — but the result must be a real `int`, not the `bool`
    # itself. `assert resolve_seed(True) == 1` alone is not enough: `True == 1`
    # is true, so an unconverted `bool` passes it while rendering its seed as
    # `"True"`, which does not resolve back to 1 and breaks the SC-004 round
    # trip. Assert the type, not just the value.
    for given, expected in ((True, 1), (False, 0)):
        resolved = resolve_seed(given)
        assert resolved == expected
        assert type(resolved) is int


def test_a_bool_seed_round_trips_through_its_reported_value():
    # The round trip is the property the type actually protects, so pin it
    # end to end rather than trusting the conversion in isolation.
    from cetools.dice import Roller, throw
    from cetools.render import as_dict

    result = throw(Roller(True), "2d6")
    assert result.seed == 1
    assert as_dict(result)["seed"] == "1"
    assert throw(Roller(as_dict(result)["seed"]), "2d6") == result


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


# --- derive_seed: batch positions and the name stream (research R2) ---


def test_derive_seed_is_stable_across_runs():
    # No literal from an earlier run to pin against yet, so stability is
    # checked by calling it twice rather than against a published constant —
    # the same guarantee resolve_seed's own "session-alpha" test states
    # differently because that one has a value to pin.
    assert derive_seed(1, "name") == derive_seed(1, "name")


def test_derive_seed_returns_a_non_negative_value_resolve_seed_accepts():
    derived = derive_seed(14333185781139156525, "name")
    assert isinstance(derived, int)
    assert derived >= 0
    assert resolve_seed(derived) == derived


def test_derive_seed_round_trips_as_a_decimal_string():
    derived = derive_seed(14333185781139156525, "name")
    assert resolve_seed(str(derived)) == derived


def test_derive_seed_distinguishes_different_parts():
    assert derive_seed(1, "name") != derive_seed(1, "given-name")
    assert derive_seed(1, 0) != derive_seed(1, 1)


def test_derive_seed_distinguishes_different_master_seeds():
    assert derive_seed(1, "name") != derive_seed(2, "name")


def test_derive_seed_folds_through_the_same_digest_as_a_text_seed():
    # research R2 requires derive_seed to reuse the existing blake2b fold
    # rather than introduce a second digest; pinned here by reaching the
    # module's own fold rather than by re-deriving the algorithm.
    from cetools.seeds import _fold

    assert derive_seed(1, "name") == _fold("1\x1fname")


def test_derive_seed_accepts_int_and_string_parts():
    assert derive_seed(1, 2, "three") == derive_seed(1, 2, "three")
