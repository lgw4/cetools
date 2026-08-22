import copy

import pytest

from cetools.chargen import (
    AgingTable,
    BackgroundSkills,
    ChargenParameters,
    DraftTable,
    MedicalTiers,
    MishapTable,
    parse_aging_table,
    parse_background_skills,
    parse_chargen_parameters,
    parse_draft_table,
    parse_medical_tiers,
    parse_mishap_table,
)
from cetools.errors import ValidationProblem
from cetools.registries import SkillRegistry


class TestDraftTable:
    def _data(self, **overrides):
        data = {
            "schema": "draft-table",
            "schema-version": 1,
            "roll": "1d6",
            "careers": ["Aerospace Defense", "Marine", "Maritime Defense", "Navy", "Scout"],
        }
        data.update(overrides)
        return data

    def test_parses_valid_file(self):
        table, problems = parse_draft_table(self._data(), "draft.toml")
        assert problems == ()
        assert isinstance(table, DraftTable)
        assert table.roll == "1d6"
        assert table.careers == (
            "Aerospace Defense",
            "Marine",
            "Maritime Defense",
            "Navy",
            "Scout",
        )

    def test_row_order_is_preserved_not_sorted(self):
        # FR-005: the row a draft throw reads is positional, so the parser
        # must not reorder the careers array in any way (e.g. alphabetizing).
        table, problems = parse_draft_table(
            self._data(careers=["Scout", "Marine", "Navy"]), "draft.toml"
        )
        assert problems == ()
        assert table.careers == ("Scout", "Marine", "Navy")

    def test_d66_roll_is_rejected(self):
        # `d66` composes two faces into a two-digit table value rather than
        # describing a count and a side count; the draft table's own die
        # reads a plain total, like task.roll (001-dice-task-engine FR-029).
        table, problems = parse_draft_table(self._data(roll="d66"), "draft.toml")
        assert table is None
        assert any(p.location == "roll" for p in problems)

    def test_unparseable_roll_is_rejected(self):
        table, problems = parse_draft_table(self._data(roll="not dice"), "draft.toml")
        assert table is None
        assert any(p.location == "roll" for p in problems)

    def test_missing_roll_is_a_problem(self):
        data = self._data()
        del data["roll"]
        table, problems = parse_draft_table(data, "draft.toml")
        assert table is None
        assert any(p.location == "roll" and p.found == "missing" for p in problems)

    def test_empty_careers_array_is_a_problem(self):
        table, problems = parse_draft_table(self._data(careers=[]), "draft.toml")
        assert table is None
        assert any(p.location == "careers" for p in problems)

    def test_missing_careers_is_a_problem(self):
        data = self._data()
        del data["careers"]
        table, problems = parse_draft_table(data, "draft.toml")
        assert table is None
        assert any(p.location == "careers" and p.found == "missing" for p in problems)

    def test_non_string_career_entry_is_a_type_problem(self):
        table, problems = parse_draft_table(self._data(careers=["Navy", 5]), "draft.toml")
        assert table is None
        assert any(p.location == "careers[1]" for p in problems)

    def test_unrecognized_top_level_key_is_a_problem(self):
        table, problems = parse_draft_table(self._data(extra="nope"), "draft.toml")
        assert table is None
        assert any(p.location == "extra" for p in problems)

    def test_problems_are_validation_problem_instances(self):
        _, problems = parse_draft_table(self._data(roll="d66"), "draft.toml")
        assert all(isinstance(p, ValidationProblem) for p in problems)


