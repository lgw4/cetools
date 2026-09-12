"""Direct tests of the shared field-checking vocabulary
(contracts/schema-vocabulary.md, 006-validation-vocabulary), rewritten to the
method call shape `ParseContext` gives it (contracts/parse-context.md,
007-parse-context-carrier). Each case keeps transcribing one row of one
table in the 006 contract; row-for-row parity with that contract is the
FR-026 criterion, and the `require_list` table added below comes from
007's own contract, since 006 never defined that check.
"""

from cetools.errors import ValidationProblem
from cetools.schema import ParseContext


class TestRequireInt:
    def test_absent_key_is_missing(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_int({}, "target")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="target", found="missing", expected="an integer"
            ),
        )

    def test_a_bool_is_not_an_integer(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_int({"target": True}, "target")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="target", found="a boolean", expected="an integer"
            ),
        )

    def test_a_non_int_value_is_a_type_problem(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_int({"target": "6"}, "target")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="target", found="a string", expected="an integer"
            ),
        )

    def test_no_minimum_accepts_any_int(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_int({"target": -5}, "target")
        assert result == -5
        assert ctx.problems == ()

    def test_below_a_minimum_of_one_is_a_positive_integer(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_int({"target": 0}, "target", minimum=1)
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="target", found="0", expected="a positive integer"
            ),
        )

    def test_below_a_minimum_other_than_one_uses_the_notation_wording(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_int({"target": -1}, "target", minimum=0)
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="target", found="-1", expected="an integer >= 0"
            ),
        )

    def test_at_or_above_the_minimum_is_accepted(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_int({"target": 1}, "target", minimum=1)
        assert result == 1
        assert ctx.problems == ()


class TestRequireString:
    def test_absent_key_is_missing(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_string({}, "name")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="name", found="missing", expected="a non-empty string"
            ),
        )

    def test_an_empty_string_is_rejected(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_string({"name": ""}, "name")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml",
                location="name",
                found="an empty string",
                expected="a non-empty string",
            ),
        )

    def test_a_non_str_value_is_a_type_problem(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_string({"name": 5}, "name")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="name", found="an integer", expected="a non-empty string"
            ),
        )

    def test_a_non_empty_string_is_accepted(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_string({"name": "Agent"}, "name")
        assert result == "Agent"
        assert ctx.problems == ()


class TestRequireBool:
    def test_absent_key_is_missing(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_bool({}, "flag")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="flag", found="missing", expected="a boolean"
            ),
        )

    def test_a_non_bool_value_is_a_type_problem(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_bool({"flag": 1}, "flag")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="flag", found="an integer", expected="a boolean"
            ),
        )

    def test_a_bool_is_accepted(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_bool({"flag": True}, "flag")
        assert result is True
        assert ctx.problems == ()


class TestRequireRoll:
    def test_absent_key_is_missing_and_still_expects_a_string(self):
        # FR-010a: this row is deliberately not swept into the "a non-empty
        # string" unification `require_string`'s absent-key row gets.
        ctx = ParseContext("f.toml")
        result = ctx.require_roll({}, "roll")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="roll", found="missing", expected="a string"
            ),
        )

    def test_a_non_str_value_is_a_type_problem(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_roll({"roll": 6}, "roll")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="roll", found="an integer", expected="a string"
            ),
        )

    def test_d66_is_rejected(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_roll({"roll": "d66"}, "roll")
        assert result is None
        assert len(ctx.problems) == 1
        assert ctx.problems[0].found == "'d66'"
        assert "two-digit table die" in ctx.problems[0].expected

    def test_valid_notation_is_accepted(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_roll({"roll": "2d6"}, "roll")
        assert result == "2d6"
        assert ctx.problems == ()


class TestRequireDict:
    def test_none_is_missing(self):
        # New to the named helper (contracts/schema-vocabulary.md): three of
        # the inline sites it absorbs distinguish "missing" from "wrong
        # type", and a merge that dropped this row would have silently
        # downgraded them to "NoneType".
        ctx = ParseContext("f.toml", "task")
        result = ctx.require_dict(None, expected="a [task] table")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="task", found="missing", expected="a [task] table"
            ),
        )

    def test_a_non_dict_value_is_a_type_problem(self):
        ctx = ParseContext("f.toml", "task")
        result = ctx.require_dict("oops", expected="a [task] table")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="task", found="a string", expected="a [task] table"
            ),
        )

    def test_a_dict_is_accepted(self):
        ctx = ParseContext("f.toml", "task")
        result = ctx.require_dict({"roll": "2d6"}, expected="a [task] table")
        assert result == {"roll": "2d6"}
        assert ctx.problems == ()


