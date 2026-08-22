from cetools.chargen import DraftTable, parse_draft_table
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
