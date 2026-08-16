"""`cetools validate` with no argument (contracts/cli.md, SC-003, SC-010).

The `PATH` argument lands in User Story 3 (T048); until then `validate`
always checks the packaged data set, so an invalid outcome here is produced
by substituting `cetools.cli.validate_rules` rather than by corrupting an
installed file.
"""

import json

import pytest
from typer.testing import CliRunner

from cetools.cli import app
from cetools.errors import ValidationProblem
from cetools.provenance import Provenance
from cetools.rules import ValidationReport

runner = CliRunner()

BOTH_OUTPUT_MODES = pytest.mark.parametrize("mode", [[], ["--json"]], ids=["text", "json"])

_PACKAGED = Provenance(version="2026.08.1", files=(), ignored=())

# Sorted by (file, location), as `validate_rules` would return them.
_FOUR_PROBLEMS = (
    ValidationProblem(
        file="navy.toml",
        location="mustering-out.chash",
        found="an unrecognized key 'chash'",
        expected="one of: benefits, cash",
    ),
    ValidationProblem(
        file="navy.toml",
        location="tables.service.entries[2]",
        found="unrecognized skill name 'Vac Suit'",
        expected="a name in the skills registry",
    ),
    ValidationProblem(
        file="navy.toml",
        location="throws.survival.target",
        found="str",
        expected="an integer",
    ),
    ValidationProblem(
        file="skills.toml",
        location="skills",
        found="no entries",
        expected="at least one",
    ),
)


def _invalid_report() -> ValidationReport:
    return ValidationReport(provenance=_PACKAGED, file_count=5, problems=_FOUR_PROBLEMS)


def _valid_report() -> ValidationReport:
    return ValidationReport(provenance=_PACKAGED, file_count=5, problems=())


@BOTH_OUTPUT_MODES
def test_validate_packaged_set_exits_zero(mode):
    result = runner.invoke(app, ["validate"] + mode)
    assert result.exit_code == 0
    assert result.stderr == ""


def test_validate_packaged_set_reports_valid_in_text():
    result = runner.invoke(app, ["validate"])
    assert "Rules data is valid." in result.stdout


def test_validate_packaged_set_reports_valid_in_json():
    result = runner.invoke(app, ["validate", "--json"])
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["problems"] == []


@BOTH_OUTPUT_MODES
def test_validate_reports_all_four_problems_in_one_run(monkeypatch, mode):
    monkeypatch.setattr("cetools.cli.validate_rules", _invalid_report)
    result = runner.invoke(app, ["validate"] + mode)
    assert result.exit_code == 1
    if mode:
        payload = json.loads(result.stdout)
        assert len(payload["problems"]) == 4
    else:
        for problem in _FOUR_PROBLEMS:
            assert problem.file in result.stdout
            assert problem.found in result.stdout


@BOTH_OUTPUT_MODES
def test_validate_problems_go_to_stdout_not_stderr(monkeypatch, mode):
    monkeypatch.setattr("cetools.cli.validate_rules", _invalid_report)
    result = runner.invoke(app, ["validate"] + mode)
    assert result.exit_code == 1
    assert result.stdout != ""
    assert result.stderr == ""


def test_validate_unknown_option_exits_two_with_empty_stdout():
    result = runner.invoke(app, ["validate", "--not-a-real-option"])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr != ""


@BOTH_OUTPUT_MODES
def test_validate_outcome_is_the_same_across_both_output_modes(monkeypatch, mode):
    monkeypatch.setattr("cetools.cli.validate_rules", _valid_report)
    valid_result = runner.invoke(app, ["validate"] + mode)
    assert valid_result.exit_code == 0

    monkeypatch.setattr("cetools.cli.validate_rules", _invalid_report)
    invalid_result = runner.invoke(app, ["validate"] + mode)
    assert invalid_result.exit_code == 1


def test_validate_help_lists_exactly_its_own_options():
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "--json" in result.stdout