class TestOptionalBool:
    def test_absent_key_reports_nothing_and_returns_the_default(self):
        ctx = ParseContext("f.toml")
        result = ctx.optional_bool({}, "always-available")
        assert result is False
        assert ctx.problems == ()

    def test_absent_key_returns_a_non_default(self):
        ctx = ParseContext("f.toml")
        result = ctx.optional_bool({}, "always-available", default=True)
        assert result is True
        assert ctx.problems == ()

    def test_a_non_bool_value_reports_a_problem_and_still_returns_the_default(self):
        ctx = ParseContext("f.toml")
        result = ctx.optional_bool({"always-available": "yes"}, "always-available")
        assert result is False
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml",
                location="always-available",
                found="a string",
                expected="a boolean",
            ),
        )

    def test_a_bool_value_is_returned_and_reports_nothing(self):
        ctx = ParseContext("f.toml")
        result = ctx.optional_bool({"always-available": True}, "always-available")
        assert result is True
        assert ctx.problems == ()


class TestUnrecognizedKeys:
    def test_every_key_admitted_reports_nothing(self):
        ctx = ParseContext("f.toml")
        ctx.unrecognized_keys({"name": "Agent"}, frozenset({"name"}))
        assert ctx.problems == ()

    def test_one_problem_per_unadmitted_key_sorted_by_key_name(self):
        ctx = ParseContext("f.toml")
        ctx.unrecognized_keys({"zeta": 1, "alpha": 2, "name": "Agent"}, frozenset({"name"}))
        assert [p.location for p in ctx.problems] == ["alpha", "zeta"]

    def test_expected_names_the_sorted_admitted_keys(self):
        ctx = ParseContext("f.toml")
        ctx.unrecognized_keys({"extra": 1}, frozenset({"beta", "alpha"}))
        assert len(ctx.problems) == 1
        assert ctx.problems[0].found == "unrecognized key 'extra'"
        assert ctx.problems[0].expected == "one of: alpha, beta"

    def test_prefix_is_applied_to_the_location(self):
        ctx = ParseContext("f.toml", "task")
        ctx.unrecognized_keys({"extra": 1}, frozenset({"roll"}))
        assert ctx.problems[0].location == "task.extra"


class TestRequireList:
    """The `require_list` condition table (contracts/parse-context.md
    §`require_list`), new to this feature and absorbing fifteen hand-written
    copies of the same idiom.
    """

    def test_absent_key_is_missing(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_list({}, "names", expected="at least one entry")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml",
                location="names",
                found="missing",
                expected="at least one entry",
            ),
        )

    def test_absent_key_uses_expected_missing_when_given(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_list(
            {}, "names", expected="at least one entry", expected_missing="an array"
        )
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="names", found="missing", expected="an array"
            ),
        )

    def test_a_non_list_value_is_a_type_problem(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_list({"names": "oops"}, "names", expected="at least one entry")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml", location="names", found="a string", expected="at least one entry"
            ),
        )

    def test_an_empty_list_is_rejected_by_default(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_list({"names": []}, "names", expected="at least one entry")
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml",
                location="names",
                found="an empty array",
                expected="at least one entry",
            ),
        )

    def test_an_empty_list_uses_expected_empty_when_given(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_list(
            {"benefits": []},
            "benefits",
            expected="an array of strings with at least one entry",
            expected_empty="at least one entry",
        )
        assert result is None
        assert ctx.problems == (
            ValidationProblem(
                file="f.toml",
                location="benefits",
                found="an empty array",
                expected="at least one entry",
            ),
        )

    def test_a_non_empty_list_is_accepted(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_list({"names": ["a", "b"]}, "names", expected="at least one entry")
        assert result == ["a", "b"]
        assert ctx.problems == ()

    def test_allow_empty_accepts_an_empty_list(self):
        ctx = ParseContext("f.toml")
        result = ctx.require_list(
            {"skills.gun-combat": []},
            "skills.gun-combat",
            expected="an array of strings",
            allow_empty=True,
        )
        assert result == []
        assert ctx.problems == ()
