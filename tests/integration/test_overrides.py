"""A house rule reaching a result: an overridden career throw reaches the
loaded data and the command line alike, a value the override omits is
absent rather than inherited from the packaged file it replaces, every file
the override does not contain still comes from the packaged data, an
unrecognized name in an override file fails exactly as it would in a shipped
file, and an override file carries no licensing obligation (SC-005, SC-006,
FR-030, FR-031, FR-046).
"""

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cetools.cli import app
from cetools.errors import RulesDataError
from cetools.rules import load_rules, validate_rules

runner = CliRunner()

NAVY = (
    Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"
).read_text(encoding="utf-8")

_COMMISSION_BLOCK = '[throws.commission]\ncharacteristic = "SOC"\ntarget = 7\n\n'


def test_an_overridden_survival_throw_reaches_the_loaded_career(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace("target = 5", "target = 9", 1), encoding="utf-8")
    rules = load_rules(override)
    assert rules.careers["navy"].throws["survival"].target == 9


def test_an_overridden_survival_throw_reaches_the_check_command(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace("target = 5", "target = 9", 1), encoding="utf-8")
    result = runner.invoke(app, ["check", "--rules-data", str(tmp_path), "--seed", "1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provenance"]["source"] == "overridden"
    files = payload["provenance"]["files"]
    assert len(files) == 1
    assert files[0]["file"] == "navy.toml"
    assert files[0]["disposition"] == "replaced"
    assert files[0]["fingerprint"].startswith("sha256:")


def test_validate_accepts_the_same_override_location(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace("target = 5", "target = 9", 1), encoding="utf-8")
    result = runner.invoke(app, ["validate", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["provenance"]["files"][0]["disposition"] == "replaced"


@pytest.mark.parametrize("command", [["check", "--rules-data"], ["validate"]])
def test_a_missing_override_location_is_a_usage_error(tmp_path, command):
    missing = tmp_path / "nope"
    result = runner.invoke(app, [*command, str(missing)])
    assert result.exit_code == 2
    assert result.stdout == ""


@pytest.mark.parametrize("command", [["check", "--rules-data"], ["validate"]])
def test_an_override_location_that_is_neither_file_nor_directory_is_a_usage_error(
    tmp_path, command
):
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    result = runner.invoke(app, [*command, str(fifo)])
    assert result.exit_code == 2
    assert result.stdout == ""


@pytest.mark.parametrize("command", [["check", "--rules-data"], ["validate"]])
def test_an_empty_override_location_is_a_usage_error(command):
    # `Path("")` is `Path(".")`, the ordinary shell mistake of an unset
    # variable in `--rules-data "$DIR"` (T137).
    result = runner.invoke(app, [*command, ""])
    assert result.exit_code == 2
    assert result.stdout == ""


def test_a_value_omitted_from_the_override_is_absent_not_inherited(tmp_path):
    assert _COMMISSION_BLOCK in NAVY
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace(_COMMISSION_BLOCK, "", 1), encoding="utf-8")
    rules = load_rules(override)
    assert "commission" not in rules.careers["navy"].throws
    assert "survival" in rules.careers["navy"].throws


def test_every_file_the_override_does_not_contain_still_comes_from_the_packaged_data(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace("target = 5", "target = 9", 1), encoding="utf-8")
    packaged = load_rules()
    overridden = load_rules(override)
    assert overridden.characteristics == packaged.characteristics
    assert overridden.skills == packaged.skills
    assert overridden.benefits == packaged.benefits
    assert overridden.task_parameters == packaged.task_parameters
    assert len(overridden.provenance.files) == 1
    assert overridden.provenance.files[0].file == "navy.toml"


def test_an_unrecognized_name_in_an_override_fails_like_a_shipped_file_would(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace('"Comms"', '"Coms"', 1), encoding="utf-8")
    with pytest.raises(RulesDataError) as excinfo:
        load_rules(override)
    problems = excinfo.value.problems
    assert any(
        p.file == "navy.toml"
        and p.found == "Coms"
        and p.expected == "a name in the skills registry"
        for p in problems
    )


def test_provenance_detail_survives_on_a_failing_report(tmp_path):
    """FR-032a's bargain is that admitting an unrecognized filename, or
    letting a house rule take effect, is paid for by naming it in provenance
    — and that bargain must hold on a run that fails, not only on one that
    succeeds. Composition (`_compose`) runs before validation, so
    `provenance` is fixed before any problem is known; this pins that a
    failing `ValidationReport` still carries the files that took effect and
    the files that were passed over, which is exactly what an author
    debugging a rejected data set needs to see (FR-035, FR-032a, FR-021).
    """
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace('"Comms"', '"Coms"', 1), encoding="utf-8")
    (tmp_path / "notes.md").write_text("not rules data", encoding="utf-8")

    report = validate_rules(tmp_path)

    assert not report.valid
    assert len(report.provenance.files) == 1
    assert report.provenance.files[0].file == "navy.toml"
    assert report.provenance.files[0].disposition.value == "replaced"
    assert report.provenance.ignored == ("notes.md",)


@pytest.mark.parametrize("mode", [[], ["--json"]], ids=["text", "json"])
def test_check_reports_every_problem_of_a_failed_load_on_stderr(tmp_path, mode):
    """The failed-load reporting path of `check`, which nothing exercised: the
    exit-1 cases elsewhere all reach `TaskError` through `--difficulty
    Trivial`, and the override cases cover only the usage-error path. Two
    independent mutations survived — printing to stdout, which breaks
    Constitution II's stream split, and collapsing the branch to
    `typer.echo(str(exc))`, which discards every problem FR-021 collected and
    leaves a bare summary in place of the form contracts/cli.md fixes.
    """
    broken = NAVY.replace('"Comms"', '"Coms"', 1).replace(
        '[throws.survival]\ncharacteristic = "INT"\ntarget = 5\n',
        '[throws.survival]\ncharacteristic = "INT"\ntarget = "five"\n',
    )
    (tmp_path / "navy.toml").write_text(broken, encoding="utf-8")
    expected = validate_rules(tmp_path).problems
    assert len(expected) >= 2

    result = runner.invoke(app, ["check", "--rules-data", str(tmp_path), "--seed", "1"] + mode)
    assert result.exit_code == 1
    assert result.stdout == ""
    lines = result.stderr.splitlines()
    assert lines == [
        f"{p.file}:{p.location}: found {p.found}; expected {p.expected}" for p in expected
    ]


def test_a_failed_check_load_produces_no_result_at_all(tmp_path):
    # FR-025: a check that cannot trust its rules data produces no result
    # rather than a result with a caveat, in both output modes.
    (tmp_path / "navy.toml").write_text(NAVY.replace('"Comms"', '"Coms"', 1), encoding="utf-8")
    for mode in ([], ["--json"]):
        result = runner.invoke(app, ["check", "--rules-data", str(tmp_path), "--seed", "1"] + mode)
        assert result.exit_code == 1
        assert result.stdout == ""
        assert "Check:" not in result.stderr


def test_an_override_file_carries_no_licensing_obligation(tmp_path):
    without_header_comment = "\n".join(
        line for line in NAVY.splitlines() if not line.startswith("#")
    ).lstrip("\n")
    assert "Open Game Content" not in without_header_comment
    override = tmp_path / "navy.toml"
    override.write_text(without_header_comment, encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