class TestAgingTable:
    def _data(self, **overrides):
        data = {
            "schema": "aging-table",
            "schema-version": 1,
            "roll": "2d6",
            "modifier": "terms-served",
            "rows": [
                {
                    "range": "-6",
                    "effects": [
                        {"class": "physical", "count": 3, "amount": -2},
                        {"class": "mental", "count": 1, "amount": -1},
                    ],
                },
                {"range": "0", "effects": [{"class": "physical", "count": 1, "amount": -1}]},
                {"range": "1+", "effects": []},
            ],
        }
        data.update(overrides)
        return data

    def test_parses_valid_file(self):
        table, problems = parse_aging_table(self._data(), "aging.toml")
        assert problems == ()
        assert isinstance(table, AgingTable)
        assert table.roll == "2d6"
        assert len(table.rows) == 3

    def test_rows_sort_by_minimum_regardless_of_file_order(self):
        data = self._data()
        data["rows"] = list(reversed(data["rows"]))
        table, problems = parse_aging_table(data, "aging.toml")
        assert problems == ()
        assert [row.minimum for row in table.rows] == [-6, 0, 1]

    def test_single_value_range_sets_minimum_equal_to_maximum(self):
        table, _ = parse_aging_table(self._data(), "aging.toml")
        zero_row = next(row for row in table.rows if row.minimum == 0)
        assert zero_row.maximum == 0

    def test_negative_single_value_range_parses(self):
        table, _ = parse_aging_table(self._data(), "aging.toml")
        floor_row = min(table.rows, key=lambda row: row.minimum)
        assert floor_row.minimum == -6
        assert floor_row.maximum == -6

    def test_bounded_range_parses_minimum_and_maximum(self):
        data = self._data()
        data["rows"][1]["range"] = "0-3"
        table, problems = parse_aging_table(data, "aging.toml")
        assert problems == ()
        row = next(row for row in table.rows if row.minimum == 0)
        assert row.maximum == 3

    def test_unbounded_top_row_has_no_maximum(self):
        table, _ = parse_aging_table(self._data(), "aging.toml")
        top_row = max(table.rows, key=lambda row: row.minimum)
        assert top_row.maximum is None

    def test_no_unbounded_row_is_a_problem(self):
        data = self._data()
        data["rows"][2]["range"] = "1"
        table, problems = parse_aging_table(data, "aging.toml")
        assert table is None
        assert any(p.location == "rows" for p in problems)

    def test_two_unbounded_rows_is_a_problem(self):
        data = self._data()
        data["rows"].append({"range": "5+", "effects": []})
        table, problems = parse_aging_table(data, "aging.toml")
        assert table is None
        assert any(p.location == "rows" for p in problems)

    def test_empty_effects_list_is_valid(self):
        table, problems = parse_aging_table(self._data(), "aging.toml")
        assert problems == ()
        top_row = max(table.rows, key=lambda row: row.minimum)
        assert top_row.effects == ()

    def test_effect_fields_parse(self):
        table, _ = parse_aging_table(self._data(), "aging.toml")
        floor_row = min(table.rows, key=lambda row: row.minimum)
        assert floor_row.effects[0].characteristic_class == "physical"
        assert floor_row.effects[0].count == 3
        assert floor_row.effects[0].amount == -2

    def test_zero_amount_effect_is_a_problem(self):
        data = self._data()
        data["rows"][0]["effects"][0]["amount"] = 0
        table, problems = parse_aging_table(data, "aging.toml")
        assert table is None
        assert any("effects[0].amount" in p.location for p in problems)

    def test_zero_count_effect_is_a_problem(self):
        data = self._data()
        data["rows"][0]["effects"][0]["count"] = 0
        table, problems = parse_aging_table(data, "aging.toml")
        assert table is None
        assert any("effects[0].count" in p.location for p in problems)

    def test_malformed_range_is_a_problem(self):
        data = self._data()
        data["rows"][0]["range"] = "low"
        table, problems = parse_aging_table(data, "aging.toml")
        assert table is None
        assert any("range" in p.location for p in problems)

    def test_modifier_other_than_terms_served_is_a_problem(self):
        table, problems = parse_aging_table(self._data(modifier="rank"), "aging.toml")
        assert table is None
        assert any(p.location == "modifier" for p in problems)

    def test_missing_rows_is_a_problem(self):
        data = self._data()
        del data["rows"]
        table, problems = parse_aging_table(data, "aging.toml")
        assert table is None
        assert any(p.location == "rows" and p.found == "missing" for p in problems)

    def test_unrecognized_top_level_key_is_a_problem(self):
        table, problems = parse_aging_table(self._data(extra="nope"), "aging.toml")
        assert table is None
        assert any(p.location == "extra" for p in problems)


