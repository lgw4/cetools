"""Direct tests of the shared field-checking vocabulary
(contracts/schema-vocabulary.md, 006-validation-vocabulary). Written before
`schema.py` existed (FR-018): each case transcribes one row of one table in
the contract, so the contract stays the single place a rule about a check's
wording is stated.
"""

from cetools.errors import ValidationProblem
from cetools.schema import (
    optional_bool,
    require_bool,
    require_dict,
    require_int,
    require_roll,
    require_string,
    unrecognized_key_problems,
)


class TestRequireInt:
    def test_absent_key_is_missing(self):
        problems: list[ValidationProblem] = []
        result = require_int({}, "target", "f.toml", "target", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="target", found="missing", expected="an integer"
            )
        ]

    def test_a_bool_is_not_an_integer(self):
        problems: list[ValidationProblem] = []
        result = require_int({"target": True}, "target", "f.toml", "target", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="target", found="a boolean", expected="an integer"
            )
        ]

    def test_a_non_int_value_is_a_type_problem(self):
        problems: list[ValidationProblem] = []
        result = require_int({"target": "6"}, "target", "f.toml", "target", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="target", found="a string", expected="an integer"
            )
        ]

    def test_no_minimum_accepts_any_int(self):
        problems: list[ValidationProblem] = []
        result = require_int({"target": -5}, "target", "f.toml", "target", problems)
        assert result == -5
        assert problems == []

    def test_below_a_minimum_of_one_is_a_positive_integer(self):
        problems: list[ValidationProblem] = []
        result = require_int({"target": 0}, "target", "f.toml", "target", problems, minimum=1)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="target", found="0", expected="a positive integer"
            )
        ]

    def test_below_a_minimum_other_than_one_uses_the_notation_wording(self):
        problems: list[ValidationProblem] = []
        result = require_int({"target": -1}, "target", "f.toml", "target", problems, minimum=0)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="target", found="-1", expected="an integer >= 0"
            )
        ]

    def test_at_or_above_the_minimum_is_accepted(self):
        problems: list[ValidationProblem] = []
        result = require_int({"target": 1}, "target", "f.toml", "target", problems, minimum=1)
        assert result == 1
        assert problems == []


class TestRequireString:
    def test_absent_key_is_missing(self):
        problems: list[ValidationProblem] = []
        result = require_string({}, "name", "f.toml", "name", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="name", found="missing", expected="a non-empty string"
            )
        ]

    def test_an_empty_string_is_rejected(self):
        problems: list[ValidationProblem] = []
        result = require_string({"name": ""}, "name", "f.toml", "name", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml",
                location="name",
                found="an empty string",
                expected="a non-empty string",
            )
        ]

    def test_a_non_str_value_is_a_type_problem(self):
        problems: list[ValidationProblem] = []
        result = require_string({"name": 5}, "name", "f.toml", "name", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="name", found="an integer", expected="a non-empty string"
            )
        ]

    def test_a_non_empty_string_is_accepted(self):
        problems: list[ValidationProblem] = []
        result = require_string({"name": "Agent"}, "name", "f.toml", "name", problems)
        assert result == "Agent"
        assert problems == []


class TestRequireBool:
    def test_absent_key_is_missing(self):
        problems: list[ValidationProblem] = []
        result = require_bool({}, "flag", "f.toml", "flag", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="flag", found="missing", expected="a boolean"
            )
        ]

    def test_a_non_bool_value_is_a_type_problem(self):
        problems: list[ValidationProblem] = []
        result = require_bool({"flag": 1}, "flag", "f.toml", "flag", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="flag", found="an integer", expected="a boolean"
            )
        ]

    def test_a_bool_is_accepted(self):
        problems: list[ValidationProblem] = []
        result = require_bool({"flag": True}, "flag", "f.toml", "flag", problems)
        assert result is True
        assert problems == []


