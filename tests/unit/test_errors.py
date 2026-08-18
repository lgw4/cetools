import dataclasses

import pytest

import cetools
from cetools.errors import (
    CetoolsError,
    DiceError,
    RulesDataError,
    TaskError,
    ValidationProblem,
)


def test_cetools_error_subclasses_exception():
    assert issubclass(CetoolsError, Exception)


def test_dice_error_subclasses_cetools_error():
    assert issubclass(DiceError, CetoolsError)


def test_rules_data_error_subclasses_cetools_error():
    assert issubclass(RulesDataError, CetoolsError)


def test_task_error_subclasses_cetools_error():
    assert issubclass(TaskError, CetoolsError)


def test_all_four_errors_importable_from_cetools():
    assert cetools.CetoolsError is CetoolsError
    assert cetools.DiceError is DiceError
    assert cetools.RulesDataError is RulesDataError
    assert cetools.TaskError is TaskError


class TestValidationProblem:
    def test_fields(self):
        problem = ValidationProblem(
            file="navy.toml",
            location="tables.service.entries[2]",
            found="INT 4+",
            expected="a skill table entry",
        )
        assert problem.file == "navy.toml"
        assert problem.location == "tables.service.entries[2]"
        assert problem.found == "INT 4+"
        assert problem.expected == "a skill table entry"

    def test_is_frozen(self):
        problem = ValidationProblem(file="navy.toml", location="", found="x", expected="y")
        with pytest.raises(dataclasses.FrozenInstanceError):
            problem.file = "other.toml"

    def test_is_slotted(self):
        problem = ValidationProblem(file="navy.toml", location="", found="x", expected="y")
        assert not hasattr(problem, "__dict__")

    def test_location_is_empty_string_for_file_as_a_whole(self):
        problem = ValidationProblem(
            file="navy.toml", location="", found="invalid TOML", expected="well-formed TOML"
        )
        assert problem.location == ""

    def test_location_defaults_to_empty_string(self):
        problem = ValidationProblem(file="navy.toml", found="invalid TOML", expected="TOML")
        assert problem.location == ""

    @pytest.mark.parametrize(
        ("a", "b"),
        [
            (
                ValidationProblem(file="a.toml", location="x", found="1", expected="2"),
                ValidationProblem(file="b.toml", location="a", found="1", expected="2"),
            ),
            (
                ValidationProblem(file="navy.toml", location="a", found="1", expected="2"),
                ValidationProblem(file="navy.toml", location="b", found="1", expected="2"),
            ),
        ],
    )
    def test_sorts_by_file_then_location(self, a, b):
        assert sorted([b, a]) == [a, b]

    def test_equal_field_values_are_equal(self):
        a = ValidationProblem(file="navy.toml", location="x", found="1", expected="2")
        b = ValidationProblem(file="navy.toml", location="x", found="1", expected="2")
        assert a == b


class TestRulesDataErrorProblems:
    def test_message_only_construction_has_empty_problems(self):
        error = RulesDataError("no characteristic band covers score 47")
        assert str(error) == "no characteristic band covers score 47"
        assert error.problems == ()

    def test_construction_with_problems(self):
        problems = (
            ValidationProblem(file="navy.toml", location="", found="x", expected="y"),
            ValidationProblem(
                file="skills.toml", location="skills.Pilot", found="1", expected="[]"
            ),
        )
        error = RulesDataError("2 problems found", problems=problems)
        assert error.problems == problems

    def test_problems_defaults_to_empty_tuple(self):
        error = RulesDataError("boom")
        assert error.problems == ()

    def test_problems_is_a_tuple(self):
        error = RulesDataError(
            "1 problem found",
            problems=[ValidationProblem(file="navy.toml", location="", found="x", expected="y")],
        )
        assert isinstance(error.problems, tuple)