class TestMishapTable:
    def _data(self, **overrides):
        data = {
            "schema": "mishap-table",
            "schema-version": 1,
            "roll": "1d6",
            "injury-roll": "1d6",
            "mishaps": [
                {
                    "description": "Injured in action.",
                    "effects": [
                        {
                            "kind": "characteristic-class",
                            "class": "physical",
                            "count": 1,
                            "amount": "-1d6",
                        }
                    ],
                },
                {"description": "Honorably discharged from the service.", "effects": []},
                {
                    "description": "Honorably discharged after a long legal battle.",
                    "effects": [{"kind": "debt", "amount": "10000"}],
                },
            ],
            "injuries": [{"description": "Lightly injured.", "effects": []}],
        }
        data.update(overrides)
        return data

    def test_parses_valid_file(self):
        table, problems = parse_mishap_table(self._data(), "mishaps.toml")
        assert problems == ()
        assert isinstance(table, MishapTable)
        assert table.roll == "1d6"
        assert table.injury_roll == "1d6"
        assert len(table.rows) == 3
        assert len(table.injuries) == 1

    def test_row_order_is_preserved(self):
        # Like the draft table, the total read positionally indexes the row.
        table, _ = parse_mishap_table(self._data(), "mishaps.toml")
        assert table.rows[0].description == "Injured in action."
        assert table.rows[2].description == "Honorably discharged after a long legal battle."

    def test_characteristic_class_effect_parses_dice_amount(self):
        table, _ = parse_mishap_table(self._data(), "mishaps.toml")
        effect = table.rows[0].effects[0]
        assert effect.kind == "characteristic-class"
        assert effect.characteristic_class == "physical"
        assert effect.count == 1
        assert effect.amount == "-1d6"

    def test_debt_effect_parses_plain_integer_amount_as_text(self):
        table, _ = parse_mishap_table(self._data(), "mishaps.toml")
        effect = table.rows[2].effects[0]
        assert effect.kind == "debt"
        assert effect.amount == "10000"
        assert effect.characteristic_class == ""
        assert effect.count == 0

    def test_empty_effects_list_is_valid(self):
        table, problems = parse_mishap_table(self._data(), "mishaps.toml")
        assert problems == ()
        assert table.rows[1].effects == ()

    def test_years_effect_kind_accepts_an_amount(self):
        data = self._data()
        data["mishaps"][1]["effects"] = [{"kind": "years", "amount": "4"}]
        table, problems = parse_mishap_table(data, "mishaps.toml")
        assert problems == ()
        assert table.rows[1].effects[0].kind == "years"
        assert table.rows[1].effects[0].amount == "4"

    def test_forfeit_term_benefit_kind_needs_no_amount(self):
        data = self._data()
        data["mishaps"][1]["effects"] = [{"kind": "forfeit-term-benefit"}]
        table, problems = parse_mishap_table(data, "mishaps.toml")
        assert problems == ()
        assert table.rows[1].effects[0].kind == "forfeit-term-benefit"
        assert table.rows[1].effects[0].amount == ""

    def test_forfeit_career_benefits_kind_needs_no_amount(self):
        data = self._data()
        data["mishaps"][1]["effects"] = [{"kind": "forfeit-career-benefits"}]
        table, problems = parse_mishap_table(data, "mishaps.toml")
        assert problems == ()
        assert table.rows[1].effects[0].kind == "forfeit-career-benefits"

    def test_roll_injury_kind_carries_no_class_count_or_amount(self):
        data = self._data()
        data["mishaps"][1]["effects"] = [{"kind": "roll-injury"}]
        table, problems = parse_mishap_table(data, "mishaps.toml")
        assert problems == ()
        effect = table.rows[1].effects[0]
        assert effect.kind == "roll-injury"
        assert effect.characteristic_class == ""
        assert effect.count == 0
        assert effect.amount == ""

    def test_misspelled_kind_is_rejected_by_the_closed_set(self):
        data = self._data()
        data["mishaps"][1]["effects"] = [{"kind": "characteristic_class"}]
        table, problems = parse_mishap_table(data, "mishaps.toml")
        assert table is None
        assert any("kind" in p.location for p in problems)

    def test_amount_that_is_neither_dice_notation_nor_an_integer_is_rejected(self):
        data = self._data()
        data["mishaps"][2]["effects"][0]["amount"] = "a lot"
        table, problems = parse_mishap_table(data, "mishaps.toml")
        assert table is None
        assert any("amount" in p.location for p in problems)

    def test_class_field_on_a_debt_effect_is_an_unrecognized_key(self):
        data = self._data()
        data["mishaps"][2]["effects"][0]["class"] = "physical"
        table, problems = parse_mishap_table(data, "mishaps.toml")
        assert table is None
        assert any("class" in p.location for p in problems)

    def test_empty_mishaps_array_is_a_problem(self):
        table, problems = parse_mishap_table(self._data(mishaps=[]), "mishaps.toml")
        assert table is None
        assert any(p.location == "mishaps" for p in problems)

    def test_empty_injuries_array_is_a_problem(self):
        table, problems = parse_mishap_table(self._data(injuries=[]), "mishaps.toml")
        assert table is None
        assert any(p.location == "injuries" for p in problems)

    def test_missing_description_is_a_problem(self):
        data = self._data()
        del data["mishaps"][1]["description"]
        table, problems = parse_mishap_table(data, "mishaps.toml")
        assert table is None
        assert any("description" in p.location for p in problems)

    def test_unrecognized_top_level_key_is_a_problem(self):
        table, problems = parse_mishap_table(self._data(extra="nope"), "mishaps.toml")
        assert table is None
        assert any(p.location == "extra" for p in problems)


