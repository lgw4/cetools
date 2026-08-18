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
    """Every row of contracts/notation.md's malformed-entry table, pinned by
    the rule it broke rather than only by the type it returned.

    Asserting `isinstance(result, NotationProblem)` alone left three of these
    guards deletable with the suite green: with the empty-entry, balanced-
    parenthesis, and one-group checks each removed in turn, the entry still
    came back a problem — by a different route and with a detail naming the
    wrong rule — so nothing distinguished the guard doing its job from the
    fallback catching the wreckage (FR-009, FR-009a).
    """

    def test_empty_string(self):
        result = parse_entry("", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert "a non-empty entry" in result.expected

    def test_whitespace_only(self):
        result = parse_entry("   ", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert "a non-empty entry" in result.expected

    def test_trailing_sign_with_no_number(self):
        result = parse_entry("Pilot -", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "Pilot -"
        assert "a number after the sign" in result.expected

    def test_unbalanced_parenthesis(self):
        result = parse_entry("Pilot (", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert "balanced parentheses" in result.expected

    def test_empty_specialty(self):
        result = parse_entry("Pilot ()", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert "a non-empty specialty" in result.expected

    def test_more_than_one_specialty_group(self):
        result = parse_entry("Pilot (A) (B)", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert "at most one specialty group" in result.expected

    def test_not_one_of_the_four_forms(self):
        result = parse_entry("INT +4+", EntryContext.GATE)
        assert isinstance(result, NotationProblem)
        assert result.found == "INT +4+"

    def test_empty_name(self):
        result = parse_entry("2", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert "a non-empty name" in result.expected

    def test_specialty_on_a_characteristic_check(self):
        # A specialty belongs to a skill or a benefit item. A characteristic
        # never carries one, and building the check from the base name alone
        # would let text an author wrote have no effect and no diagnostic,
        # while evading the exact registry match FR-013 requires: the name as
        # written is "INT (Foo)", which no characteristics registry holds.
        result = parse_entry("INT (Foo) 4+", EntryContext.GATE)
        assert isinstance(result, NotationProblem)
        assert result.found == "INT (Foo) 4+"
        assert "characteristic check" in result.expected

    def test_specialty_on_a_characteristic_adjustment(self):
        result = parse_entry("STR (Foo) +1", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "STR (Foo) +1"
        assert "characteristic adjustment" in result.expected

    def test_specialty_on_a_characteristic_adjustment_in_a_benefit_table(self):
        result = parse_entry("SOC (Foo) -1", EntryContext.BENEFIT_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "SOC (Foo) -1"

    def test_negative_level_reads_as_adjustment_not_routed_to_registry(self):
        # "Pilot -1" is grammatically a well-formed adjustment; whether "Pilot"
        # is a real characteristic is a registry question, out of scope here.
        result = parse_entry("Pilot -1", EntryContext.SKILL_TABLE)
        assert result == CharacteristicAdjustment(characteristic="Pilot", amount=-1)


class TestTheSpaceBeforeASpecialtyGroupIsMandatory:
    """T100. `name := text [ WS "(" text ")" ]` with `WS` one or more spaces,
    and the parser split on the parenthesis without requiring any, so
    `Blade(Cutlass)`, `Blade  (Cutlass)` and `Blade (Cutlass)` were one
    reference. That is the widening FR-013 forbids, and it is the rule T087
    already applied to a benefit item; the property strategy always renders
    with a space, so nothing could find it.
    """

    def test_the_canonical_form_parses(self):
        assert parse_entry("Blade (Cutlass)", EntryContext.SKILL_TABLE) == SkillReference(
            name="Blade", specialty="Cutlass"
        )

    def test_the_space_free_form_is_malformed(self):
        result = parse_entry("Blade(Cutlass)", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "Blade(Cutlass)"
        assert "a space before the specialty group" in result.expected

    def test_the_space_free_form_is_malformed_in_the_grant_form_too(self):
        result = parse_entry("Blade(Cutlass) 1", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert "a space before the specialty group" in result.expected

    def test_more_than_one_space_still_parses(self):
        # `WS` is one or *more*, so this stays admissible; the base name is
        # stripped, which is why a skill reference has nothing to reassemble.
        assert parse_entry("Blade  (Cutlass)", EntryContext.SKILL_TABLE) == SkillReference(
            name="Blade", specialty="Cutlass"
        )

    def test_space_inside_the_group_is_still_trimmed(self):
        # The inner `.strip()` has no sibling coverage: dropping it turned
        # `Blade ( Cutlass )` from a valid reference into an unrecognized
        # specialty with the rest of the suite green.
        assert parse_entry("Blade ( Cutlass )", EntryContext.SKILL_TABLE) == SkillReference(
            name="Blade", specialty="Cutlass"
        )


class TestBareNamesWithoutWhitespace:
    """The untested complement of the trailing-token rule: an entry with no
    whitespace at all has no trailing token, so it is a bare name whatever it
    looks like. Both the `trailing is not None` guards and the `\\s+` in
    `_TRAILING_TOKEN` could be loosened with the suite green, each flipping
    these from the bare names the grammar requires into malformed entries.
    """

    @pytest.mark.parametrize("text", ["Zero-G2", "T2", "-", "+"])
    def test_a_whitespace_free_entry_is_a_bare_name(self, text):
        assert parse_entry(text, EntryContext.SKILL_TABLE) == SkillReference(
            name=text, specialty=None
        )

    def test_a_whitespace_free_entry_that_is_itself_a_suffix_is_not(self):
        # `2+` has no name before it, so it is the check form with an empty
        # characteristic rather than a bare name: the trailing-token rule is
        # about a *tail*, and an entry that is nothing but a tail has none.
        result = parse_entry("2+", EntryContext.GATE)
        assert isinstance(result, NotationProblem)
        assert "a non-empty name" in result.expected


class TestSpecialtyEndingInADigit:
    """The tail is looked for after a specialty's closing parenthesis, so the
    "trailing token contains a digit but matches no suffix form" heuristic
    never sees the `)` of `Blade (Mark 2)`. contracts/notation.md admits any
    run of non-parenthesis characters as a specialty's text, and the grant
    form of the same specialty always parsed, so rejecting the bare form was
    an over-rejection nothing had decided on (FR-006, FR-009).
    """

    def test_bare_reference_whose_specialty_ends_in_a_digit(self):
        assert parse_entry("Blade (Mark 2)", EntryContext.SKILL_TABLE) == SkillReference(
            name="Blade", specialty="Mark 2"
        )

    def test_the_grant_form_of_the_same_specialty_still_parses(self):
        assert parse_entry("Blade (Mark 2) 1", EntryContext.SKILL_TABLE) == SkillGrant(
            skill=SkillReference(name="Blade", specialty="Mark 2"), level=1
        )

    def test_bare_benefit_item_whose_specialty_ends_in_a_digit(self):
        assert parse_entry("Weapon (Mark 2)", EntryContext.BENEFIT_TABLE) == BenefitItem(
            name="Weapon (Mark 2)"
        )

    def test_text_after_the_specialty_group_is_still_malformed(self):
        # Looking for the tail after the closing parenthesis must not let text
        # beyond the specialty be dropped on the floor.
        result = parse_entry("Blade (Mark 2) Extra", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)

    def test_a_suffix_after_a_specialty_that_matches_no_form_is_still_malformed(self):
        result = parse_entry("Blade (Mark 2) x1", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)


class TestMalformedEntriesNameTheFormsTheirPositionAdmits:
    """FR-009 requires a malformed entry to report "the forms that were
    acceptable in that position", and FR-009a restates that as its reason for
    existing. A context-free "one of the four notation forms" was not merely
    incomplete but false: a gate admits one form and a benefits entry two.
    """

    _GATE_CASES = ["", "   ", "Pilot -", "Pilot (", "Pilot ()", "Pilot (A) (B)", "INT +4+", "2"]

    @pytest.mark.parametrize("text", [*_GATE_CASES, "INT (Foo) 4+"])
    def test_a_gate_names_its_one_form_and_never_claims_four(self, text):
        result = parse_entry(text, EntryContext.GATE)
        assert isinstance(result, NotationProblem)
        assert result.expected.startswith("a characteristic check")
        assert "four" not in result.expected

    @pytest.mark.parametrize("text", [*_GATE_CASES, "SOC (Foo) -1"])
    def test_a_benefit_table_names_its_two_forms(self, text):
        result = parse_entry(text, EntryContext.BENEFIT_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.expected.startswith("a characteristic adjustment or a bare benefit item")
        assert "four" not in result.expected

    @pytest.mark.parametrize("text", [*_GATE_CASES, "STR (Foo) +1"])
    def test_a_skill_table_names_its_three_forms(self, text):
        result = parse_entry(text, EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.expected.startswith(
            "a characteristic adjustment, a skill grant, or a bare skill reference"
        )
        assert "four" not in result.expected

    def test_the_specific_malformation_survives_alongside_the_admissible_forms(self):
        result = parse_entry("Pilot -", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert "a number after the sign" in result.expected


class TestMalformedEntriesReportTheEntryAsWritten:
    """FR-009 asks for "the entry as written". Every site but the empty-entry
    one reported the stripped text, so an author who wrote trailing spaces was
    shown an entry that is not the one in their file.
    """

    def test_a_malformed_entry_keeps_its_surrounding_whitespace(self):
        result = parse_entry("  Pilot -  ", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "  Pilot -  "

    def test_an_inadmissible_form_keeps_its_surrounding_whitespace(self):
        result = parse_entry("  INT 4+  ", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "  INT 4+  "

    def test_a_name_level_malformation_reports_the_whole_entry(self):
        result = parse_entry("  Pilot (A) (B)  ", EntryContext.SKILL_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "  Pilot (A) (B)  "


class TestBenefitItemMatchedAsWritten:
    """FR-013 requires every name to be matched exactly, giving case folding
    as the example of the quiet widening it forbids. Reassembling the name as
    `f"{base} ({specialty})"` widened it the same way: one registry entry
    answered to three written forms, and an item actually spelled
    `Weapon(Blade)` could never be matched at all.
    """

    def test_the_canonical_spelling_is_unchanged(self):
        assert parse_entry("Weapon (Blade)", EntryContext.BENEFIT_TABLE) == BenefitItem(
            name="Weapon (Blade)"
        )

    def test_a_missing_space_is_rejected_rather_than_normalized(self):
        # T100 settled the half T087 left open. `Weapon(Blade)` was admitted as
        # a benefit item carrying that spelling, so it failed later on the
        # registry; the grammar's `WS` before a specialty group is mandatory,
        # so it is malformed here and the author is told which rule it broke
        # instead of being told the registry has no such item.
        result = parse_entry("Weapon(Blade)", EntryContext.BENEFIT_TABLE)
        assert isinstance(result, NotationProblem)
        assert result.found == "Weapon(Blade)"
        assert "a space before the specialty group" in result.expected

    def test_a_doubled_space_is_not_collapsed(self):
        assert parse_entry("Weapon  (Blade)", EntryContext.BENEFIT_TABLE) == BenefitItem(
            name="Weapon  (Blade)"
        )

    def test_surrounding_whitespace_is_still_trimmed(self):
        assert parse_entry("  Low Passage  ", EntryContext.BENEFIT_TABLE) == BenefitItem(
            name="Low Passage"
        )

    def test_a_malformed_specialty_is_still_caught(self):
        assert isinstance(parse_entry("Weapon ()", EntryContext.BENEFIT_TABLE), NotationProblem)


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
