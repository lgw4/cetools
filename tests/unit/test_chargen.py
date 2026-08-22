from cetools.chargen import AgingTable, DraftTable, parse_aging_table, parse_draft_table
from cetools.errors import ValidationProblem


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