class TestBackgroundSkills:
    SKILLS = SkillRegistry(
        skills={"Gun Combat": ("Slug Rifle", "Energy Rifle"), "Melee Combat": (), "Animals": ()}
    )

    def _data(self, **overrides):
        data = {
            "schema": "background-skills",
            "schema-version": 1,
            "law-level": ["Gun Combat 0", "Gun Combat 0", "Melee Combat 0"],
            "trade-code": ["Animals 0", "Gun Combat 0"],
            "education": ["Melee Combat 1"],
        }
        data.update(overrides)
        return data

    def test_parses_valid_file(self):
        table, problems = parse_background_skills(
            self._data(), "background-skills.toml", self.SKILLS
        )
        assert problems == ()
        assert isinstance(table, BackgroundSkills)
        assert len(table.law_level) == 3
        assert len(table.trade_code) == 2
        assert len(table.education) == 1
        assert table.law_level[0].skill.name == "Gun Combat"
        assert table.law_level[0].level == 0

    def test_duplicates_within_a_list_are_preserved(self):
        # research R5: a skill named twice in one list is twice as likely to
        # be drawn, so the parser must not deduplicate.
        table, _ = parse_background_skills(self._data(), "background-skills.toml", self.SKILLS)
        names = [grant.skill.name for grant in table.law_level]
        assert names == ["Gun Combat", "Gun Combat", "Melee Combat"]

    def test_duplicates_across_law_level_and_trade_code_are_independent_lists(self):
        # The same skill appearing in both lists is meaningful weighting
        # across the concatenation the walk draws from, not something the
        # parser reconciles between the two fields.
        table, _ = parse_background_skills(self._data(), "background-skills.toml", self.SKILLS)
        assert any(grant.skill.name == "Gun Combat" for grant in table.law_level)
        assert any(grant.skill.name == "Gun Combat" for grant in table.trade_code)

    def test_unresolvable_skill_name_is_a_problem(self):
        table, problems = parse_background_skills(
            self._data(education=["Not A Skill 0"]), "background-skills.toml", self.SKILLS
        )
        assert table is None
        assert any(p.location == "education[0]" for p in problems)

    def test_a_bare_skill_reference_with_no_level_is_rejected(self):
        # data-model.md types every entry as a SkillGrant: a level is always
        # explicit in this table, unlike a career's tables.
        table, problems = parse_background_skills(
            self._data(**{"law-level": ["Gun Combat"]}), "background-skills.toml", self.SKILLS
        )
        assert table is None
        assert any(p.location == "law-level[0]" for p in problems)

    def test_a_characteristic_adjustment_is_rejected(self):
        table, problems = parse_background_skills(
            self._data(**{"law-level": ["STR +1"]}), "background-skills.toml", self.SKILLS
        )
        assert table is None
        assert any(p.location == "law-level[0]" for p in problems)

    def test_empty_law_level_array_is_a_problem(self):
        table, problems = parse_background_skills(
            self._data(**{"law-level": []}), "background-skills.toml", self.SKILLS
        )
        assert table is None
        assert any(p.location == "law-level" for p in problems)

    def test_missing_trade_code_is_a_problem(self):
        data = self._data()
        del data["trade-code"]
        table, problems = parse_background_skills(data, "background-skills.toml", self.SKILLS)
        assert table is None
        assert any(p.location == "trade-code" and p.found == "missing" for p in problems)

    def test_unrecognized_top_level_key_is_a_problem(self):
        table, problems = parse_background_skills(
            self._data(extra="nope"), "background-skills.toml", self.SKILLS
        )
        assert table is None
        assert any(p.location == "extra" for p in problems)


