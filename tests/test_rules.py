from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.generator import generate
from cetools.engine.models import Character, GenerationFailure
from cetools.engine.rolls import RollName
from cetools.engine.rules import HOUSE, SRD, Rules
from conftest import scripted

# The two departures from the SRD, both settled in
# specs/002-scout-character-career/spec.md, travel together as a policy.


def test_house_is_the_default() -> None:
    # Every production caller gets HOUSE without asking; a caller who wants the
    # SRD must say so.
    assert generate.__defaults__[-1] is HOUSE


def test_house_rerolls_until_qualified_and_holds_the_term_cap() -> None:
    assert HOUSE == Rules(reroll_until_qualified=True, natural_12_forces_extra_term=False)


def test_srd_rolls_for_enlistment_and_honours_the_natural_12() -> None:
    assert SRD == Rules(reroll_until_qualified=False, natural_12_forces_extra_term=True)


def test_rules_are_frozen() -> None:
    # A policy is a value. Two presets cannot drift into each other.
    assert HOUSE != SRD


# --- The qualification rule, end to end ---


def test_house_cannot_fail_enlistment() -> None:
    # The qualification check is scripted to fail, and HOUSE never makes it:
    # characteristics are rerolled until the career accepts them.
    result = generate(NAVY_CAREER, scripted(checks={RollName.QUALIFICATION: False}), rules=HOUSE)
    assert isinstance(result, Character)


def test_srd_can_fail_enlistment() -> None:
    result = generate(NAVY_CAREER, scripted(checks={RollName.QUALIFICATION: False}), rules=SRD)
    assert isinstance(result, GenerationFailure)
    assert "enlistment failed" in result.reason


# --- The 7-term cap, end to end ---


def test_house_holds_the_cap_against_a_natural_12() -> None:
    result = generate(
        NAVY_CAREER,
        scripted(checks={RollName.PSI_GATE: False}, two_d6={RollName.REENLISTMENT: 12}),
        rules=HOUSE,
    )
    assert isinstance(result, Character)
    assert result.terms_served == 7


def test_srd_grants_the_eighth_term_on_a_natural_12() -> None:
    result = generate(
        NAVY_CAREER,
        scripted(checks={RollName.PSI_GATE: False}, two_d6={RollName.REENLISTMENT: 12}),
        rules=SRD,
    )
    assert isinstance(result, Character)
    assert result.terms_served == 8
