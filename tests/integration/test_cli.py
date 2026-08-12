import re
from importlib.metadata import version

from typer.testing import CliRunner

from cetools.cli import app

runner = CliRunner()


def test_roll_successful_throw_exits_zero_with_stdout():
    result = runner.invoke(app, ["roll", "2d6", "--seed", "session-alpha"])
    assert result.exit_code == 0
    assert "2d6 = 6" in result.stdout


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

    assert second.stdout == third.stdout
