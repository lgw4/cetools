import json
import re
from importlib.metadata import version

from typer.testing import CliRunner

from cetools.cli import app

runner = CliRunner()


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


def test_version_prints_package_version_and_exits_zero():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert version("cetools") in result.stdout


def test_roll_help_lists_exactly_its_own_options():
    result = runner.invoke(app, ["roll", "--help"])
    assert result.exit_code == 0
    assert "NOTATION" in result.stdout
    assert "--seed" in result.stdout
    assert "--json" in result.stdout
    for check_only_option in ("--difficulty", "--characteristic", "--skill", "--dm"):
        assert check_only_option not in result.stdout


def test_roll_seed_round_trip_is_byte_identical():
    first = runner.invoke(app, ["roll", "2d6"])
    assert first.exit_code == 0
    match = re.search(r"Seed:\s+(\d+)", first.stdout)
    assert match is not None
    seed = match.group(1)

    second = runner.invoke(app, ["roll", "2d6", "--seed", seed])
    third = runner.invoke(app, ["roll", "2d6", "--seed", seed])

    # SC-004 is the promise that the *reported* seed reproduces the result it
    # was reported with, so the unseeded run is the one that has to match. The
    # second-against-third comparison only shows a given seed is deterministic.
    assert first.stdout == second.stdout
    assert second.stdout == third.stdout


def test_check_failed_check_exits_zero():
    result = runner.invoke(app, ["check", "--difficulty", "Formidable", "--seed", "1"])
    assert result.exit_code == 0
    assert "Check: FAILURE" in result.stdout


def test_check_unknown_difficulty_exits_one_with_empty_stdout():
    result = runner.invoke(app, ["check", "--difficulty", "Trivial", "--seed", "1"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr != ""


def test_check_malformed_dm_missing_equals_exits_two():
    result = runner.invoke(app, ["check", "--dm", "cover", "--seed", "1"])
    assert result.exit_code == 2


def test_check_malformed_dm_non_numeric_value_exits_two():
    result = runner.invoke(app, ["check", "--dm", "label=x", "--seed", "1"])
    assert result.exit_code == 2


def test_check_malformed_dm_empty_label_exits_two():
    result = runner.invoke(app, ["check", "--dm", "=-2", "--seed", "1"])
    assert result.exit_code == 2


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


def test_check_help_lists_exactly_its_own_options():
    result = runner.invoke(app, ["check", "--help"])
    assert result.exit_code == 0
    for option in ("--difficulty", "--characteristic", "--skill", "--dm", "--seed", "--json"):
        assert option in result.stdout
    assert "NOTATION" not in result.stdout


def test_check_seed_round_trip_is_byte_identical():
    first = runner.invoke(app, ["check"])
    assert first.exit_code == 0
    match = re.search(r"Seed:\s+(\d+)", first.stdout)
    assert match is not None
    seed = match.group(1)

    second = runner.invoke(app, ["check", "--seed", seed])
    third = runner.invoke(app, ["check", "--seed", seed])

    # See the roll round trip: the unseeded run is the one SC-004 binds.
    assert first.stdout == second.stdout
    assert second.stdout == third.stdout


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