class TestMedicalTiers:
    def _data(self, **overrides):
        data = {
            "schema": "medical-tiers",
            "schema-version": 1,
            "roll": "2d6",
            "rank-dm": True,
            "tiers": [
                {
                    "name": "service",
                    "thresholds": [
                        {"target": 4, "paid-percent": 75},
                        {"target": 8, "paid-percent": 100},
                    ],
                },
                {
                    "name": "fringe",
                    "thresholds": [
                        {"target": 8, "paid-percent": 50},
                        {"target": 12, "paid-percent": 75},
                    ],
                },
            ],
        }
        data.update(overrides)
        return data

    def test_parses_valid_file(self):
        table, problems = parse_medical_tiers(self._data(), "medical-tiers.toml")
        assert problems == ()
        assert isinstance(table, MedicalTiers)
        assert table.roll == "2d6"
        assert table.rank_dm is True
        assert set(table.tiers) == {"service", "fringe"}

    def test_thresholds_sort_highest_target_first(self):
        table, _ = parse_medical_tiers(self._data(), "medical-tiers.toml")
        targets = [threshold.target for threshold in table.tiers["service"]]
        assert targets == [8, 4]

    def test_thresholds_sort_regardless_of_file_order(self):
        data = self._data()
        data["tiers"][0]["thresholds"] = list(reversed(data["tiers"][0]["thresholds"]))
        table, problems = parse_medical_tiers(data, "medical-tiers.toml")
        assert problems == ()
        targets = [threshold.target for threshold in table.tiers["service"]]
        assert targets == [8, 4]

    def test_paid_percent_out_of_range_is_a_problem(self):
        data = self._data()
        data["tiers"][0]["thresholds"][0]["paid-percent"] = 101
        table, problems = parse_medical_tiers(data, "medical-tiers.toml")
        assert table is None
        assert any("paid-percent" in p.location for p in problems)

    def test_negative_paid_percent_is_a_problem(self):
        data = self._data()
        data["tiers"][0]["thresholds"][0]["paid-percent"] = -1
        table, problems = parse_medical_tiers(data, "medical-tiers.toml")
        assert table is None
        assert any("paid-percent" in p.location for p in problems)

    def test_paid_percent_boundary_values_are_valid(self):
        data = self._data()
        data["tiers"][0]["thresholds"][0]["paid-percent"] = 0
        data["tiers"][0]["thresholds"][1]["paid-percent"] = 100
        table, problems = parse_medical_tiers(data, "medical-tiers.toml")
        assert problems == ()

    def test_duplicate_tier_name_is_a_problem(self):
        data = self._data()
        data["tiers"].append(dict(data["tiers"][0]))
        table, problems = parse_medical_tiers(data, "medical-tiers.toml")
        assert table is None
        assert any("service" in p.found for p in problems)

    def test_rank_dm_must_be_a_boolean_not_assumed(self):
        # Declared rather than assumed: a missing rank-dm is a problem, not a
        # default of False the engine holds.
        data = self._data()
        del data["rank-dm"]
        table, problems = parse_medical_tiers(data, "medical-tiers.toml")
        assert table is None
        assert any(p.location == "rank-dm" and p.found == "missing" for p in problems)

    def test_empty_tiers_array_is_a_problem(self):
        table, problems = parse_medical_tiers(self._data(tiers=[]), "medical-tiers.toml")
        assert table is None
        assert any(p.location == "tiers" for p in problems)

    def test_empty_thresholds_array_is_a_problem(self):
        data = self._data()
        data["tiers"][0]["thresholds"] = []
        table, problems = parse_medical_tiers(data, "medical-tiers.toml")
        assert table is None
        assert any("thresholds" in p.location for p in problems)

    def test_duplicate_target_within_a_tier_is_a_problem(self):
        data = self._data()
        data["tiers"][0]["thresholds"].append({"target": 4, "paid-percent": 90})
        table, problems = parse_medical_tiers(data, "medical-tiers.toml")
        assert table is None
        assert any("4" in p.found for p in problems)

    def test_unrecognized_top_level_key_is_a_problem(self):
        table, problems = parse_medical_tiers(self._data(extra="nope"), "medical-tiers.toml")
        assert table is None
        assert any(p.location == "extra" for p in problems)


