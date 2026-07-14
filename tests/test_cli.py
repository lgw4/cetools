from unittest.mock import patch

from typer.testing import CliRunner

from cetools.cli.main import app
from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.generator import DRAFT, RANDOM
from cetools.engine.models import Cash, Character, GenerationFailure

_SCOUT = SCOUT_CAREER
_NAVY = NAVY_CAREER
_MARINE = MARINE_CAREER
_AEROSPACE = AEROSPACE_CAREER

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
    career=SCOUT_CAREER,
    rank=0,
    terms_served=1,
    name="Jane Doe",
    skills={"Piloting": 1, "Navigation": 0},
    benefits=[Cash(amount=1000)],
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
        career=NAVY_CAREER,
        rank=6,
        terms_served=7,
        name="Jane Doe",
        skills={"Navigation": 2, "Zero-G": 1},
        benefits=[Cash(amount=10000)],
        pension=14000,
        terms=[],
        drafted=drafted,
    )


def test_success_exit_code_0():
    with patch("cetools.cli.character.generate", return_value=_make_character()) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.exit_code == 0


def test_success_stdout_nonempty():
    with patch("cetools.cli.character.generate", return_value=_make_character()) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.stdout.strip()


def test_success_stderr_empty():
    with patch("cetools.cli.character.generate", return_value=_make_character()) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.stderr == ""


def test_enlistment_failure_exit_code_1():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.generate", return_value=failure) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.exit_code == 1


def test_enlistment_failure_stdout_empty():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.generate", return_value=failure) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.stdout == ""


def test_enlistment_failure_stderr_nonempty():
    failure = GenerationFailure(reason="Navy enlistment failed")
    with patch("cetools.cli.character.generate", return_value=failure) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.stderr.strip()


def test_survival_failure_exit_code_1():
    failure = GenerationFailure(reason="Marine enlistment failed")
    with patch("cetools.cli.character.generate", return_value=failure) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.exit_code == 1


def test_survival_failure_stdout_empty():
    failure = GenerationFailure(reason="Marine enlistment failed")
    with patch("cetools.cli.character.generate", return_value=failure) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.stdout == ""


def test_survival_failure_stderr_nonempty():
    failure = GenerationFailure(reason="Marine enlistment failed")
    with patch("cetools.cli.character.generate", return_value=failure) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.stderr.strip()


def test_failure_exit_code_propagated_from_generation_failure() -> None:
    failure = GenerationFailure(reason="Custom failure", exit_code=2)
    with patch("cetools.cli.character.generate", return_value=failure) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.exit_code == 2


# --- T018: CLI draft default ---


def test_cli_no_career_generates_character_successfully() -> None:
    drafted_char = _make_character(drafted=True)
    with patch("cetools.cli.character.generate", return_value=drafted_char) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.exit_code == 0
    assert "(Drafted)" not in result.stdout


def test_cli_no_career_career_line_omits_drafted() -> None:
    drafted_char = _make_character(drafted=True)
    with patch("cetools.cli.character.generate", return_value=drafted_char) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert mock_generate.call_args.args[0] is DRAFT
    career_line = next(ln for ln in result.stdout.splitlines() if "Navy" in ln)
    assert "(Drafted)" not in career_line


# --- T022: Named --career paths ---


def test_career_scout_exits_0() -> None:
    with patch("cetools.cli.character.generate", return_value=_SCOUT_CHARACTER) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "scout"])
    assert mock_generate.call_args.args[0] is _SCOUT
    assert result.exit_code == 0


def test_career_scout_no_drafted_marker() -> None:
    with patch("cetools.cli.character.generate", return_value=_SCOUT_CHARACTER) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "scout"])
    assert mock_generate.call_args.args[0] is _SCOUT
    assert "(Drafted)" not in result.stdout


def test_career_navy_exits_0() -> None:
    navy_char = _make_character(drafted=False)
    with patch("cetools.cli.character.generate", return_value=navy_char) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "navy"])
    assert mock_generate.call_args.args[0] is _NAVY
    assert result.exit_code == 0


def test_career_navy_no_drafted_marker() -> None:
    navy_char = _make_character(drafted=False)
    with patch("cetools.cli.character.generate", return_value=navy_char) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "navy"])
    assert mock_generate.call_args.args[0] is _NAVY
    assert "(Drafted)" not in result.stdout


