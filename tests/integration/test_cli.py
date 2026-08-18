import json
import re
from importlib.metadata import version

import pytest
from typer.testing import CliRunner

from cetools.cli import app

runner = CliRunner()

# Signed, because a seed may carry a minus sign (001-dice-task-engine FR-002)
# and an unsigned pattern would silently stop matching the moment one did.
_REPORTED_SEED = r"Seed:\s+([+-]?\d+)"

ROLL_AND_CHECK = pytest.mark.parametrize(
    "command", [["roll", "2d6"], ["check"]], ids=["roll", "check"]
)
BOTH_OUTPUT_MODES = pytest.mark.parametrize("mode", [[], ["--json"]], ids=["text", "json"])


def _reported_seed(stdout: str, json_mode: bool) -> str:
    if json_mode:
        return json.loads(stdout)["seed"]
    match = re.search(_REPORTED_SEED, stdout)
    assert match is not None, f"no seed in output: {stdout!r}"
    return match.group(1)


def test_roll_successful_throw_exits_zero_with_stdout():
    result = runner.invoke(app, ["roll", "2d6", "--seed", "session-alpha"])
    assert result.exit_code == 0
    assert "2d6 = 6" in result.stdout


def test_roll_d66_exits_zero_and_is_distinct_from_1d66():
    d66_result = runner.invoke(app, ["roll", "d66", "--seed", "session-alpha"])
    one_d66_result = runner.invoke(app, ["roll", "1d66", "--seed", "session-alpha"])
    assert d66_result.exit_code == 0
    assert "d66 = 15" in d66_result.stdout
    assert one_d66_result.exit_code == 0
    assert d66_result.stdout != one_d66_result.stdout