class TestRequireRoll:
    def test_absent_key_is_missing_and_still_expects_a_string(self):
        # FR-010a: this row is deliberately not swept into the "a non-empty
        # string" unification `require_string`'s absent-key row gets.
        problems: list[ValidationProblem] = []
        result = require_roll({}, "roll", "f.toml", "roll", problems)
        assert result is None
        assert problems == [
            ValidationProblem(file="f.toml", location="roll", found="missing", expected="a string")
        ]

    def test_a_non_str_value_is_a_type_problem(self):
        problems: list[ValidationProblem] = []
        result = require_roll({"roll": 6}, "roll", "f.toml", "roll", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="roll", found="an integer", expected="a string"
            )
        ]

    def test_d66_is_rejected(self):
        problems: list[ValidationProblem] = []
        result = require_roll({"roll": "d66"}, "roll", "f.toml", "roll", problems)
        assert result is None
        assert len(problems) == 1
        assert problems[0].found == "'d66'"
        assert "two-digit table die" in problems[0].expected

    def test_valid_notation_is_accepted(self):
        problems: list[ValidationProblem] = []
        result = require_roll({"roll": "2d6"}, "roll", "f.toml", "roll", problems)
        assert result == "2d6"
        assert problems == []


class TestRequireDict:
    def test_none_is_missing(self):
        # New to the named helper (contracts/schema-vocabulary.md): three of
        # the inline sites it absorbs distinguish "missing" from "wrong
        # type", and a merge that dropped this row would have silently
        # downgraded them to "NoneType".
        problems: list[ValidationProblem] = []
        result = require_dict(None, "f.toml", "task", "a [task] table", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="task", found="missing", expected="a [task] table"
            )
        ]

    def test_a_non_dict_value_is_a_type_problem(self):
        problems: list[ValidationProblem] = []
        result = require_dict("oops", "f.toml", "task", "a [task] table", problems)
        assert result is None
        assert problems == [
            ValidationProblem(
                file="f.toml", location="task", found="a string", expected="a [task] table"
            )
        ]

    def test_a_dict_is_accepted(self):
        problems: list[ValidationProblem] = []
        result = require_dict({"roll": "2d6"}, "f.toml", "task", "a [task] table", problems)
        assert result == {"roll": "2d6"}
        assert problems == []


class TestOptionalBool:
    def test_absent_key_reports_nothing_and_returns_the_default(self):
        problems: list[ValidationProblem] = []
        result = optional_bool({}, "always-available", "f.toml", "always-available", problems)
        assert result is False
        assert problems == []

    def test_absent_key_returns_a_non_default(self):
        problems: list[ValidationProblem] = []
        result = optional_bool(
            {}, "always-available", "f.toml", "always-available", problems, default=True
        )
        assert result is True
        assert problems == []

    def test_a_non_bool_value_reports_a_problem_and_still_returns_the_default(self):
        problems: list[ValidationProblem] = []
        result = optional_bool(
            {"always-available": "yes"},
            "always-available",
            "f.toml",
            "always-available",
            problems,
        )
        assert result is False
        assert problems == [
            ValidationProblem(
                file="f.toml",
                location="always-available",
                found="a string",
                expected="a boolean",
            )
        ]

    def test_a_bool_value_is_returned_and_reports_nothing(self):
        problems: list[ValidationProblem] = []
        result = optional_bool(
            {"always-available": True}, "always-available", "f.toml", "always-available", problems
        )
        assert result is True
        assert problems == []


class TestUnrecognizedKeyProblems:
    def test_every_key_admitted_returns_the_empty_list(self):
        problems = unrecognized_key_problems({"name": "Agent"}, frozenset({"name"}), "f.toml")
        assert problems == []

    def test_one_problem_per_unadmitted_key_sorted_by_key_name(self):
        problems = unrecognized_key_problems(
            {"zeta": 1, "alpha": 2, "name": "Agent"}, frozenset({"name"}), "f.toml"
        )
        assert [p.location for p in problems] == ["alpha", "zeta"]

    def test_expected_names_the_sorted_admitted_keys(self):
        problems = unrecognized_key_problems({"extra": 1}, frozenset({"beta", "alpha"}), "f.toml")
        assert len(problems) == 1
        assert problems[0].found == "unrecognized key 'extra'"
        assert problems[0].expected == "one of: alpha, beta"

    def test_prefix_is_applied_to_the_location(self):
        problems = unrecognized_key_problems({"extra": 1}, frozenset({"roll"}), "f.toml", "task.")
        assert problems[0].location == "task.extra"