# --- T023: Unrecognized career ---


def test_career_unknown_exits_1() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "smuggler"])
    assert result.exit_code == 1


def test_career_unknown_stderr_message_exact() -> None:
    # T018: updated to match the "no close match" format (canonical names, no suggestion)
    result = runner.invoke(app, ["character", "generate", "--career", "smuggler"])
    expected = (
        "Unknown career 'smuggler'. Valid careers: Aerospace System Defense, "
        "Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat, "
        "Drifter, Entertainer, Hunter, Marine, Maritime System Defense, "
        "Mercenary, Merchant, Navy, Noble, Physician, Pirate, Rogue, "
        "Scientist, Scout, Surface System Defense, Technician"
    )
    assert result.stderr.strip() == expected


def test_career_unknown_original_value_in_message() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "Smuggler"])
    assert "Smuggler" in result.stderr


# --- T024: Input normalization ---


def test_career_title_case_exits_0() -> None:
    with patch("cetools.cli.character.generate", return_value=_SCOUT_CHARACTER) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "Scout"])
    assert mock_generate.call_args.args[0] is _SCOUT
    assert result.exit_code == 0


def test_career_upper_case_exits_0() -> None:
    with patch("cetools.cli.character.generate", return_value=_SCOUT_CHARACTER) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "SCOUT"])
    assert mock_generate.call_args.args[0] is _SCOUT
    assert result.exit_code == 0


def test_career_with_whitespace_exits_0() -> None:
    with patch("cetools.cli.character.generate", return_value=_SCOUT_CHARACTER) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "  scout  "])
    assert mock_generate.call_args.args[0] is _SCOUT
    assert result.exit_code == 0


# --- T006: Aerospace System Defense CLI generation ---

_AEROSPACE_RANK_TITLES = {
    "Airman",
    "Flight Officer",
    "Flight Lieutenant",
    "Squadron Leader",
    "Wing Commander",
    "Group Captain",
    "Air Commodore",
}


def _make_aerospace_character() -> "Character":
    from cetools.engine.models import Cash, Character

    return Character(
        characteristics={
            "Strength": 7,
            "Dexterity": 9,
            "Endurance": 8,
            "Intelligence": 6,
            "Education": 7,
            "Social Standing": 5,
        },
        upp="798675",
        age=26,
        career=AEROSPACE_CAREER,
        rank=1,
        terms_served=1,
        name="Jane Doe",
        skills={"Aircraft": 1, "Electronics": 0},
        benefits=[Cash(amount=1000)],
        pension=0,
        terms=[],
        drafted=False,
    )


def test_aerospace_career_exact_name_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_aerospace_character(),
    ) as mock_generate:
        result = runner.invoke(
            app, ["character", "generate", "--career", "Aerospace System Defense"]
        )
    assert mock_generate.call_args.args[0] is _AEROSPACE
    assert result.exit_code == 0


def test_aerospace_career_exact_name_output_contains_career_name() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_aerospace_character(),
    ) as mock_generate:
        result = runner.invoke(
            app, ["character", "generate", "--career", "Aerospace System Defense"]
        )
    assert mock_generate.call_args.args[0] is _AEROSPACE
    assert "Aerospace System Defense" in result.stdout


def test_aerospace_career_output_contains_valid_rank_title() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_aerospace_character(),
    ) as mock_generate:
        result = runner.invoke(
            app, ["character", "generate", "--career", "Aerospace System Defense"]
        )
    assert mock_generate.call_args.args[0] is _AEROSPACE
    assert any(title in result.stdout for title in _AEROSPACE_RANK_TITLES)


# --- T007: Case-insensitive and hyphenated input ---


def test_aerospace_career_lowercase_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_aerospace_character(),
    ) as mock_generate:
        result = runner.invoke(
            app, ["character", "generate", "--career", "aerospace system defense"]
        )
    assert mock_generate.call_args.args[0] is _AEROSPACE
    assert result.exit_code == 0