def test_roll_bad_notation_exits_one_with_stderr_and_empty_stdout():
    result = runner.invoke(app, ["roll", "7dQ", "--seed", "session-alpha"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr != ""


def test_roll_unknown_option_exits_two():
    result = runner.invoke(app, ["roll", "2d6", "--not-a-real-option"])
    assert result.exit_code == 2
    assert result.stdout == ""


def test_roll_missing_required_argument_exits_two_with_empty_stdout():
    # 001-dice-task-engine FR-031 names "missing required arguments" as a usage
    # error in its own right, and that feature's FR-027, "nothing at all is
    # written to the output stream", binds every error, not only the ones the
    # library raises.
    result = runner.invoke(app, ["roll"])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr != ""


def test_version_prints_package_version_and_exits_zero():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert version("cetools") in result.stdout


def test_roll_help_lists_exactly_its_own_options(help_text, options_in_help):
    # 001-dice-task-engine FR-025 asks for "exactly the options that subcommand
    # accepts and no others", stated as something checkable: an allowlist plus a
    # denylist would pass with a spurious option added, so the whole set is
    # compared.
    assert "NOTATION" in help_text(["roll"])
    assert options_in_help(["roll"]) == {"--seed", "--json", "--help"}


def test_roll_seed_round_trip_is_byte_identical():
    first = runner.invoke(app, ["roll", "2d6"])
    assert first.exit_code == 0
    match = re.search(_REPORTED_SEED, first.stdout)
    assert match is not None
    seed = match.group(1)

    second = runner.invoke(app, ["roll", "2d6", "--seed", seed])
    third = runner.invoke(app, ["roll", "2d6", "--seed", seed])

    # SC-004 is the promise that the *reported* seed reproduces the result it
    # was reported with, so the unseeded run is the one that has to match. The
    # second-against-third comparison only shows a given seed is deterministic.
    assert first.stdout == second.stdout
    assert second.stdout == third.stdout


@pytest.mark.parametrize("command", [["roll", "2d6"], ["check"]])
@pytest.mark.parametrize("mode", [[], ["--json"]])
def test_negative_seed_is_reported_with_its_sign(command, mode):
    result = runner.invoke(app, command + ["--seed", "-5"] + mode)
    assert result.exit_code == 0
    seed = json.loads(result.stdout)["seed"] if mode else result.stdout
    assert "-5" in seed


@pytest.mark.parametrize("command", [["roll", "2d6"], ["check"]])
@pytest.mark.parametrize("mode", [[], ["--json"]])
def test_seed_above_2_64_is_reported_in_full(command, mode):
    huge = str(2**64 + 12345)
    result = runner.invoke(app, command + ["--seed", huge] + mode)
    assert result.exit_code == 0
    seed = json.loads(result.stdout)["seed"] if mode else result.stdout
    assert huge in seed


@pytest.mark.parametrize("command", [["roll", "2d6"], ["check"]])
def test_negative_seed_does_not_alias_onto_its_positive_counterpart(command):
    negative = runner.invoke(app, command + ["--seed", "-5"])
    positive = runner.invoke(app, command + ["--seed", "5"])
    assert negative.exit_code == 0
    assert positive.exit_code == 0
    dice_line = re.compile(r"Dice:\s+(.*)")
    assert dice_line.search(negative.stdout)[1] != dice_line.search(positive.stdout)[1]


def test_check_failed_check_exits_zero():
    result = runner.invoke(app, ["check", "--difficulty", "Formidable", "--seed", "1"])
    assert result.exit_code == 0
    assert "Check: FAILURE" in result.stdout


def test_check_unknown_difficulty_exits_one_with_empty_stdout():
    result = runner.invoke(app, ["check", "--difficulty", "Trivial", "--seed", "1"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr != ""


@BOTH_OUTPUT_MODES
@pytest.mark.parametrize(
    "raw", ["cover", "label=x", "=-2"], ids=["missing-equals", "non-numeric", "empty-label"]
)
def test_check_malformed_dm_exits_two_with_empty_stdout(raw, mode):
    # 001-dice-task-engine SC-006: `--json` changes none of the exit statuses,
    # and that feature's FR-027 empty-stdout rule holds for a usage error
    # exactly as it does for a library one.
    result = runner.invoke(app, ["check", "--dm", raw, "--seed", "1"] + mode)
    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr != ""


def test_check_dm_splits_on_last_equals():
    result = runner.invoke(app, ["check", "--dm", "a=b=-2", "--seed", "1"])
    assert result.exit_code == 0
    assert "a=b" in result.stdout


def test_check_repeated_dm_preserves_supplied_order():
    result = runner.invoke(
        app,
        ["check", "--dm", "cover=-2", "--dm", "aided by ally=+1", "--seed", "session-alpha"],
    )
    assert result.exit_code == 0
    cover_index = result.stdout.index("cover")
    ally_index = result.stdout.index("aided by ally")
    assert cover_index < ally_index


def test_check_help_lists_exactly_its_own_options(help_text, options_in_help):
    assert "NOTATION" not in help_text(["check"])
    assert options_in_help(["check"]) == {
        "--difficulty",
        "--characteristic",
        "--skill",
        "--dm",
        "--seed",
        "--rules-data",
        "--json",
        "--help",
    }


def test_check_rules_data_carries_a_help_string(help_text):
    # The option-name set alone left `help=None` on `--rules-data` passing,
    # although contracts/cli.md requires it to carry one. Rich wraps inside
    # its box, so the text is matched in fragments rather than as one line.
    plain = " ".join(help_text(["check"]).split())
    assert "Override location" in plain
    assert "composed over the packaged data" in plain


def test_check_seed_round_trip_is_byte_identical():
    first = runner.invoke(app, ["check"])
    assert first.exit_code == 0
    match = re.search(_REPORTED_SEED, first.stdout)
    assert match is not None
    seed = match.group(1)

    second = runner.invoke(app, ["check", "--seed", seed])
    third = runner.invoke(app, ["check", "--seed", seed])

    # See the roll round trip: the unseeded run is the one SC-004 binds.
    assert first.stdout == second.stdout
    assert second.stdout == third.stdout


@ROLL_AND_CHECK
@BOTH_OUTPUT_MODES
def test_reported_seed_round_trips_in_both_output_modes(command, mode):
    # SC-004 binds every rendered result in *both* output modes: a seed that is
    # merely printed is not the promise. The text mode covered this already;
    # `--json` was only presence-checked, which an implementation reporting a
    # seed unrelated to its dice would pass.
    first = runner.invoke(app, command + mode)
    assert first.exit_code == 0
    seed = _reported_seed(first.stdout, bool(mode))

    second = runner.invoke(app, command + ["--seed", seed] + mode)
    assert second.exit_code == 0
    assert first.stdout == second.stdout


@ROLL_AND_CHECK
@BOTH_OUTPUT_MODES
def test_explicit_negative_seed_round_trips_in_both_output_modes(command, mode):
    first = runner.invoke(app, command + ["--seed", "-5"] + mode)
    assert first.exit_code == 0
    assert _reported_seed(first.stdout, bool(mode)) == "-5"

    second = runner.invoke(app, command + ["--seed", "-5"] + mode)
    assert first.stdout == second.stdout


def test_roll_d66_json_output_matches_text_values():
    text_result = runner.invoke(app, ["roll", "d66", "--seed", "session-alpha"])
    json_result = runner.invoke(app, ["roll", "d66", "--seed", "session-alpha", "--json"])

    assert json_result.exit_code == 0
    payload = json.loads(json_result.stdout)
    assert payload["kind"] == "roll"
    assert payload["notation"] == "d66"
    assert payload["faces"] == [1, 5]
    assert payload["modifier"] == 0
    assert payload["total"] == 15
    assert str(payload["total"]) in text_result.stdout
    assert payload["seed"] in text_result.stdout


def test_roll_json_output_parses_and_matches_text_values():
    text_result = runner.invoke(app, ["roll", "2d6+1", "--seed", "session-alpha"])
    json_result = runner.invoke(app, ["roll", "2d6+1", "--seed", "session-alpha", "--json"])

    assert json_result.exit_code == 0
    payload = json.loads(json_result.stdout)
    assert payload["kind"] == "roll"
    assert payload["notation"] == "2d6+1"
    assert payload["faces"] == [1, 5]
    assert payload["modifier"] == 1
    assert payload["total"] == 7
    assert str(payload["total"]) in text_result.stdout
    assert payload["seed"] in text_result.stdout


def test_roll_json_error_writes_nothing_to_stdout_and_plain_text_to_stderr():
    result = runner.invoke(app, ["roll", "7dQ", "--seed", "session-alpha", "--json"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr != ""
    stripped = result.stderr.strip()
    assert not (stripped.startswith("{") and stripped.endswith("}"))


def test_check_json_output_parses_and_matches_text_values():
    text_result = runner.invoke(
        app,
        [
            "check",
            "--difficulty",
            "Difficult",
            "--characteristic",
            "9",
            "--skill",
            "2",
            "--dm",
            "cover=-2",
            "--seed",
            "session-alpha",
        ],
    )
    json_result = runner.invoke(
        app,
        [
            "check",
            "--difficulty",
            "Difficult",
            "--characteristic",
            "9",
            "--skill",
            "2",
            "--dm",
            "cover=-2",
            "--seed",
            "session-alpha",
            "--json",
        ],
    )

    assert json_result.exit_code == 0
    payload = json.loads(json_result.stdout)
    assert payload["kind"] == "check"
    assert payload["faces"] == [1, 5]
    assert payload["dice_total"] == 6
    assert payload["total"] == 5
    assert payload["target"] == 8
    assert payload["success"] is False
    assert str(payload["target"]) in text_result.stdout
    assert payload["seed"] in text_result.stdout


def test_check_json_error_writes_nothing_to_stdout_and_plain_text_to_stderr():
    result = runner.invoke(app, ["check", "--difficulty", "Trivial", "--seed", "1", "--json"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr != ""
    stripped = result.stderr.strip()
    assert not (stripped.startswith("{") and stripped.endswith("}"))