def _valid_chargen_parameters_data() -> dict:
    return {
        "schema": "chargen-parameters",
        "schema-version": 1,
        "characteristics": {"roll": "2d6"},
        "background-skills": {"base": 3, "characteristic": "EDU", "homeworld-first": 2},
        "terms": {
            "starting-age": 18,
            "term-years": 4,
            "mishap-term-years": 2,
            "cap": 7,
            "aging-begins-at-age": 34,
        },
        "qualification": {"penalty-per-previous-career": -2, "draft-entries-allowed": 1},
        "basic-training": {"first-career-all": True, "subsequent-career-count": 1},
        "survival": {"natural-failure": 2},
        "skill-rolls": {
            "per-term": 1,
            "per-term-without-throws": 2,
            "on-commission": 1,
            "on-advancement": 1,
        },
        "commission": {"drafted-first-term-barred": True},
        "continuation": {"roll": "1d6", "target": 4},
        "mustering-out": {
            "roll": "1d6",
            "cash-choice-roll": "1d6",
            "cash-choice-target": 4,
            "maximum-cash-rolls": 3,
            "retired-cash-dm": 1,
            "rank-benefits": [
                {"rank": 4, "extra": 1},
                {"rank": 5, "extra": 2},
                {"rank": 6, "extra": 3},
            ],
            "material-rank-dm": [{"rank": 5, "dm": 1}],
        },
        "pension": {"minimum-terms": 5, "base": 10000, "per-additional-term": 2000},
        "medical": {
            "crisis-roll": "1d6",
            "crisis-multiplier": 10000,
            "crisis-restores-to": 1,
            "restore-cost-per-point": 5000,
        },
    }


# (group, key, attribute) for every scalar FR-038 enumerates, so the
# missing/misspelled-key tests below cover the whole surface rather than a
# hand-picked sample.
_CHARGEN_SCALARS = [
    ("characteristics", "roll", "characteristics_roll"),
    ("background-skills", "base", "background_skills_base"),
    ("background-skills", "characteristic", "background_skills_characteristic"),
    ("background-skills", "homeworld-first", "background_skills_homeworld_first"),
    ("terms", "starting-age", "terms_starting_age"),
    ("terms", "term-years", "terms_term_years"),
    ("terms", "mishap-term-years", "terms_mishap_term_years"),
    ("terms", "cap", "terms_cap"),
    ("terms", "aging-begins-at-age", "terms_aging_begins_at_age"),
    (
        "qualification",
        "penalty-per-previous-career",
        "qualification_penalty_per_previous_career",
    ),
    ("qualification", "draft-entries-allowed", "qualification_draft_entries_allowed"),
    ("basic-training", "first-career-all", "basic_training_first_career_all"),
    ("basic-training", "subsequent-career-count", "basic_training_subsequent_career_count"),
    ("survival", "natural-failure", "survival_natural_failure"),
    ("skill-rolls", "per-term", "skill_rolls_per_term"),
    ("skill-rolls", "per-term-without-throws", "skill_rolls_per_term_without_throws"),
    ("skill-rolls", "on-commission", "skill_rolls_on_commission"),
    ("skill-rolls", "on-advancement", "skill_rolls_on_advancement"),
    ("commission", "drafted-first-term-barred", "commission_drafted_first_term_barred"),
    ("continuation", "roll", "continuation_roll"),
    ("continuation", "target", "continuation_target"),
    ("mustering-out", "roll", "mustering_out_roll"),
    ("mustering-out", "cash-choice-roll", "mustering_out_cash_choice_roll"),
    ("mustering-out", "cash-choice-target", "mustering_out_cash_choice_target"),
    ("mustering-out", "maximum-cash-rolls", "mustering_out_maximum_cash_rolls"),
    ("mustering-out", "retired-cash-dm", "mustering_out_retired_cash_dm"),
    ("pension", "minimum-terms", "pension_minimum_terms"),
    ("pension", "base", "pension_base"),
    ("pension", "per-additional-term", "pension_per_additional_term"),
    ("medical", "crisis-roll", "medical_crisis_roll"),
    ("medical", "crisis-multiplier", "medical_crisis_multiplier"),
    ("medical", "crisis-restores-to", "medical_crisis_restores_to"),
    ("medical", "restore-cost-per-point", "medical_restore_cost_per_point"),
]