def test_aerospace_career_uppercase_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_aerospace_character(),
    ) as mock_generate:
        result = runner.invoke(
            app, ["character", "generate", "--career", "AEROSPACE SYSTEM DEFENSE"]
        )
    assert mock_generate.call_args.args[0] is _AEROSPACE
    assert result.exit_code == 0


def test_aerospace_career_hyphenated_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_aerospace_character(),
    ) as mock_generate:
        result = runner.invoke(
            app, ["character", "generate", "--career", "aerospace-system-defense"]
        )
    assert mock_generate.call_args.args[0] is _AEROSPACE
    assert result.exit_code == 0


def test_aerospace_career_hyphenated_mixed_case_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_aerospace_character(),
    ) as mock_generate:
        result = runner.invoke(
            app, ["character", "generate", "--career", "Aerospace-System-Defense"]
        )
    assert mock_generate.call_args.args[0] is _AEROSPACE
    assert result.exit_code == 0


# --- T016: "Did you mean" suggestion for near-miss input ---


def test_career_near_miss_did_you_mean_exits_1() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "neavy"])
    assert result.exit_code == 1


def test_career_near_miss_did_you_mean_message() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "neavy"])
    assert "Unknown career 'neavy'" in result.stderr
    assert "Did you mean: Navy" in result.stderr


def test_career_near_miss_no_valid_careers_list() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "neavy"])
    assert "Valid careers:" not in result.stderr


def test_career_partial_prefix_no_did_you_mean() -> None:
    # "Aerospace" alone has similarity ~0.545 to "aerospace system defense", below
    # the cutoff=0.6 threshold, so it must fall back to the "Valid careers" list.
    result = runner.invoke(app, ["character", "generate", "--career", "Aerospace"])
    assert "Did you mean" not in result.stderr
    assert "Valid careers:" in result.stderr


# --- T017: "No close match" lists all canonical career names ---


def test_career_no_match_lists_canonical_names() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "xyzzy"])
    assert "Aerospace System Defense" in result.stderr
    assert "Marine" in result.stderr
    assert "Navy" in result.stderr
    assert "Scout" in result.stderr


def test_career_no_match_valid_careers_format() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "xyzzy"])
    expected = (
        "Unknown career 'xyzzy'. Valid careers: Aerospace System Defense, "
        "Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat, "
        "Drifter, Entertainer, Hunter, Marine, Maritime System Defense, "
        "Mercenary, Merchant, Navy, Noble, Physician, Pirate, Rogue, "
        "Scientist, Scout, Surface System Defense, Technician"
    )
    assert result.stderr.strip() == expected


def test_career_no_match_no_did_you_mean() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "xyzzy"])
    assert "Did you mean" not in result.stderr


# --- T017b: --help text enumerates canonical career names ---


def test_career_help_lists_canonical_names() -> None:
    result = runner.invoke(app, ["character", "generate", "--help"])
    # Career names may be wrapped by the terminal box renderer; check each individually.
    assert "Aerospace System" in result.output
    assert "Defense" in result.output
    assert "Marine" in result.output
    assert "Maritime" in result.output
    assert "Navy" in result.output
    assert "Scout" in result.output


# --- T006: Marine CLI generation ---

_MARINE_RANK_TITLES = {
    "Trooper",
    "Lieutenant",
    "Captain",
    "Major",
    "Lt Colonel",
    "Colonel",
    "Brigadier",
}


def _make_marine_character() -> Character:
    return Character(
        characteristics={
            "Strength": 8,
            "Dexterity": 7,
            "Endurance": 9,
            "Intelligence": 8,
            "Education": 7,
            "Social Standing": 6,
        },
        upp="879876",
        age=22,
        career=MARINE_CAREER,
        rank=0,
        terms_served=1,
        name="Jane Doe",
        skills={"Zero-G": 1, "Gun Combat": 0},
        benefits=[Cash(amount=1000)],
        pension=0,
        terms=[],
        drafted=False,
    )


def test_career_marine_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_marine_character(),
    ) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "Marine"])
    assert mock_generate.call_args.args[0] is _MARINE
    assert result.exit_code == 0


def test_career_marine_output_contains_career_name() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_marine_character(),
    ) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "Marine"])
    assert mock_generate.call_args.args[0] is _MARINE
    assert "Marine" in result.stdout


