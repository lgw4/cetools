from cetools.chargen import (
    AgingTable,
    BackgroundSkills,
    DraftTable,
    MishapTable,
    parse_aging_table,
    parse_background_skills,
    parse_draft_table,
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
