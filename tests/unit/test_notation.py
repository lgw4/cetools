import dataclasses

import pytest

from cetools.notation import (
    BenefitItem,
    CharacteristicAdjustment,
    CharacteristicCheck,
    EntryContext,
    NotationProblem,
    SkillGrant,
    SkillReference,
    parse_entry,
)


class TestFourForms:
    def test_check(self):
        assert parse_entry("INT 4+", EntryContext.GATE) == CharacteristicCheck(
            characteristic="INT", target=4
        )

    def test_adjustment_positive(self):
        assert parse_entry("STR +1", EntryContext.SKILL_TABLE) == CharacteristicAdjustment(
            characteristic="STR", amount=1
        )

    def test_adjustment_negative(self):
        assert parse_entry("SOC -1", EntryContext.SKILL_TABLE) == CharacteristicAdjustment(
            characteristic="SOC", amount=-1
        )

    def test_grant(self):
        assert parse_entry("Pilot 2", EntryContext.SKILL_TABLE) == SkillGrant(
            skill=SkillReference(name="Pilot", specialty=None), level=2
        )

    def test_grant_with_specialty(self):
        assert parse_entry("Blade (Cutlass) 1", EntryContext.SKILL_TABLE) == SkillGrant(
            skill=SkillReference(name="Blade", specialty="Cutlass"), level=1
        )

    def test_bare_skill_reference(self):
        assert parse_entry("Vacc Suit", EntryContext.SKILL_TABLE) == SkillReference(
            name="Vacc Suit", specialty=None
        )

    def test_bare_skill_reference_with_specialty(self):
        assert parse_entry("Gun Combat (Slug Rifle)", EntryContext.SKILL_TABLE) == SkillReference(
            name="Gun Combat", specialty="Slug Rifle"
        )

    def test_bare_benefit_item(self):
        assert parse_entry("Low Passage", EntryContext.BENEFIT_TABLE) == BenefitItem(
            name="Low Passage"
        )


class TestTailAnchoredPrecedence:
    def test_check_beats_grant_on_trailing_plus(self):
        # A trailing "+" after digits is the check form, not a grant.
        result = parse_entry("EDU 8+", EntryContext.GATE)
        assert isinstance(result, CharacteristicCheck)
        assert result.target == 8

    def test_signed_digits_is_adjustment_not_grant(self):
        result = parse_entry("DEX +2", EntryContext.SKILL_TABLE)
        assert isinstance(result, CharacteristicAdjustment)

    def test_unsigned_digits_is_grant_not_adjustment(self):
        result = parse_entry("Mechanical 1", EntryContext.SKILL_TABLE)
        assert isinstance(result, SkillGrant)


class TestNamesWithSpecialCharacters:
    def test_apostrophe(self):
        assert parse_entry("Ship's Boat", EntryContext.SKILL_TABLE) == SkillReference(
            name="Ship's Boat", specialty=None
        )

    def test_slash(self):
        assert parse_entry("Air/Raft", EntryContext.SKILL_TABLE) == SkillReference(
            name="Air/Raft", specialty=None
        )

    def test_hyphen(self):
        assert parse_entry("Jack-of-all-Trades", EntryContext.SKILL_TABLE) == SkillReference(
            name="Jack-of-all-Trades", specialty=None
        )

    def test_internal_spaces(self):
        assert parse_entry("Heavy Weapons", EntryContext.SKILL_TABLE) == SkillReference(
            name="Heavy Weapons", specialty=None
        )


class TestEntryContexts:
    def test_check_not_admitted_in_skill_table(self):
        result = parse_entry("INT 4+", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "INT 4+"

    def test_check_not_admitted_in_benefit_table(self):
        result = parse_entry("INT 4+", EntryContext.BENEFIT_TABLE)
        assert isinstance(result, NotationProblem)

    def test_grant_not_admitted_in_benefit_table(self):
        result = parse_entry("Pilot 2", EntryContext.BENEFIT_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "Pilot 2"

    def test_bare_not_admitted_in_gate(self):
        result = parse_entry("Vacc Suit", EntryContext.GATE)
        assert isinstance(result, NotationProblem)

    def test_adjustment_admitted_in_skill_table(self):
        assert isinstance(
            parse_entry("STR +1", EntryContext.SKILL_TABLE), CharacteristicAdjustment
        )

    def test_adjustment_admitted_in_benefit_table(self):
        assert isinstance(
            parse_entry("INT +1", EntryContext.BENEFIT_TABLE), CharacteristicAdjustment
        )

    def test_bare_in_skill_table_yields_skill_reference(self):
        assert isinstance(parse_entry("Pilot", EntryContext.SKILL_TABLE), SkillReference)

    def test_bare_in_benefit_table_yields_benefit_item(self):
        assert isinstance(parse_entry("Blade", EntryContext.BENEFIT_TABLE), BenefitItem)

    def test_check_admitted_in_gate(self):
        assert isinstance(parse_entry("EDU 8+", EntryContext.GATE), CharacteristicCheck)


class TestMalformedEntries:
    def test_empty_string(self):
        result = parse_entry("", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)

    def test_whitespace_only(self):
        result = parse_entry("   ", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)

    def test_trailing_sign_with_no_number(self):
        result = parse_entry("Pilot -", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "Pilot -"

    def test_unbalanced_parenthesis(self):
        result = parse_entry("Pilot (", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)

    def test_empty_specialty(self):
        result = parse_entry("Pilot ()", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)

    def test_more_than_one_specialty_group(self):
        result = parse_entry("Pilot (A) (B)", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)

    def test_not_one_of_the_four_forms(self):
        result = parse_entry("INT +4+", EntryContext.GATE)
        assert isinstance(result, NotationProblem)
        assert result.found == "INT +4+"

    def test_empty_name(self):
        result = parse_entry("2", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)

    def test_negative_level_reads_as_adjustment_not_routed_to_registry(self):
        # "Pilot -1" is grammatically a well-formed adjustment; whether "Pilot"
        # is a real characteristic is a registry question, out of scope here.
        result = parse_entry("Pilot -1", EntryContext.SKILL_TABLE)
        assert result == CharacteristicAdjustment(characteristic="Pilot", amount=-1)


class TestNoRegistryLookup:
    def test_unrecognized_characteristic_still_parses(self):
        # notation.py never consults a registry; INT vs XYZ are equally valid text.
        assert parse_entry("XYZ 4+", EntryContext.GATE) == CharacteristicCheck(
            characteristic="XYZ", target=4
        )

    def test_unrecognized_skill_still_parses(self):
        assert parse_entry("Not A Real Skill", EntryContext.SKILL_TABLE) == SkillReference(
            name="Not A Real Skill", specialty=None
        )


class TestSkillReferenceIsFrozenAndSlotted:
    def test_frozen(self):
        ref = SkillReference(name="Pilot", specialty=None)
        with pytest.raises(dataclasses.FrozenInstanceError):
            ref.name = "Other"

    def test_slotted(self):
        ref = SkillReference(name="Pilot", specialty=None)
        assert not hasattr(ref, "__dict__")