def test_career_marine_output_contains_valid_rank_title() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_marine_character(),
    ) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "Marine"])
    assert mock_generate.call_args.args[0] is _MARINE
    assert any(title in result.stdout for title in _MARINE_RANK_TITLES)


def test_career_marine_no_drafted_marker() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_marine_character(),
    ) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "Marine"])
    assert mock_generate.call_args.args[0] is _MARINE
    assert "(Drafted)" not in result.stdout


# --- T007: Marine case-insensitive input ---


def test_career_marine_lowercase_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_marine_character(),
    ) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "marine"])
    assert mock_generate.call_args.args[0] is _MARINE
    assert result.exit_code == 0


def test_career_marine_uppercase_exits_0() -> None:
    with patch(
        "cetools.cli.character.generate",
        return_value=_make_marine_character(),
    ) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "MARINE"])
    assert mock_generate.call_args.args[0] is _MARINE
    assert result.exit_code == 0


# --- T009A: "Marines" (plural, near-miss) suggests Marine ---


def test_career_marines_plural_did_you_mean_marine() -> None:
    result = runner.invoke(app, ["character", "generate", "--career", "Marines"])
    assert result.exit_code == 1
    assert result.stderr.strip() == "Unknown career 'Marines'. Did you mean: Marine?"


# --- Batch generation: --count/-n and --random ---


def test_count_generates_multiple_drafted_characters():
    with patch("cetools.cli.character.generate", return_value=_make_character()) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "-n", "3"])
    assert result.exit_code == 0
    assert mock_generate.call_count == 3
    assert all(call.args[0] is DRAFT for call in mock_generate.call_args_list)
    assert result.stdout.count("Navy (7 terms)") == 3


def test_count_with_career_generates_multiple_of_that_career():
    with patch("cetools.cli.character.generate", return_value=_SCOUT_CHARACTER) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--career", "scout", "-n", "2"])
    assert result.exit_code == 0
    assert mock_generate.call_count == 2
    assert all(call.args[0] is _SCOUT for call in mock_generate.call_args_list)
    assert result.stdout.count("Scout (1 terms)") == 2


def test_random_flag_uses_random_career_character():
    with patch("cetools.cli.character.generate", return_value=_make_character()) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--random", "-n", "2"])
    assert result.exit_code == 0
    assert mock_generate.call_count == 2
    assert all(call.args[0] is RANDOM for call in mock_generate.call_args_list)


def test_default_generate_still_single_draft():
    with patch("cetools.cli.character.generate", return_value=_make_character()) as mock_generate:
        result = runner.invoke(app, ["character", "generate"])
    assert result.exit_code == 0
    assert mock_generate.call_count == 1
    assert mock_generate.call_args.args[0] is DRAFT
    assert result.stdout.count("Navy (7 terms)") == 1


def test_career_and_random_are_mutually_exclusive():
    result = runner.invoke(app, ["character", "generate", "--career", "scout", "--random"])
    assert result.exit_code == 1
    assert "mutually exclusive" in result.stderr


def test_count_below_one_is_rejected():
    result = runner.invoke(app, ["character", "generate", "-n", "0"])
    assert result.exit_code == 2  # Typer validation error


def test_batch_reports_failure_and_continues():
    failure = GenerationFailure(reason="boom")
    with patch(
        "cetools.cli.character.generate",
        side_effect=[_make_character(), failure, _make_character()],
    ) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--random", "-n", "3"])
    assert mock_generate.call_count == 3
    assert all(call.args[0] is RANDOM for call in mock_generate.call_args_list)
    assert result.exit_code == 1
    assert "boom" in result.stderr
    assert result.stdout.count("Navy (7 terms)") == 2


def test_batch_all_failures_exits_1_with_empty_stdout():
    failure = GenerationFailure(reason="all fail")
    with patch(
        "cetools.cli.character.generate",
        side_effect=[failure, failure],
    ) as mock_generate:
        result = runner.invoke(app, ["character", "generate", "--random", "-n", "2"])
    assert mock_generate.call_count == 2
    assert all(call.args[0] is RANDOM for call in mock_generate.call_args_list)
    assert result.exit_code == 1
    assert result.stdout.strip() == ""
    assert "all fail" in result.stderr
