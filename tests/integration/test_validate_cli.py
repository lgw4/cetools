"""`cetools validate` with no argument (contracts/cli.md, SC-003, SC-010).

An invalid outcome here is produced by substituting `cetools.cli.validate_rules`
rather than by corrupting an installed file. The `PATH` argument itself is
covered separately in `tests/integration/test_overrides.py` (T045, T048).
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

# Sorted by (file, location), as `validate_rules` would return them, and
# worded as it really words them.
#
# These were hand-written from the worked example in contracts/cli.md, which
# had drifted from the code: the fixtures pinned the *contract's* wording and
# the loader emitted something else, so neither side checked the other and
# four documented example lines were lines no run could produce.
# `test_the_fixture_wording_is_the_wording_the_loader_emits` below now closes
# that loop by producing the same four problems through `validate_rules`.
_FOUR_PROBLEMS = (
    ValidationProblem(
        file="navy.toml",
        location="mustering-out.chash",
        found="unrecognized key 'chash'",
        expected="one of: benefits, cash",
    ),
    ValidationProblem(
        file="navy.toml",
        location="tables.service.entries[0]",
        found="Vac Suit",
        expected="a name in the skills registry",
    ),
    ValidationProblem(
        file="navy.toml",
        location="throws.survival.target",
        found="a string",
        expected="an integer",
    ),
    ValidationProblem(
        file="skills.toml",
        location="skills",
        found="an empty table",
        expected="at least one entry",
    ),
)


def _invalid_report(path=None) -> ValidationReport:
    return ValidationReport(provenance=_PACKAGED, file_count=5, problems=_FOUR_PROBLEMS)


def _valid_report(path=None) -> ValidationReport:
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


def test_validate_packaged_set_reports_twenty_six_files():
    # Four singleton files, six universal chargen tables, eight careers, and
    # eight name tables (003-npc-generator, research R6).
    result = runner.invoke(app, ["validate", "--json"])
    payload = json.loads(result.stdout)
    assert payload["file_count"] == 26


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


def test_the_fixture_wording_is_the_wording_the_loader_emits(tmp_path):
    """Produce the same four problems through the real loader and compare.

    Without this the fixtures above are a second, independent transcription of
    the contract, and a transcription that agrees with nothing is what let the
    worked examples in contracts/cli.md and contracts/json-output.md go stale:
    four of the five showed text no run could produce, and every test that
    might have noticed was asserting against the same stale text.
    """
    from pathlib import Path

    from cetools.rules import validate_rules

    data = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data"
    navy = (data / "careers" / "navy.toml").read_text(encoding="utf-8")
    skills = (data / "registries" / "skills.toml").read_text(encoding="utf-8")

    (tmp_path / "navy.toml").write_text(
        navy.replace('"Comms"', '"Vac Suit"', 1)
        .replace("[mustering-out]\n", "[mustering-out]\nchash = 5\n")
        .replace(
            '[throws.survival]\ncharacteristic = "INT"\ntarget = 5\n',
            '[throws.survival]\ncharacteristic = "INT"\ntarget = "five"\n',
        ),
        encoding="utf-8",
    )
    (tmp_path / "skills.toml").write_text(
        skills.split("[skills]")[0] + "[skills]\n", encoding="utf-8"
    )

    emitted = {(p.file, p.location): p for p in validate_rules(tmp_path).problems}
    for expected in _FOUR_PROBLEMS:
        key = (expected.file, expected.location)
        assert key in emitted, sorted(emitted)
        assert emitted[key] == expected


def test_validate_help_lists_exactly_its_own_options(help_text, options_in_help):
    assert "PATH" in help_text(["validate"])
    assert options_in_help(["validate"]) == {"--json", "--help"}


def test_validate_path_carries_a_help_string(help_text):
    # contracts/cli.md requires `validate` and `--rules-data` to carry help
    # strings, and the two help tests assert only the option-name *set*, so
    # `help=None` on either left 628 tests passing while the screen listed a
    # bare metavar with nothing said about it. Rich wraps inside its box, so
    # the text is matched in fragments rather than as one line.
    plain = " ".join(help_text(["validate"]).split())
    assert "Optional override location" in plain
    assert "validate the packaged data set" in plain


def test_the_top_level_help_describes_the_validate_command(help_text):
    plain = " ".join(help_text([]).split())
    assert "validate" in plain
