import copy

import pytest

from cetools.careers import (
    CareerDefinition,
    MusteringOut,
    Rank,
    RankLadder,
    SkillTable,
    Throw,
    parse_career,
)
from cetools.notation import (
    CharacteristicAdjustment,
    CharacteristicCheck,
    SkillGrant,
    SkillReference,
)
from cetools.registries import BenefitRegistry, CharacteristicRegistry, SkillRegistry

FILE = "navy.toml"


@pytest.fixture
def characteristics():
    return CharacteristicRegistry(
        names={
            "STR": "Strength",
            "DEX": "Dexterity",
            "END": "Endurance",
            "INT": "Intellect",
            "EDU": "Education",
            "SOC": "Social Standing",
        }
    )


@pytest.fixture
def skills():
    return SkillRegistry(
        skills={
            "Ship's Boat": (),
            "Vacc Suit": (),
            "Gunnery": (),
            "Mechanical": (),
            "Gun Combat": ("Slug Rifle", "Energy Rifle"),
            "Blade": ("Cutlass", "Dagger", "Sword"),
            "Electronic": (),
            "Engineering": (),
            "Jack-of-all-Trades": (),
            "Medical": (),
            "Navigation": (),
            "Computer": (),
            "Pilot": (),
            "Admin": (),
        }
    )


@pytest.fixture
def benefits():
    return BenefitRegistry(
        items=("Low Passage", "Middle Passage", "High Passage", "Blade", "Gun", "Ship Share")
    )


@pytest.fixture
def valid_data():
    return {
        "schema": "career",
        "schema-version": 1,
        "name": "Navy",
        "throws": {
            "qualification": {"characteristic": "INT", "target": 8},
            "survival": {"characteristic": "INT", "target": 5},
            "commission": {"characteristic": "SOC", "target": 10},
            "promotion": {"characteristic": "EDU", "target": 8},
            "re-enlistment": {"target": 6},
        },
        "tables": {
            "personal": {"entries": ["STR +1", "DEX +1", "END +1", "INT +1", "EDU +1", "SOC +1"]},
            "service": {
                "entries": [
                    "Ship's Boat",
                    "Vacc Suit",
                    "Gunnery",
                    "Mechanical",
                    "Gun Combat",
                    "Blade",
                ]
            },
            "advanced": {
                "entries": [
                    "Vacc Suit",
                    "Mechanical",
                    "Electronic",
                    "Engineering",
                    "Gunnery",
                    "Jack-of-all-Trades",
                ]
            },
            "advanced-education": {
                "requires": "EDU 8+",
                "entries": ["Medical", "Navigation", "Engineering", "Computer", "Pilot", "Admin"],
            },
        },
        "ladders": [
            {
                "name": "enlisted",
                "ranks": [
                    {"rank": 1, "title": "Able Spacehand"},
                    {"rank": 5, "title": "Petty Officer", "bonus": "Mechanical 1"},
                ],
            },
            {
                "name": "officer",
                "ranks": [
                    {"rank": 1, "title": "Ensign", "bonus": "SOC +1"},
                    {"rank": 2, "title": "Lieutenant"},
                ],
            },
        ],
        "mustering-out": {
            "cash": [1000, 5000, 5000, 10000, 20000, 50000, 50000],
            "benefits": ["Low Passage", "INT +1", "EDU +2", "Blade", "High Passage", "Ship Share"],
        },
    }


def _problem_locations(problems):
    return {p.location for p in problems}


