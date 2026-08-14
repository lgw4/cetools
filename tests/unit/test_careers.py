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
