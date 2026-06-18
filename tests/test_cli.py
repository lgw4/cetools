from unittest.mock import patch

from typer.testing import CliRunner

from cetools.cli.main import app
from cetools.engine.models import Benefit, Character, GenerationFailure

runner = CliRunner()


def _make_character() -> Character:
    return Character(
        characteristics={
            "Strength": 7,
            "Dexterity": 10,
            "Endurance": 6,
            "Intelligence": 11,
            "Education": 8,
            "Social Standing": 5,
        },
        upp="7A6B85",
        age=46,
        career="Navy",
        rank=6,
        rank_title="Commodore",
        terms_served=7,
        skills={"Navigation": 2, "Zero-G": 1},
        benefits=[Benefit(kind="cash", cash_amount=10000)],
        pension=14000,
        terms=[],
    )


def test_success_exit_code_0():
    with patch("cetools.cli.character.generate_character", return_value=_make_character()):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 0


def test_success_stdout_nonempty():
    with patch("cetools.cli.character.generate_character", return_value=_make_character()):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stdout.strip()


def test_success_stderr_empty():
    with patch("cetools.cli.character.generate_character", return_value=_make_character()):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stderr == ""


def test_enlistment_failure_exit_code_1():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.generate_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 1


def test_enlistment_failure_stdout_empty():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.generate_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stdout == ""


def test_enlistment_failure_stderr_nonempty():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.generate_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stderr.strip()


def test_survival_failure_exit_code_1():
    failure = GenerationFailure(reason="Character died during term 2 survival check")
    with patch("cetools.cli.character.generate_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 1


def test_survival_failure_stdout_empty():
    failure = GenerationFailure(reason="Character died during term 2 survival check")
    with patch("cetools.cli.character.generate_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stdout == ""


def test_survival_failure_stderr_nonempty():
    failure = GenerationFailure(reason="Character died during term 2 survival check")
    with patch("cetools.cli.character.generate_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stderr.strip()


def test_failure_exit_code_propagated_from_generation_failure() -> None:
    failure = GenerationFailure(reason="Custom failure", exit_code=2)
    with patch("cetools.cli.character.generate_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 2