class TestValidCareer:
    def test_parses_successfully(self, valid_data, characteristics, skills, benefits):
        career, problems = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert problems == ()
        assert isinstance(career, CareerDefinition)

    def test_name(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert career.name == "Navy"

    def test_throws(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert career.throws["qualification"] == Throw(characteristic="INT", target=8)
        assert career.throws["re-enlistment"] == Throw(characteristic=None, target=6)

    def test_commission_present(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert career.throws["commission"] == Throw(characteristic="SOC", target=10)

    def test_tables(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert isinstance(career.tables["personal"], SkillTable)
        assert career.tables["personal"].requires is None
        assert career.tables["personal"].entries[0] == CharacteristicAdjustment(
            characteristic="STR", amount=1
        )

    def test_gated_table_requires(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert career.tables["advanced-education"].requires == CharacteristicCheck(
            characteristic="EDU", target=8
        )

    def test_service_table_skill_reference(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert career.tables["service"].entries[0] == SkillReference(
            name="Ship's Boat", specialty=None
        )

    def test_ladders(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert len(career.ladders) == 2
        enlisted = next(ladder for ladder in career.ladders if ladder.name == "enlisted")
        assert isinstance(enlisted, RankLadder)
        assert enlisted.ranks[0] == Rank(rank=1, title="Able Spacehand", bonus=None)

    def test_rank_bonus_resolved_as_notation(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        enlisted = next(ladder for ladder in career.ladders if ladder.name == "enlisted")
        petty_officer = enlisted.ranks[1]
        assert petty_officer.bonus == SkillGrant(
            skill=SkillReference(name="Mechanical", specialty=None), level=1
        )

    def test_mustering_out(self, valid_data, characteristics, skills, benefits):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        assert isinstance(career.mustering_out, MusteringOut)
        assert career.mustering_out.cash[0] == 1000
        assert career.mustering_out.benefits[0].name == "Low Passage"

    def test_mustering_out_benefit_adjustment_checked_against_characteristics(
        self, valid_data, characteristics, skills, benefits
    ):
        career, _ = parse_career(valid_data, FILE, characteristics, skills, benefits)
        adjustment = career.mustering_out.benefits[1]
        assert adjustment == CharacteristicAdjustment(characteristic="INT", amount=1)


class TestMissingRequiredElements:
    @pytest.mark.parametrize(
        ("path", "location"),
        [
            (("name",), "name"),
            (("throws", "qualification"), "throws.qualification"),
            (("throws", "survival"), "throws.survival"),
            (("throws", "promotion"), "throws.promotion"),
            (("throws", "re-enlistment"), "throws.re-enlistment"),
            (("tables", "personal"), "tables.personal"),
            (("tables", "service"), "tables.service"),
            (("tables", "advanced"), "tables.advanced"),
            (("mustering-out", "cash"), "mustering-out.cash"),
            (("mustering-out", "benefits"), "mustering-out.benefits"),
        ],
    )
    def test_removing_a_required_element_is_rejected(
        self, valid_data, characteristics, skills, benefits, path, location
    ):
        data = copy.deepcopy(valid_data)
        target = data
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert location in _problem_locations(problems)

    def test_removing_throws_entirely_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        del data["throws"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert problems

    def test_removing_tables_entirely_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        del data["tables"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None

    def test_removing_ladders_is_rejected(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        del data["ladders"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None

    def test_removing_mustering_out_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        del data["mustering-out"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None


class TestOptionalElements:
    def test_commission_may_be_absent(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        del data["throws"]["commission"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert problems == ()
        assert "commission" not in career.throws

    def test_advanced_education_may_be_absent(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        del data["tables"]["advanced-education"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert problems == ()
        assert "advanced-education" not in career.tables

    def test_rank_bonus_may_be_absent(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        del data["ladders"][0]["ranks"][1]["bonus"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert problems == ()

    def test_table_requires_may_be_absent(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        del data["tables"]["advanced-education"]["requires"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert problems == ()
        assert career.tables["advanced-education"].requires is None


class TestClosedNameSets:
    def test_unrecognized_throw_key_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["throws"]["retirement"] = {"target": 1}
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "throws.retirement" in _problem_locations(problems)

    def test_unrecognized_table_key_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["tables"]["sevice"] = {"entries": ["Pilot"]}
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "tables.sevice" in _problem_locations(problems)


class TestThrowTargets:
    def test_target_must_be_positive(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["throws"]["qualification"]["target"] = 0
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "throws.qualification.target" in _problem_locations(problems)

    def test_target_as_string_is_a_type_problem_not_a_notation_problem(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["throws"]["qualification"]["target"] = "8"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "throws.qualification.target"]
        assert len(matching) == 1
        assert "notation" not in matching[0].expected.lower()
        assert "integer" in matching[0].expected.lower()

    def test_unrecognized_characteristic_on_a_throw(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["throws"]["qualification"]["characteristic"] = "XYZ"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "throws.qualification.characteristic" in _problem_locations(problems)


class TestRankPositions:
    def test_negative_rank_is_rejected(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"][0]["rank"] = -1
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None

    def test_duplicate_rank_positions_within_a_ladder_are_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"][1]["rank"] = 1
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None

    def test_ranks_are_sorted_by_position(self, valid_data, characteristics, skills, benefits):
        # Ordering was the one mutation in the career schema killed by a test
        # that traced to no contract: FR-016 requires only that positions be
        # non-negative and distinct, and data-model.md alone said "sorted by
        # rank". contracts/data-files.md now states it, and states why — a
        # consumer reading a ladder never has to sort it, and two files
        # differing only in the order they list the same ranks load to the
        # same thing.
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"] = [
            {"rank": 5, "title": "Petty Officer"},
            {"rank": 1, "title": "Able Spacehand"},
        ]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert problems == ()
        enlisted = next(ladder for ladder in career.ladders if ladder.name == "enlisted")
        assert [rank.rank for rank in enlisted.ranks] == [1, 5]


class TestDistinctLadderNames:
    def test_duplicate_ladder_names_are_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["ladders"][1]["name"] = "enlisted"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None


class TestNonEmptyTables:
    def test_empty_entries_array_is_rejected(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["tables"]["personal"]["entries"] = []
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None

    def test_empty_ladders_array_is_rejected(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["ladders"] = []
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None

    def test_empty_cash_array_is_rejected(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["cash"] = []
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None

    def test_empty_ranks_array_is_rejected(self, valid_data, characteristics, skills, benefits):
        # FR-016: "A ladder MUST carry at least one rank." The sibling cases
        # above were covered and this one was not, which makes the gap
        # asymmetric rather than a drawn line.
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"] = []
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].ranks" in _problem_locations(problems)

    def test_empty_mustering_out_benefits_array_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        # FR-017: cash and benefits are both required and "both MUST declare
        # at least one entry".
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["benefits"] = []
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "mustering-out.benefits" in _problem_locations(problems)


class TestNotationBearingFieldsValidatedAgainstRegistry:
    def test_unrecognized_skill_in_service_table(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][0] = "Not A Real Skill"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "tables.service.entries[0]" in _problem_locations(problems)

    def test_unrecognized_characteristic_in_gate(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["tables"]["advanced-education"]["requires"] = "XYZ 8+"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "tables.advanced-education.requires" in _problem_locations(problems)

    def test_form_not_admitted_in_context_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        # A check is not admissible in a skill table.
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][0] = "INT 4+"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None

    def test_unrecognized_benefit_item(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["benefits"][0] = "Not A Real Benefit"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "mustering-out.benefits[0]" in _problem_locations(problems)

    def test_mustering_out_adjustment_checked_against_characteristics_not_benefit_items(
        self, valid_data, characteristics, skills, benefits
    ):
        # "INT +1" in a benefits list is an adjustment: checked against the
        # characteristics registry, never the benefit items registry.
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["benefits"][1] = "XYZ +1"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "mustering-out.benefits[1]"]
        assert len(matching) == 1
        assert "characteristic" in matching[0].expected.lower()

    def test_rank_bonus_unrecognized_skill(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"][1]["bonus"] = "Not A Real Skill 1"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].ranks[1].bonus" in _problem_locations(problems)


class TestPlainNumericFieldsNeverRoutedThroughNotation:
    def test_cash_amount_as_string_is_a_type_problem(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["cash"][0] = "1000"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "mustering-out.cash[0]"]
        assert len(matching) == 1
        assert "integer" in matching[0].expected.lower()

    def test_negative_cash_amount_is_rejected(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["cash"][0] = -1
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None


class TestGateIsOptionalOnEveryTable:
    """FR-015 says in terms that "the gate is optional on every table rather
    than fixed to one of them". Every gate in the suite and in the shipped
    data sat on `advanced-education`, so restricting `requires` to that one
    table left the whole suite passing.
    """

    @pytest.mark.parametrize("table", ["personal", "service", "advanced"])
    def test_a_gate_on_a_table_other_than_advanced_education(
        self, valid_data, characteristics, skills, benefits, table
    ):
        data = copy.deepcopy(valid_data)
        data["tables"][table]["requires"] = "EDU 8+"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert problems == ()
        assert career.tables[table].requires == CharacteristicCheck(characteristic="EDU", target=8)


class TestRequiredSubKeys:
    """The seam between FR-019's top-level enumeration, which SC-004 tests
    exhaustively, and the per-object tables in contracts/data-files.md. Each
    of these keys is required there and nothing noticed it becoming optional.
    """

    def test_a_throw_without_a_target_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        # FR-014: "The target is required."
        data = copy.deepcopy(valid_data)
        del data["throws"]["qualification"]["target"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "throws.qualification.target" in _problem_locations(problems)

    def test_a_rank_without_its_position_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        # FR-016: each rank carries "its position".
        data = copy.deepcopy(valid_data)
        del data["ladders"][0]["ranks"][0]["rank"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].ranks[0].rank" in _problem_locations(problems)

    def test_a_rank_without_its_title_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        # FR-016: each rank carries "its title".
        data = copy.deepcopy(valid_data)
        del data["ladders"][0]["ranks"][0]["title"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].ranks[0].title" in _problem_locations(problems)

    def test_a_ladder_without_a_name_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        del data["ladders"][0]["name"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].name" in _problem_locations(problems)

    def test_a_table_without_its_entries_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        # Not a lost diagnostic but a lost rejection: with the check removed,
        # `parse_career` returned no problem at all and built a career whose
        # `tables` silently omitted `service`, so a data set with no service
        # table loaded successfully. `TestNonEmptyTables` covers an *empty*
        # `entries` and `test_reference_career.py` removes only whole tables,
        # so nothing deleted this key (FR-015, FR-019, contracts/data-files.md).
        data = copy.deepcopy(valid_data)
        del data["tables"]["service"]["entries"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "tables.service.entries" in _problem_locations(problems)

    def test_a_ladder_without_its_ranks_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        # The sibling seam: with the check removed the career built with
        # `ladders` set to `None` and no problem reported (FR-016, FR-019).
        data = copy.deepcopy(valid_data)
        del data["ladders"][0]["ranks"]
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].ranks" in _problem_locations(problems)


class TestEmptyStringsAreRejectedWhereANameIsRequired:
    """`_require_string` rejects an empty value as well as a missing one, and
    every case was proved by the missing half alone: relaxing it to a bare
    `isinstance` check left the suite green. An empty career name is not a
    name, and FR-019b's distinctness rule would make two of them a clash
    rather than two careers, so the strictness is worth keeping and worth
    pinning (contracts/data-files.md).
    """

    def test_an_empty_career_name(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["name"] = ""
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "name"]
        assert len(matching) == 1
        assert matching[0].found == "an empty string"

    def test_an_empty_rank_title(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"][0]["title"] = ""
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].ranks[0].title" in _problem_locations(problems)

    def test_an_empty_ladder_name(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["name"] = ""
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].name" in _problem_locations(problems)


class TestBooleansAreNotIntegers:
    """`True == 1` in Python and nowhere in TOML, so every integer-valued
    field guards on the exact type. Weakening any of these to a bare
    `isinstance` check left the suite green, and the consequence is a rules
    value changed with no report rather than a worse message: `target = true`
    composed as `Throw(target=True)` (FR-020b, FR-014, FR-016, FR-017).
    """

    def test_a_boolean_throw_target(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["throws"]["survival"]["target"] = True
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "throws.survival.target"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"
        assert matching[0].expected == "an integer"

    def test_a_boolean_rank_position(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"][0]["rank"] = True
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "ladders[0].ranks[0].rank"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"

    def test_a_boolean_cash_amount(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["cash"][0] = True
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "mustering-out.cash[0]"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"


class TestNonStringInANotationBearingFieldIsATypeProblem:
    """contracts/notation.md: "Non-string content in a notation-bearing field
    is a type problem reported against the field, not routed to the parser."
    Replacing the guard with `value = str(value)` left the suite green, and
    under that mutation `entries = [5]` reported the unrecognized-entry-form
    problem FR-004a's typing exists to prevent instead of naming the type.
    The mirror direction — a string in a numeric field — was already covered
    (FR-004a, FR-020b).
    """

    def _assert_typed(self, problems, location):
        matching = [p for p in problems if p.location == location]
        assert len(matching) == 1, [p.location for p in problems]
        assert matching[0].found == "an integer"
        assert matching[0].expected == "a notation string"

    def test_a_table_entry(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][0] = 5
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        self._assert_typed(problems, "tables.service.entries[0]")

    def test_a_table_gate(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["tables"]["advanced-education"]["requires"] = 5
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        self._assert_typed(problems, "tables.advanced-education.requires")

    def test_a_rank_bonus(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"][1]["bonus"] = 5
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        self._assert_typed(problems, "ladders[0].ranks[1].bonus")

    def test_a_mustering_out_benefit(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["benefits"][0] = 5
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        self._assert_typed(problems, "mustering-out.benefits[0]")


class TestKeyClosureWithinEachObject:
    """FR-020 exists because a misspelled key "would otherwise leave the throw
    or table that key configures silently inoperative". The closed sets of
    throw names and table names are pinned above; the key closure *within*
    each object was not, so a misspelled `charactristic` inside a throw was
    caught by nothing a regression would trip.
    """

    def test_an_unrecognized_key_at_the_career_top_level(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["laders"] = []
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "laders" in _problem_locations(problems)

    def test_an_unrecognized_key_inside_a_throw(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["throws"]["qualification"]["charactristic"] = "INT"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "throws.qualification.charactristic" in _problem_locations(problems)

    def test_an_unrecognized_key_inside_a_skill_table(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["require"] = "EDU 8+"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "tables.service.require" in _problem_locations(problems)

    def test_an_unrecognized_key_inside_a_rank(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["ranks"][0]["titel"] = "Able Spacehand"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].ranks[0].titel" in _problem_locations(problems)

    def test_an_unrecognized_key_inside_a_ladder(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["ladders"][0]["rank"] = []
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        assert "ladders[0].rank" in _problem_locations(problems)


class TestBareNameValidatedAgainstItsPositionsRegistryAndNoOther:
    """FR-005 states the requirement together with its reason: "so that a skill
    name is never accepted because it happens to appear in the benefit items
    registry". Rejecting names absent from *both* registries left an
    implementation that consulted both and accepted a name found in either
    passing every test in the suite.
    """

    def test_a_benefits_only_name_in_a_skill_table_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        assert "Low Passage" in benefits
        assert "Low Passage" not in skills.skills
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][0] = "Low Passage"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "tables.service.entries[0]"]
        assert len(matching) == 1
        assert "skills registry" in matching[0].expected

    def test_a_skills_only_name_in_a_benefits_table_is_rejected(
        self, valid_data, characteristics, skills, benefits
    ):
        assert "Vacc Suit" in skills.skills
        assert "Vacc Suit" not in benefits
        data = copy.deepcopy(valid_data)
        data["mustering-out"]["benefits"][0] = "Vacc Suit"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert career is None
        matching = [p for p in problems if p.location == "mustering-out.benefits[0]"]
        assert len(matching) == 1
        assert "benefits registry" in matching[0].expected

    def test_a_name_in_both_registries_is_accepted_in_either_position(
        self, valid_data, characteristics, skills, benefits
    ):
        # The spec's Edge Case about one name in two registries rests on the
        # same guarantee: position selects the registry, so "Blade" resolves
        # in both without either lookup consulting the other.
        assert "Blade" in benefits and "Blade" in skills.skills
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][0] = "Blade"
        data["mustering-out"]["benefits"][0] = "Blade"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert problems == ()


class TestThreeDistinguishableSkillProblems:
    """FR-007 requires a specialty given for a skill that has none, and a
    specialty the registry does not list for that skill, to be "reported
    distinguishably from an unrecognized skill name". That is a claim about
    the reported problem, not about the `SkillResolution` enum, and the three
    branches that build the text were pinned nowhere.
    """

    def _problem(self, data, characteristics, skills, benefits, location):
        _, problems = parse_career(data, FILE, characteristics, skills, benefits)
        matching = [p for p in problems if p.location == location]
        assert len(matching) == 1, problems
        return matching[0]

    def test_a_specialty_given_for_a_skill_that_has_none(
        self, valid_data, characteristics, skills, benefits
    ):
        assert skills.skills["Admin"] == ()
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][0] = "Admin (Legal)"
        problem = self._problem(
            data, characteristics, skills, benefits, "tables.service.entries[0]"
        )
        assert problem.found == "Admin (Legal)"
        assert "no specialties" in problem.expected

    def test_a_specialty_the_registry_does_not_list_for_that_skill(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][0] = "Blade (Chainsaw)"
        problem = self._problem(
            data, characteristics, skills, benefits, "tables.service.entries[0]"
        )
        assert problem.found == "Blade (Chainsaw)"
        assert "a specialty the skills registry gives Blade" == problem.expected

    def test_an_unrecognized_skill_name(self, valid_data, characteristics, skills, benefits):
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][0] = "Vac Suit"
        problem = self._problem(
            data, characteristics, skills, benefits, "tables.service.entries[0]"
        )
        assert problem.found == "Vac Suit"
        assert problem.expected == "a name in the skills registry"

    def test_the_three_are_pairwise_distinguishable(
        self, valid_data, characteristics, skills, benefits
    ):
        reported = set()
        for entry in ("Admin (Legal)", "Blade (Chainsaw)", "Vac Suit"):
            data = copy.deepcopy(valid_data)
            data["tables"]["service"]["entries"][0] = entry
            problem = self._problem(
                data, characteristics, skills, benefits, "tables.service.entries[0]"
            )
            reported.add((problem.found, problem.expected))
        assert len(reported) == 3


class TestSpecialtyDistinguishableInLoadedData:
    def test_choice_owed_vs_fully_specified_in_service_table(
        self, valid_data, characteristics, skills, benefits
    ):
        data = copy.deepcopy(valid_data)
        data["tables"]["service"]["entries"][4] = "Gun Combat (Slug Rifle)"
        career, problems = parse_career(data, FILE, characteristics, skills, benefits)
        assert problems == ()
        bare = career.tables["service"].entries[4]
        assert bare.specialty == "Slug Rifle"
