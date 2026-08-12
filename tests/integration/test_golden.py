from typer.testing import CliRunner

from cetools.cli import app

runner = CliRunner()


def test_roll_2d6_plus1_matches_golden_file(read_golden):
    result = runner.invoke(app, ["roll", "2d6+1", "--seed", "session-alpha"])
    assert result.exit_code == 0
    assert result.stdout == read_golden("roll_2d6_plus1.txt")


def test_roll_1d6_matches_golden_file(read_golden):
    result = runner.invoke(app, ["roll", "1d6", "--seed", "session-alpha"])
    assert result.exit_code == 0
    assert result.stdout == read_golden("roll_1d6.txt")


def test_roll_d66_matches_golden_file(read_golden):
    result = runner.invoke(app, ["roll", "d66", "--seed", "session-alpha"])
    assert result.exit_code == 0
    assert result.stdout == read_golden("roll_d66.txt")


def test_check_difficult_matches_golden_file(read_golden):
    result = runner.invoke(
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
    assert result.exit_code == 0
    assert result.stdout == read_golden("check_difficult.txt")


def test_check_unskilled_matches_golden_file(read_golden):
    result = runner.invoke(app, ["check", "--seed", "1"])
    assert result.exit_code == 0
    assert result.stdout == read_golden("check_unskilled.txt")
