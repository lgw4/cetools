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
import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cetools.cli import app
from cetools.dice import Roller
from cetools.errors import RulesDataError
from cetools.names import roll_name
from cetools.rules import load_rules, validate_rules

runner = CliRunner()

NAVY = (
    Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"
).read_text(encoding="utf-8")

_NAMES_DIR = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "names"
SURNAMES_EUROPE = (_NAMES_DIR / "surnames-europe.toml").read_text(encoding="utf-8")

_COMMISSION_BLOCK = '[throws.commission]\ncharacteristic = "SOC"\ntarget = 7\ndice = "2d6"\n\n'

# A career the packaged data set does not ship, reusing Drifter's skills and
# benefits so every name it references already resolves against the
# packaged registries (FR-030, FR-031).
_RAIDERS_CAREER = """\
schema = "career"
schema-version = 4

name = "Raiders"
medical-tier = "fringe"

[throws.qualification]
characteristic = "END"
target = 3
dice = "2d6"

[throws.survival]
characteristic = "END"
target = 5
dice = "2d6"

[throws.re-enlistment]
target = 5
dice = "2d6"

[tables.personal]
entries = ["STR +1", "DEX +1", "END +1", "SOC -1", "Streetwise", "Carousing"]

[tables.service]
entries = ["Carousing", "Gambling", "Recon", "Broker", "Streetwise", "Survival"]

[tables.specialist]
entries = ["Gambling", "Jack-of-All-Trades", "Melee Combat", "Recon", "Broker", "Streetwise"]

[tables.advanced-education]
requires = "EDU 6+"
entries = ["Admin", "Advocate", "Broker", "Electronics", "Medicine", "Navigation"]

[[ladders]]
name = "raiders"
role = "entry"
ranks = [
  { rank = 0, title = "Raider" },
]

[mustering-out]
cash = [1000, 1000, 2000, 2000, 5000, 5000]
benefits = ["Low Passage", "Weapon", "Ship Share", "Mid Passage", "SOC -1", "Low Passage"]
"""


def _toml_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _surname_table_text(region: str, source: str, names: list[str]) -> str:
    entries = ", ".join(f'{{ name = "{name}" }}' for name in names)
    return (
        'schema = "surnames"\n'
        "schema-version = 1\n\n"
        f'region = "{_toml_escape(region)}"\n'
        f'source = "{_toml_escape(source)}"\n'
        f"names = [{entries}]\n"
    )


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


@pytest.mark.needs_posix_special_files
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


# --- npc: FR-058, an override's provenance always appears --------------------


def test_a_career_the_packaged_set_does_not_ship_can_be_entered_and_is_reported_as_added(
    tmp_path,
):
    (tmp_path / "raiders.toml").write_text(_RAIDERS_CAREER, encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "npc",
            "--rules-data",
            str(tmp_path),
            "--seed",
            "raiders-added",
            "--count",
            "150",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    files = payload["provenance"]["files"]
    assert len(files) == 1
    assert files[0]["file"] == "raiders.toml"
    assert files[0]["disposition"] == "added"

    entered = {
        service["career"]
        for character in payload["characters"]
        for service in character["careers"]
    }
    assert "Raiders" in entered


def test_a_replaced_file_is_reported_as_replaced_on_stderr_in_text_mode(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace("target = 5", "target = 9", 1), encoding="utf-8")

    result = runner.invoke(app, ["npc", "--rules-data", str(tmp_path), "--seed", "session-alpha"])

    assert result.exit_code == 0
    assert "Rules: overridden" in result.stderr
    assert "navy.toml" in result.stderr
    assert "replaced" in result.stderr


def test_an_overrides_provenance_appears_in_document_under_json(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace("target = 5", "target = 9", 1), encoding="utf-8")

    result = runner.invoke(
        app, ["npc", "--rules-data", str(tmp_path), "--seed", "session-alpha", "--json"]
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["provenance"]["source"] == "overridden"
    assert payload["provenance"]["files"][0]["file"] == "navy.toml"
    assert payload["provenance"]["files"][0]["disposition"] == "replaced"


# --- name-table overrides: FR-043f, FR-043i, FR-042 --------------------------


def test_replacing_a_shipped_region_leaves_the_weighting_unchanged(tmp_path):
    original = tomllib.loads(SURNAMES_EUROPE)
    shrunk_names = [entry["name"] for entry in original["names"][:5]]
    override = tmp_path / "surnames-europe.toml"
    override.write_text(
        _surname_table_text(original["region"], original["source"], shrunk_names),
        encoding="utf-8",
    )

    rules = load_rules(override)
    assert len(rules.surnames) == 7  # still seven regions in force: one replaced, none added

    roller = Roller("europe-weight-check")
    counts: dict[str, int] = {}
    for _ in range(7_000):
        name = roll_name(roller, rules.given_names, rules.surnames)
        counts[name.region] = counts.get(name.region, 0) + 1

    expected_share = 1 / 7
    share = counts.get("Europe", 0) / 7_000
    assert 0.9 * expected_share <= share <= 1.1 * expected_share


def test_adding_an_eighth_region_gives_it_the_same_weight_as_each_of_the_others(tmp_path):
    override = tmp_path / "surnames-oceania.toml"
    override.write_text(
        _surname_table_text(
            "Oceania",
            "An override-added region, no part of the shipped seven.",
            [f"Name{i}" for i in range(40)],
        ),
        encoding="utf-8",
    )

    rules = load_rules(override)
    assert len(rules.surnames) == 8

    roller = Roller("oceania-weight-check")
    counts: dict[str, int] = {}
    for _ in range(8_000):
        name = roll_name(roller, rules.given_names, rules.surnames)
        counts[name.region] = counts.get(name.region, 0) + 1

    expected_share = 1 / 8
    for region, count in counts.items():
        share = count / 8_000
        assert 0.9 * expected_share <= share <= 1.1 * expected_share, (region, share)


def test_neither_the_sixty_forty_floors_nor_either_designation_is_imposed_on_an_override(
    tmp_path,
):
    (tmp_path / "surnames-oceania.toml").write_text(
        _surname_table_text(
            "Oceania",
            "Two entries, well under the shipped forty-entry floor.",
            ["Aroha", "Manaia"],
        ),
        encoding="utf-8",
    )
    (tmp_path / "given-names.toml").write_text(
        'schema = "given-names"\n'
        "schema-version = 1\n\n"
        'source = "Three entries, well under the shipped sixty-entry floor."\n'
        'names = ["Rei", "Toa", "Nikau"]\n',
        encoding="utf-8",
    )

    report = validate_rules(tmp_path)
    assert report.valid

    rules = load_rules(tmp_path)
    assert len(rules.surnames["surnames-oceania"].names) == 2
    assert len(rules.given_names.names) == 3
