from unittest.mock import patch

from typer.testing import CliRunner

from cetools.cli.main import app
from cetools.engine.models import Benefit, Character, GenerationFailure

# Scout character for --career tests
_SCOUT_CHARACTER = Character(
    characteristics={
        "Strength": 6,
        "Dexterity": 8,
        "Endurance": 7,
        "Intelligence": 9,
        "Education": 7,
        "Social Standing": 6,
    },
    upp="687976",
    age=22,
    career="Scout",
    rank=0,
    rank_title="Scout",
    terms_served=1,
    skills={"Piloting": 1, "Navigation": 0},
    benefits=[Benefit(kind="cash", cash_amount=1000)],
    pension=0,
    terms=[],
    drafted=False,
)

runner = CliRunner()


def _make_character(drafted: bool = False) -> Character:
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
        drafted=drafted,
    )


def test_success_exit_code_0():
    with patch("cetools.cli.character.draft_character", return_value=_make_character()):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 0


def test_success_stdout_nonempty():
    with patch("cetools.cli.character.draft_character", return_value=_make_character()):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stdout.strip()


def test_success_stderr_empty():
    with patch("cetools.cli.character.draft_character", return_value=_make_character()):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stderr == ""


def test_enlistment_failure_exit_code_1():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.draft_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 1


def test_enlistment_failure_stdout_empty():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.draft_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stdout == ""


def test_enlistment_failure_stderr_nonempty():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.draft_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stderr.strip()


def test_survival_failure_exit_code_1():
    failure = GenerationFailure(reason="Character died during term 2 survival check")
    with patch("cetools.cli.character.draft_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 1


def test_survival_failure_stdout_empty():
    failure = GenerationFailure(reason="Character died during term 2 survival check")
    with patch("cetools.cli.character.draft_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stdout == ""


def test_survival_failure_stderr_nonempty():
    failure = GenerationFailure(reason="Character died during term 2 survival check")
    with patch("cetools.cli.character.draft_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.stderr.strip()


def test_failure_exit_code_propagated_from_generation_failure() -> None:
    failure = GenerationFailure(reason="Custom failure", exit_code=2)
    with patch("cetools.cli.character.draft_character", return_value=failure):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 2


# --- T018: CLI draft default ---


def test_cli_no_career_generates_drafted_character() -> None:
    drafted_char = _make_character(drafted=True)
    with patch("cetools.cli.character.draft_character", return_value=drafted_char):
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 0
    assert "(Drafted)" in result.stdout


def test_cli_no_career_career_line_contains_drafted() -> None:
    drafted_char = _make_character(drafted=True)
    with patch("cetools.cli.character.draft_character", return_value=drafted_char):
        result = runner.invoke(app, ["character", "generate"])
    career_line = next(ln for ln in result.stdout.splitlines() if "Navy" in ln)
    assert "(Drafted)" in career_line


# --- T022: Named --career paths ---


def test_career_scout_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate_career_character",
        return_value=_SCOUT_CHARACTER,
    ):
        result = runner.invoke(app, ["character", "generate", "--career", "scout"])
    assert result.exit_code == 0


def test_career_scout_no_drafted_marker() -> None:
    with patch(
        "cetools.cli.character.generate_career_character",
        return_value=_SCOUT_CHARACTER,
    ):
        result = runner.invoke(app, ["character", "generate", "--career", "scout"])
    assert "(Drafted)" not in result.stdout


def test_career_navy_exits_0() -> None:
    navy_char = _make_character(drafted=False)
    with patch(
        "cetools.cli.character.generate_career_character",
        return_value=navy_char,
    ):
        result = runner.invoke(app, ["character", "generate", "--career", "navy"])
    assert result.exit_code == 0


def test_career_navy_no_drafted_marker() -> None:
    navy_char = _make_character(drafted=False)
    with patch(
        "cetools.cli.character.generate_career_character",
        return_value=navy_char,
    ):
        result = runner.invoke(app, ["character", "generate", "--career", "navy"])
    assert "(Drafted)" not in result.stdout


# --- T023: Unrecognized career ---


def test_career_unknown_exits_1() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "marine"])
    assert result.exit_code == 1


def test_career_unknown_stderr_message_exact() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "marine"])
    assert result.stderr.strip() == "Unknown career 'marine'. Valid careers: navy, scout"


def test_career_unknown_original_value_in_message() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "Marine"])
    assert "Marine" in result.stderr


# --- T024: Input normalization ---


def test_career_title_case_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate_career_character",
        return_value=_SCOUT_CHARACTER,
    ):
        result = runner.invoke(app, ["character", "generate", "--career", "Scout"])
    assert result.exit_code == 0


def test_career_upper_case_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate_career_character",
        return_value=_SCOUT_CHARACTER,
    ):
        result = runner.invoke(app, ["character", "generate", "--career", "SCOUT"])
    assert result.exit_code == 0


def test_career_with_whitespace_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate_career_character",
        return_value=_SCOUT_CHARACTER,
    ):
        result = runner.invoke(app, ["character", "generate", "--career", "  scout  "])
    assert result.exit_code == 0