class TestChargenParameters:
    def test_parses_valid_file(self):
        parameters, problems = parse_chargen_parameters(
            _valid_chargen_parameters_data(), "chargen-parameters.toml"
        )
        assert problems == ()
        assert isinstance(parameters, ChargenParameters)
        assert parameters.characteristics_roll == "2d6"
        assert parameters.terms_cap == 7
        assert parameters.qualification_penalty_per_previous_career == -2
        assert parameters.basic_training_first_career_all is True
        assert parameters.commission_drafted_first_term_barred is True

    def test_rank_benefits_parse_as_rank_and_amount_pairs(self):
        parameters, problems = parse_chargen_parameters(
            _valid_chargen_parameters_data(), "chargen-parameters.toml"
        )
        assert problems == ()
        assert [(b.rank, b.amount) for b in parameters.mustering_out_rank_benefits] == [
            (4, 1),
            (5, 2),
            (6, 3),
        ]

    def test_material_rank_dm_parses_as_rank_and_amount_pairs(self):
        parameters, problems = parse_chargen_parameters(
            _valid_chargen_parameters_data(), "chargen-parameters.toml"
        )
        assert problems == ()
        assert [(b.rank, b.amount) for b in parameters.mustering_out_material_rank_dm] == [(5, 1)]

    @pytest.mark.parametrize(("group", "key", "attribute"), _CHARGEN_SCALARS)
    def test_every_scalar_is_required(self, group, key, attribute):
        data = copy.deepcopy(_valid_chargen_parameters_data())
        del data[group][key]
        parameters, problems = parse_chargen_parameters(data, "chargen-parameters.toml")
        assert parameters is None
        location = f"{group}.{key}"
        assert any(
            p.location == location and p.found == "missing" for p in problems
        ), f"{location} was not reported missing: {problems}"

    def test_a_misspelled_key_is_reported_rather_than_silently_defaulted(self):
        data = copy.deepcopy(_valid_chargen_parameters_data())
        data["terms"]["cp"] = data["terms"].pop("cap")
        parameters, problems = parse_chargen_parameters(data, "chargen-parameters.toml")
        assert parameters is None
        locations = {p.location for p in problems}
        assert "terms.cp" in locations
        assert "terms.cap" in locations

    @pytest.mark.parametrize("group", list(dict.fromkeys(g for g, _, _ in _CHARGEN_SCALARS)))
    def test_every_group_is_a_closed_key_set(self, group):
        data = copy.deepcopy(_valid_chargen_parameters_data())
        data[group]["unexpected-extra-key"] = 1
        parameters, problems = parse_chargen_parameters(data, "chargen-parameters.toml")
        assert parameters is None
        assert any(p.location == f"{group}.unexpected-extra-key" for p in problems)

    def test_unrecognized_top_level_key_is_a_problem(self):
        data = copy.deepcopy(_valid_chargen_parameters_data())
        data["extra"] = "nope"
        parameters, problems = parse_chargen_parameters(data, "chargen-parameters.toml")
        assert parameters is None
        assert any(p.location == "extra" for p in problems)

    def test_boolean_where_integer_expected_is_a_type_problem(self):
        data = copy.deepcopy(_valid_chargen_parameters_data())
        data["terms"]["cap"] = True
        parameters, problems = parse_chargen_parameters(data, "chargen-parameters.toml")
        assert parameters is None
        matching = [p for p in problems if p.location == "terms.cap"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"

    def test_d66_roll_is_rejected(self):
        data = copy.deepcopy(_valid_chargen_parameters_data())
        data["continuation"]["roll"] = "d66"
        parameters, problems = parse_chargen_parameters(data, "chargen-parameters.toml")
        assert parameters is None
        assert any(p.location == "continuation.roll" for p in problems)
