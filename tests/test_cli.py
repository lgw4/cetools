import inspect
from functools import partial
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cetools.cli import prompts, ship
from cetools.cli.main import app
from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.generator import DRAFT, RANDOM
from cetools.engine.models import Cash, Character, GenerationFailure
from cetools.engine.ships import (
    ArmorType,
    Configuration,
    Drive,
    HullClass,
    armor_options,
    available_ratings,
    bay_kinds,
    computer_models,
    electronics_packages,
    fitting_kinds,
    hardpoints,
    hull_tonnages,
    screen_kinds,
    small_craft_maneuver_ratings,
    small_craft_power_ratings,
    small_craft_weapons,
    turret_mounts,
    turret_weapons,
)

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


# --- T018: `cetools world generate` ---


def test_world_generate_seed_prints_one_line_and_exits_0():
    result = runner.invoke(app, ["world", "generate", "--seed", "42"])
    assert result.exit_code == 0
    assert len(result.stdout.strip().splitlines()) == 1


def test_world_generate_name_names_the_world():
    result = runner.invoke(app, ["world", "generate", "--name", "Terra", "--seed", "1"])
    assert result.exit_code == 0
    assert result.stdout.startswith("Terra")


def test_world_generate_count_prints_multiple_lines():
    result = runner.invoke(app, ["world", "generate", "--count", "2", "--seed", "1"])
    assert result.exit_code == 0
    assert len(result.stdout.strip().splitlines()) == 2


def test_world_generate_default_count_is_one():
    result = runner.invoke(app, ["world", "generate", "--seed", "7"])
    assert result.exit_code == 0
    assert len(result.stdout.strip().splitlines()) == 1


def test_world_generate_name_with_count_greater_than_one_exits_1():
    result = runner.invoke(app, ["world", "generate", "--name", "Terra", "--count", "2"])
    assert result.exit_code == 1
    assert "--name applies only to a single world (use --count 1)." in result.stderr


def test_world_generate_allegiance_is_stamped():
    result = runner.invoke(app, ["world", "generate", "--seed", "1", "--allegiance", "ImDs"])
    assert result.exit_code == 0
    assert result.stdout.strip().endswith("ImDs")


def test_world_generate_allegiance_defaults_to_na():
    result = runner.invoke(app, ["world", "generate", "--seed", "1"])
    assert result.exit_code == 0
    assert result.stdout.strip().endswith("Na")


def test_world_generate_same_seed_is_deterministic():
    result_a = runner.invoke(app, ["world", "generate", "--seed", "5"])
    result_b = runner.invoke(app, ["world", "generate", "--seed", "5"])
    assert result_a.stdout == result_b.stdout


def test_world_generate_count_below_one_is_rejected():
    result = runner.invoke(app, ["world", "generate", "--count", "0"])
    assert result.exit_code != 0


def test_world_generate_without_seed_still_succeeds():
    result = runner.invoke(app, ["world", "generate"])
    assert result.exit_code == 0
    assert result.stdout.strip()


# --- T028: `cetools world subsector` ---


def test_world_subsector_seed_prints_hex_prefixed_lines_and_exits_0():
    result = runner.invoke(app, ["world", "subsector", "--seed", "7"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert lines
    for line in lines:
        tokens = line.split()
        hex_code = tokens[1]
        assert len(hex_code) == 4
        assert hex_code.isdigit()
        assert tokens.count(hex_code) == 1


def test_world_subsector_dense_yields_more_occupied_hexes_than_default():
    default_result = runner.invoke(app, ["world", "subsector", "--seed", "7"])
    dense_result = runner.invoke(app, ["world", "subsector", "--density", "dense", "--seed", "7"])
    default_lines = len(default_result.stdout.strip().splitlines())
    dense_lines = len(dense_result.stdout.strip().splitlines())
    assert dense_lines > default_lines


def test_world_subsector_invalid_density_exits_nonzero():
    result = runner.invoke(app, ["world", "subsector", "--density", "bogus"])
    assert result.exit_code != 0


def test_world_subsector_same_seed_is_deterministic():
    result_a = runner.invoke(app, ["world", "subsector", "--seed", "5"])
    result_b = runner.invoke(app, ["world", "subsector", "--seed", "5"])
    assert result_a.stdout == result_b.stdout


def test_character_same_seed_is_deterministic():
    args = ["character", "generate", "--career", "scout", "--seed", "42"]
    first = runner.invoke(app, args)
    second = runner.invoke(app, args)
    assert first.exit_code == 0
    assert first.stdout.strip()
    assert first.stdout == second.stdout


def test_character_different_seeds_differ():
    base = ["character", "generate", "--career", "scout"]
    a = runner.invoke(app, base + ["--seed", "1"])
    b = runner.invoke(app, base + ["--seed", "2"])
    assert a.stdout != b.stdout


def test_character_seed_with_count_fixes_the_whole_sequence():
    args = ["character", "generate", "--career", "scout", "-n", "3", "--seed", "7"]
    first = runner.invoke(app, args)
    second = runner.invoke(app, args)
    assert first.stdout == second.stdout
    # The seed fixes a sequence of three distinct characters, not one repeated.
    blocks = [block for block in first.stdout.strip().split("\n\n") if block.strip()]
    assert len(blocks) == 3
    assert len(set(blocks)) > 1


# --- `cetools ship build` (T018) ---

_FREE_TRADER_TOML = "tests/data/ships/free-trader.toml"


# The SRD's worked free-trader example, verbatim.
_BEOWULF_PARAGRAPH = (
    "Using a 200-ton hull (4 Hull, 4 Structure), the Beowulf is a starship. It mounts jump "
    "drive A, maneuver drive A and power plant A, giving a performance of Jump-1 and 1-G "
    "acceleration. Fuel tankage of 22 tons supports the power plant for two weeks and one "
    "Jump-1 jump. Adjacent to the bridge is a computer Model 1. The ship is equipped with "
    "Standard sensors (DM-4). There are four staterooms. The ship has two hardpoints and two "
    "tons allocated to fire control, but has no weapons installed. Cargo capacity is 135 tons. "
    "The hull is standard, and no additional armor has been installed. Special features "
    "include one ton of fuel processors (processes 20 tons of unrefined fuel into refined fuel "
    "per day). The ship requires a crew of five: one pilot, one navigator, one engineer, one "
    "medic and one steward. The ship cannot carry any additional passengers. The ship costs "
    "MCr29.772 (including discounts and fees) and takes 44 weeks to build."
)


def test_ship_build_prints_a_heading_and_one_paragraph_and_exits_0():
    result = runner.invoke(app, ["ship", "build", _FREE_TRADER_TOML])
    assert result.exit_code == 0

    lines = _description_lines(result.stdout)
    assert len(lines) == 3
    assert lines[0] == "TL8 Beowulf"
    assert lines[1] == ""
    assert lines[2].endswith(".")


# This doubles as T022 (US2): `ship build` on a hand-authored design is
# unchanged by ship naming. It asserts the whole rendering, heading included,
# so a separate "still renders TL8 Beowulf" case would add no coverage.
def test_ship_build_free_trader_matches_the_worked_example():
    result = runner.invoke(app, ["ship", "build", _FREE_TRADER_TOML])
    assert result.exit_code == 0
    assert _description_lines(result.stdout) == ["TL8 Beowulf", "", _BEOWULF_PARAGRAPH]


def test_ship_build_renders_an_authored_purpose_and_tech_level():
    path = "tests/data/ships/subsidized-merchant.toml"
    result = runner.invoke(app, ["ship", "build", path])
    assert result.exit_code == 0

    lines = _description_lines(result.stdout)
    assert lines[0] == "TL11 Beowulf"
    assert "the Beowulf is a subsidized merchant plying the routes" in lines[2]


def test_ship_build_toml_emits_round_trippable_design():
    result = runner.invoke(app, ["ship", "build", _FREE_TRADER_TOML, "--toml"])
    assert result.exit_code == 0
    assert "hull_tons = 200" in result.stdout

    from cetools.engine.ships import build_ship, loads_design

    design = loads_design(result.stdout)
    build_ship(design)  # round-tripped design must still be legal


def test_ship_build_out_writes_a_file(tmp_path):
    out_path = tmp_path / "beowulf.toml"
    result = runner.invoke(
        app, ["ship", "build", _FREE_TRADER_TOML, "--toml", "--out", str(out_path)]
    )
    assert result.exit_code == 0
    assert out_path.exists()
    assert "hull_tons = 200" in out_path.read_text()


def test_ship_build_out_without_toml_exits_1():
    result = runner.invoke(app, ["ship", "build", _FREE_TRADER_TOML, "--out", "ignored.toml"])
    assert result.exit_code == 1
    assert "--toml" in result.stderr


def test_ship_build_missing_file_exits_1():
    result = runner.invoke(app, ["ship", "build", "/no/such/design.toml"])
    assert result.exit_code == 1
    assert "cannot read design file" in result.stderr


def test_ship_build_malformed_toml_exits_1(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text("not valid toml [[[")
    result = runner.invoke(app, ["ship", "build", str(bad)])
    assert result.exit_code == 1
    assert result.stderr.strip()


def test_ship_build_rules_illegal_design_exits_1(tmp_path):
    illegal = tmp_path / "illegal.toml"
    illegal.write_text('hull_tons = 150\n\n[drives]\njump = "A"\npower = "A"\n')
    result = runner.invoke(app, ["ship", "build", str(illegal)])
    assert result.exit_code == 1
    assert "not a tabulated hull size" in result.stderr


# --- `cetools ship generate` (T031, T022) ---


def _description_lines(stdout: str) -> list[str]:
    """The heading, blank line and paragraph of a USDF description, with the
    trailing newline `typer.echo` adds stripped."""
    return stdout.rstrip("\n").split("\n")


def test_ship_generate_prints_a_heading_and_one_paragraph():
    result = runner.invoke(app, ["ship", "generate", "--seed", "42"])
    assert result.exit_code == 0

    lines = _description_lines(result.stdout)
    assert len(lines) == 3
    assert lines[0].startswith("TL")
    assert lines[1] == ""
    assert lines[2].endswith(".")


def test_ship_generate_seed_is_byte_identical():
    args = ["ship", "generate", "--seed", "42"]
    first = runner.invoke(app, args)
    second = runner.invoke(app, args)
    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.stdout == second.stdout


def test_ship_generate_hull_reflected_in_description():
    result = runner.invoke(app, ["ship", "generate", "--seed", "42", "--hull", "400"])
    assert result.exit_code == 0
    assert "400-ton hull" in result.stdout


def test_ship_generate_toml_emits_round_trippable_design():
    result = runner.invoke(app, ["ship", "generate", "--seed", "42", "--toml"])
    assert result.exit_code == 0

    from cetools.engine.ships import build_ship, loads_design

    design = loads_design(result.stdout)
    build_ship(design)  # generated design must be legal


def test_ship_generate_out_writes_a_file(tmp_path):
    out_path = tmp_path / "generated.toml"
    result = runner.invoke(
        app, ["ship", "generate", "--seed", "42", "--toml", "--out", str(out_path)]
    )
    assert result.exit_code == 0
    assert out_path.exists()

    from cetools.engine.ships import build_ship, loads_design

    build_ship(loads_design(out_path.read_text()))


def test_ship_generate_reports_seed_on_stderr_and_never_in_the_paragraph():
    result = runner.invoke(app, ["ship", "generate"])
    assert result.exit_code == 0
    assert "seed" in result.stderr.lower()

    paragraph = _description_lines(result.stdout)[2]
    assert "seed" not in paragraph.lower()
    assert "seed" not in result.stdout.lower()


def test_ship_generate_invalid_hull_exits_1():
    result = runner.invoke(app, ["ship", "generate", "--hull", "150"])
    assert result.exit_code == 1
    assert result.stderr.strip()


# --- `cetools ship generate --small-craft` (T042) ---


def test_ship_generate_small_craft_without_hull():
    result = runner.invoke(app, ["ship", "generate", "--small-craft", "--seed", "7", "--toml"])
    assert result.exit_code == 0

    from cetools.engine.ships import build_ship, loads_design

    design = loads_design(result.stdout)
    assert 10 <= design.hull_tons <= 95
    build_ship(design)


def test_ship_generate_small_craft_with_hull():
    result = runner.invoke(
        app, ["ship", "generate", "--small-craft", "--hull", "40", "--seed", "7"]
    )
    assert result.exit_code == 0
    assert "40-ton hull" in result.stdout


def test_ship_generate_small_craft_hull_95_accepted():
    result = runner.invoke(
        app, ["ship", "generate", "--small-craft", "--hull", "95", "--seed", "7"]
    )
    assert result.exit_code == 0
    assert "95-ton hull" in result.stdout


def test_ship_generate_small_craft_hull_100_out_of_range_exits_1():
    result = runner.invoke(
        app, ["ship", "generate", "--small-craft", "--hull", "100", "--seed", "7"]
    )
    assert result.exit_code == 1
    assert result.stderr.strip()


# --- `cetools ship generate --interactive` (#44) ---


_QUESTIONS = (
    "hull_class",
    "hull",
    "configuration",
    "jump",
    "maneuver",
    "power",
    "armor",
    "computer",
    "electronics",
    "staterooms",
    "fitting",
    "turrets",
    "bay",
    "screen",
    "name",
    "purpose",
)
"""The wizard's questions, in the order it asks them.

Piped input is positional, so every test that answers one question has to know
where the others sit. Keeping that knowledge here means a ticket which adds a
question edits one line rather than every test that answers a later one.
"""


_SMALL_CRAFT_SKIPS = ("jump", "bay")
"""The questions a small-craft session never asks: the ruleset forbids both."""

_ENTER_THROUGH = "\n" * (len(_QUESTIONS) + 2)
"""More Enters than the wizard has questions, so a test that means "take every
default" keeps meaning that as later tickets add prompts."""


def _small_craft_answers(*, skip: tuple[str, ...] = (), **given: str) -> str:
    """Piped input for a session already known to be building a small craft.

    `--small-craft` pre-answers the hull class, and the ruleset omits the jump
    and bay questions, so those three slots are never asked for.
    """
    return _answers(skip=("hull_class",) + _SMALL_CRAFT_SKIPS + skip, **given)


def _pins_an_armor_fit(armor_answer: str) -> bool:
    """Whether an `armor` answer produces a real `ArmorFit`—Enter (no answer
    at all) and `none` do not, so the wizard asks no follow-up there; any
    other answer, including one reached after a malformed retry, pins a layer
    and the new Armor options question follows it (T047, FR-019)."""
    last_line = armor_answer.strip().splitlines()[-1].strip().lower() if armor_answer else ""
    return last_line not in ("", "none")


def _answers(
    *, skip: tuple[str, ...] = (), pad: bool = True, armor_options: str = "", **given: str
) -> str:
    """Piped input answering the named questions and pressing Enter through the rest.

    `skip` names questions this invocation never asks, because a flag already
    pre-answered them: `--hull` means the hull question is not asked, and every
    answer after it would otherwise land one slot early.

    `pad` appends spare Enters to carry any prompt this table does not know
    about, such as a turret's mount and weapon. Turn it off when the test has
    something to say *after* the session ends, since the spare Enters would
    otherwise be swallowed by the accept-or-revise question.

    `armor_options` answers the Armor options question that follows a pinned
    armor answer (T047)—not one of `_QUESTIONS`, since it is asked only
    conditionally, so a caller who does not care about it need not know it
    exists.
    """
    unknown = (set(given) | set(skip)) - set(_QUESTIONS)
    assert not unknown, f"no such question: {sorted(unknown)}"
    asked = (question for question in _QUESTIONS if question not in skip)
    parts = []
    for question in asked:
        value = given.get(question, "")
        parts.append(f"{value}\n")
        if question == "armor" and _pins_an_armor_fit(value):
            parts.append(f"{armor_options}\n")
    answered = "".join(parts)
    return answered + _ENTER_THROUGH if pad else answered


_SCALAR_PROMPTS = (
    ("configuration", "Configuration (distributed, standard, streamlined) [roll]:", "streamlined"),
    ("computer", "Computer model (1-7, none) [roll]:", "3"),
    (
        "electronics",
        "Electronics (standard, basic civilian, basic military, advanced, very advanced, "
        "none) [roll]:",
        "basic_military",
    ),
    ("staterooms", "Staterooms (a count, or none) [roll]:", "4"),
    (
        "fitting",
        "Fitting (armory, detention cell, fuel scoops, fuel processor, laboratory, library, "
        "luxuries, vault, none) [roll]:",
        "laboratory",
    ),
    ("bay", "Weapon bay (missile bank, particle, meson, fusion, none) [roll]:", "particle"),
    ("screen", "Screen (meson screen, nuclear damper, none) [roll]:", "meson_screen"),
    ("name", "Name (any text, or none) [roll]:", "Wayfarer"),
)


@pytest.mark.parametrize(
    "question,prompt,answer", _SCALAR_PROMPTS, ids=[q for q, _, _ in _SCALAR_PROMPTS]
)
def test_ship_generate_interactive_asks_for_each_scalar_field(question, prompt, answer):
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), **{question: answer}),
    )
    assert result.exit_code == 0, result.stderr
    assert prompt in result.stderr


def test_ship_generate_interactive_fitting_prompt_does_not_name_the_vehicle_hangar():
    """AS 1.4, FR-024: the question cannot supply a vehicle's tonnage, so the
    one fitting that needs one is not offered."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",)),
    )
    assert result.exit_code == 0, result.stderr
    assert "vehicle_hangar" not in result.stderr
    assert "vehicle hangar" not in result.stderr


def test_ship_generate_interactive_computer_prompt_shows_a_range_not_every_model():
    """AS 1.5, FR-005: seven tabulated models collapse to one run."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",)),
    )
    assert result.exit_code == 0, result.stderr
    assert "Computer model (1-7, none) [roll]:" in result.stderr
    assert "1, 2, 3, 4, 5, 6, 7" not in result.stderr


def test_ship_generate_interactive_pins_every_scalar_field_at_once():
    """One session answering the lot, read back off the design it wrote."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(
            skip=("hull",),
            configuration="streamlined",
            computer="3",
            electronics="basic_military",
            staterooms="4",
            fitting="laboratory",
            bay="particle",
            screen="meson_screen",
            name="Wayfarer",
            purpose="a courier for the mails",
        ),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import Configuration, loads_design

    design = loads_design(result.stdout)
    assert design.configuration is Configuration.STREAMLINED
    assert design.computer.model == 3
    assert design.electronics == "basic_military"
    assert design.staterooms == 4
    assert [fit.kind for fit in design.fittings] == ["laboratory"]
    assert [fit.kind for fit in design.bays] == ["particle"]
    assert [fit.kind for fit in design.screens] == ["meson_screen"]
    assert design.name == "Wayfarer"
    assert design.purpose == "a courier for the mails"


def test_ship_generate_interactive_purpose_defaults_to_none_not_to_a_roll():
    """The one field generation never invents, so its prompt must not imply it
    will: pressing Enter leaves the ship without a purpose."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",)),
    )
    assert result.exit_code == 0
    assert "Purpose [none]:" in result.stderr
    assert "Purpose (" not in result.stderr  # FR-006: the [none] default already says it

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).purpose is None


def test_ship_generate_interactive_staterooms_and_name_carry_fr006_notes():
    """Neither has a closed set, but both must say `none` pins a value Enter
    does not (FR-006)."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",)),
    )
    assert result.exit_code == 0, result.stderr
    assert "Staterooms (a count, or none) [roll]:" in result.stderr
    assert "Name (any text, or none) [roll]:" in result.stderr


def test_ship_generate_interactive_none_pins_zero_staterooms():
    """Zero is an answer: `none` at the staterooms prompt means a ship with no
    staterooms, which is different from letting the dice choose."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), staterooms="none"),
    )
    assert result.exit_code == 0

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).staterooms == 0


def test_ship_generate_interactive_zero_is_an_alternate_spelling_of_none_at_staterooms():
    """FR-002: `0` pins the same deliberate zero as `none`, and is not itself
    named at the prompt—`none` already says it."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), staterooms="0"),
    )
    assert result.exit_code == 0, result.stderr
    assert "Staterooms (a count, or none) [roll]:" in result.stderr
    assert "0" not in result.stderr.split("Staterooms")[1].split("[roll]:")[0]

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).staterooms == 0


@pytest.mark.parametrize(
    "question,answer,reason",
    [
        ("configuration", "wedge", "wedge is not a known configuration"),
        ("computer", "9", "unknown computer model 9"),
        ("electronics", "psychic", "unknown electronics package 'psychic'"),
        ("staterooms", "-1", "staterooms cannot be negative"),
        ("fitting", "swimming_pool", "unknown fitting 'swimming_pool'"),
        ("bay", "railgun", "unknown bay kind 'railgun'"),
        ("screen", "deflector", "unknown screen kind 'deflector'"),
    ],
)
def test_ship_generate_interactive_unknown_scalar_answers_are_reasked(question, answer, reason):
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",), **{question: f"{answer}\n"}),
    )
    assert result.exit_code == 0, result.stderr
    assert reason in result.stderr


@pytest.mark.parametrize(
    "question,answer,known",
    [
        (
            "electronics",
            "psychic",
            "standard, basic civilian, basic military, advanced, very advanced, none",
        ),
        (
            "fitting",
            "swimming_pool",
            "armory, detention cell, fuel scoops, fuel processor, laboratory, library, "
            "luxuries, vault, none",
        ),
        ("screen", "deflector", "meson screen, nuclear damper, none"),
    ],
    ids=["electronics", "fitting", "screen"],
)
def test_ship_generate_interactive_refusal_names_values_in_displayed_spelling_and_order(
    question, answer, known
):
    """FR-016: the refusal names the same set the prompt named, in the same
    order, `none` included where the prompt accepted it (AS 1.7, AS 3.5)."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",), **{question: f"{answer}\n"}),
    )
    assert result.exit_code == 0, result.stderr
    assert f"known: {known}" in result.stderr


def test_ship_generate_interactive_turret_mount_refusal_names_values_in_displayed_spelling():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",), turrets="1\nswivel\nsingle\npulse_laser"),
    )
    assert result.exit_code == 0, result.stderr
    assert "known: single, double, triple, pop up, fixed" in result.stderr
    assert (
        result.stderr.count("Turret 1 mount (single, double, triple, pop up, fixed) [roll]:") == 2
    )


# --- T036 (US3): every accepted form of a displayed value is one answer (FR-015) ---


@pytest.mark.parametrize(
    "form", ["pop up", "pop_up", "pop-up", "Pop Up", "POP_UP"], ids=lambda f: repr(f)
)
def test_ship_generate_interactive_turret_mount_accepts_every_form_of_pop_up(form):
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), turrets=f"1\n{form}\npulse_laser"),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    (turret,) = loads_design(result.stdout).turrets
    assert turret.mount == "pop_up"


@pytest.mark.parametrize("form", ["bonded superdense 15", "bonded_superdense 15"])
def test_ship_generate_interactive_armor_accepts_the_type_spaced_or_underscored(form):
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), armor=form),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import ArmorType, loads_design

    assert [(fit.type, fit.percent) for fit in loads_design(result.stdout).armor] == [
        (ArmorType.BONDED_SUPERDENSE, 15)
    ]


def test_ship_generate_interactive_electronics_collapses_a_doubled_internal_space():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), electronics="basic  civilian"),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).electronics == "basic_civilian"


@pytest.mark.parametrize(
    "question,carried",
    [
        ("computer", "computer"),
        ("electronics", "electronics"),
        ("fitting", "fittings"),
        ("bay", "bays"),
        ("screen", "screens"),
    ],
)
def test_ship_generate_interactive_none_pins_each_optional_component_away(question, carried):
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), **{question: "none"}),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert not getattr(loads_design(result.stdout), carried)


@pytest.mark.parametrize(
    "question,answer,reason",
    [
        ("computer", "quantum", "quantum is not a computer model"),
        ("staterooms", "loads", "loads is not a number of staterooms"),
    ],
)
def test_ship_generate_interactive_unreadable_scalar_answers_are_reasked(question, answer, reason):
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",), **{question: f"{answer}\n"}),
    )
    assert result.exit_code == 0, result.stderr
    assert reason in result.stderr


def test_ship_generate_interactive_pins_a_fitting_the_generator_would_never_roll():
    """A vault is absent from the curated list, so no seed produces one."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), fitting="vault"),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert [fit.kind for fit in loads_design(result.stdout).fittings] == ["vault"]


def test_ship_generate_interactive_a_vehicle_sized_fitting_is_refused_at_the_prompt():
    """Vehicle tonnage is out of scope for the wizard (#41), so the record that
    needs it refuses the answer rather than the wizard inventing a tonnage."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",), fitting="vehicle_hangar\nvault"),
    )
    assert result.exit_code == 0, result.stderr
    assert "vehicle_hangar requires a positive vehicle_tons" in result.stderr


def test_ship_generate_interactive_none_pins_a_ship_with_no_name():
    """`none` at the name prompt is an answer, not a skipped question: it must
    not quietly fall through to the catalogue."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), name="none"),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).name == ""


_OVERLOADED = [
    "ship",
    "generate",
    "--interactive",
    "--hull",
    "200",
    "--seed",
    "11",
]
"""A session asking a 200-ton hull for more than it can hold."""

_OVERLOADED_ANSWERS = dict(
    skip=("hull",),
    jump="2",
    armor="crystaliron 30",
    staterooms="8",
    turrets="2\ntriple\npulse_laser\ntriple\npulse_laser",
)


def test_ship_generate_interactive_offers_accept_or_revise_when_something_went_unmet():
    """Fourteen answers should not be lost because one did not fit."""
    result = runner.invoke(app, _OVERLOADED, input=_answers(**_OVERLOADED_ANSWERS))

    assert result.exit_code == 0
    assert "could not honour" in result.stderr
    assert "Accept this ship or revise [accept]:" in result.stderr


def test_ship_generate_interactive_accepting_prints_the_ship_and_exits_0():
    """Enter at the accept prompt takes the default, which is to accept."""
    result = runner.invoke(app, _OVERLOADED, input=_answers(**_OVERLOADED_ANSWERS))

    assert result.exit_code == 0
    assert result.stdout.strip()
    assert result.stderr.count("Accept this ship or revise [accept]:") == 1


def test_ship_generate_interactive_revising_re_asks_only_the_implicated_prompts():
    """Only the answers named in the report come back, and every other answer
    the referee gave is preserved untouched."""
    result = runner.invoke(
        app,
        _OVERLOADED + ["--toml"],
        input=_answers(pad=False, **_OVERLOADED_ANSWERS) + "revise\n4\nnone\n",
    )
    assert result.exit_code == 0, result.stderr

    after_revise = result.stderr.split("Accept this ship or revise")[1]
    assert "Staterooms (a count, or none) [roll]:" in after_revise
    assert "Turrets (1-2, none) [roll]:" in after_revise
    assert "Configuration" not in after_revise  # an answer nothing implicated
    assert "Armor" not in after_revise

    from cetools.engine.ships import loads_design

    design = loads_design(result.stdout)
    assert design.staterooms == 4  # the revised answer
    assert design.turrets == ()
    assert design.armor[0].percent == 30  # the answer that was kept


def test_ship_generate_interactive_revising_the_hull_class_re_asks_the_tonnage():
    """Tonnage is tabulated per ruleset, so the class it was validated against
    leaving takes the answer with it.

    Carrying a 200-ton starship hull into a small-craft session guarantees a
    refusal on the next attempt and spends one of the five on it, over an answer
    the referee could not have kept even if they wanted to.
    """
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), pad=False, armor="crystaliron 7")
        + "hull_class\nsmall craft\n40\naccept\n",
    )
    assert result.exit_code == 0, result.stderr

    after_revise = result.stderr.split("Revise which answers")[1]
    assert "Hull tonnage" in after_revise

    from cetools.engine.ships import HullClass, loads_design

    design = loads_design(result.stdout)
    assert design.hull_class is HullClass.SMALL_CRAFT
    assert design.hull_tons == 40


def test_ship_generate_interactive_a_design_the_builder_rejects_re_enters_the_loop():
    """The other failure class: no ship at all, and interactively that is a
    question rather than an exit."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), pad=False, armor="crystaliron 7")
        + "armor\ncrystaliron 5\n\n",  # revised armor pins a layer, so options is asked again
    )
    assert result.exit_code == 0, result.stderr
    assert "armor must be added in 5% increments" in result.stderr

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).armor[0].percent == 5


def test_ship_generate_a_design_the_builder_rejects_still_exits_1_when_not_interactive():
    result = runner.invoke(app, ["ship", "generate", "--hull", "150", "--seed", "11"])

    assert result.exit_code == 1
    assert not result.stdout.strip()


def test_ship_generate_interactive_the_revise_loop_gives_up_on_repeated_conflicts():
    """A referee who answers the same way every time still gets a ship rather
    than an endless session."""
    revisions = "revise\n8\n2\ntriple\npulse_laser\ntriple\npulse_laser\n" * 12
    result = runner.invoke(
        app, _OVERLOADED, input=_answers(pad=False, **_OVERLOADED_ANSWERS) + revisions
    )

    assert result.exit_code == 0
    assert "revised enough" in result.stderr
    assert result.stdout.strip()


def test_ship_generate_interactive_the_accept_prompt_re_asks_a_typo():
    """Every other prompt re-asks rather than guessing; this one is no different,
    because guessing here would silently accept a ship the referee rejected."""
    result = runner.invoke(
        app, _OVERLOADED, input=_answers(pad=False, **_OVERLOADED_ANSWERS) + "reivse\naccept\n"
    )

    assert result.exit_code == 0
    assert "answer accept or revise; got reivse" in result.stderr
    assert result.stderr.count("Accept this ship or revise [accept]:") == 2


def test_ship_generate_interactive_an_unknown_answer_name_is_reasked():
    """The answers to revise are named, so a name nothing knows is a typo."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), pad=False, armor="crystaliron 7")
        + "armour\narmor\ncrystaliron 5\n\n",  # revised armor pins a layer, options asked again
    )

    assert result.exit_code == 0, result.stderr
    assert "no such answer: armour" in result.stderr


_REVISE_PROMPT = (
    "Revise which answers (hull class, hull tons, configuration, jump rating, "
    "maneuver rating, power rating, armor, computer, electronics, staterooms, "
    "fitting, turrets, bay, screen, name, purpose) [all]:"
)


def test_ship_generate_interactive_revise_prompt_names_all_sixteen_answers():
    """FR-007: the revise question is the one prompt exempt from the two-line
    budget, and names every `DesignConstraints` field in spaced spelling."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), pad=False, armor="crystaliron 7")
        + "armor\ncrystaliron 5\n\n",  # revised armor pins a layer, options asked again
    )
    assert result.exit_code == 0, result.stderr
    assert _REVISE_PROMPT in result.stderr


@pytest.mark.parametrize(
    "answer",
    [
        "hull class, hull tons",
        "hull class hull tons",
        "hull_class hull_tons",
        "Hull Class, Hull Tons",
    ],
    ids=["spaced-comma", "spaced", "underscored", "mixed-case"],
)
def test_ship_generate_interactive_revise_accepts_every_form_of_a_two_word_name(answer):
    """FR-015: `hull class` and `hull tons` are one value each, not two unknown
    words—`split_values` matches the whole answer before it is split."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), pad=False, armor="crystaliron 7")
        + f"{answer}\nsmall craft\n40\naccept\n",
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).hull_tons == 40


def test_ship_generate_interactive_revising_everything_is_the_default():
    """Enter at the which-answers prompt puts the whole session back, which is
    the honest answer when a refusal names nothing the session can act on."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), pad=False, armor="crystaliron 7")
        # Everything comes back, including the hull class and tonnage the flag
        # pre-answered the first time round.
        + "\n" + _answers(pad=False, hull="200", armor="crystaliron 5"),
    )

    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).armor[0].percent == 5


def test_ship_generate_interactive_gives_up_and_exits_1_when_every_round_is_refused():
    """The other end of the loop: a refusal yields no ship at all, so a referee
    who answers illegally every time has nothing to be handed."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11"],
        input=_answers(skip=("hull",), pad=False, armor="crystaliron 7")
        # Each revised armor answer pins a layer, so options is asked again too.
        + "armor\ncrystaliron 7\n\n" * 4,
    )

    assert result.exit_code == 1
    assert not result.stdout.strip()
    assert "revised enough" in result.stderr
    assert result.stderr.count("armor must be added in 5% increments") == 5


def test_ship_generate_interactive_reproduces_a_session_by_saving_and_rebuilding(tmp_path):
    """No replay format: the TOML round-trip is already lossless, so a saved
    design rebuilds to exactly the ship the session produced."""
    out_path = tmp_path / "tonight.toml"
    generated = runner.invoke(
        app,
        _OVERLOADED + ["--toml", "--out", str(out_path)],
        input=_answers(**_OVERLOADED_ANSWERS),
    )
    assert generated.exit_code == 0, generated.stderr

    rebuilt = runner.invoke(app, ["ship", "build", str(out_path), "--toml"])
    assert rebuilt.exit_code == 0
    assert rebuilt.stdout == out_path.read_text() + "\n"


def test_ship_generate_reports_unmet_constraints_on_stderr_and_still_exits_0():
    """Generation never fails on tonnage: a real ship comes back, and the
    referee is told plainly which answers it could not honour."""
    result = runner.invoke(app, _OVERLOADED, input=_answers(**_OVERLOADED_ANSWERS))

    assert result.exit_code == 0
    assert "could not honour" in result.stderr
    assert "staterooms" in result.stderr
    assert "turrets" in result.stderr


def test_ship_generate_unmet_report_names_what_was_asked_and_what_was_got():
    result = runner.invoke(app, _OVERLOADED, input=_answers(**_OVERLOADED_ANSWERS))

    assert "asked 8, got 7" in result.stderr
    assert "t free" in result.stderr


def test_ship_generate_unmet_constraints_never_reach_stdout():
    """The ship on stdout stays a design a pipe can read."""
    result = runner.invoke(app, _OVERLOADED + ["--toml"], input=_answers(**_OVERLOADED_ANSWERS))

    assert result.exit_code == 0
    assert "could not honour" not in result.stdout

    from cetools.engine.ships import build_ship, loads_design

    build_ship(loads_design(result.stdout))


def test_ship_generate_says_nothing_when_every_constraint_is_honoured():
    result = runner.invoke(app, ["ship", "generate", "--seed", "42"])

    assert result.exit_code == 0
    assert "could not honour" not in result.stderr


def test_ship_generate_interactive_asks_for_the_hull_class_first():
    """It governs which questions follow, so it cannot be asked later."""
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "11"], input=_answers()
    )
    assert result.exit_code == 0

    asked = result.stderr
    assert asked.startswith("Hull class (starship, small craft) [starship]:")
    assert asked.index("Hull class") < asked.index("Hull tonnage")


def test_ship_generate_interactive_small_craft_session_omits_jump_and_bay():
    """The ruleset forbids both, so a referee designing a launch is not asked."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(hull_class="small craft", skip=_SMALL_CRAFT_SKIPS),
    )
    assert result.exit_code == 0, result.stderr
    assert "Jump rating" not in result.stderr
    assert "Weapon bay" not in result.stderr
    assert "Maneuver rating" in result.stderr


def test_ship_generate_interactive_small_craft_screen_prompt_offers_none_not_a_roll():
    """A screen is never rolled onto a small craft, so Enter there means none.

    Every other field's Enter genuinely rolls, and the label says `[roll]` on all
    of them. On this one path it was advertising a draw the generator does not
    make, which is the one field where a referee pressing Enter got something
    other than what the prompt promised.
    """
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--seed", "7"],
        input=_small_craft_answers(),
    )
    assert result.exit_code == 0, result.stderr
    assert "Screen (meson screen, nuclear damper, none) [none]:" in result.stderr


def test_ship_generate_interactive_starship_screen_prompt_still_offers_a_roll():
    """The label is wrong only on the small-craft path; a starship does roll one."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(),
    )
    assert result.exit_code == 0, result.stderr
    assert "Screen (meson screen, nuclear damper, none) [roll]:" in result.stderr


def test_ship_generate_interactive_hull_class_answer_selects_the_small_craft_ruleset():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(hull_class="small craft", skip=_SMALL_CRAFT_SKIPS),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import HullClass, loads_design

    assert loads_design(result.stdout).hull_class is HullClass.SMALL_CRAFT


def test_ship_generate_interactive_small_craft_hull_tonnages_are_the_small_craft_table():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(hull_class="small craft", hull="200\n40", skip=_SMALL_CRAFT_SKIPS),
    )
    assert result.exit_code == 0, result.stderr
    assert "200 tons is not a tabulated small-craft hull size" in result.stderr

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).hull_tons == 40


def test_ship_generate_interactive_small_craft_flag_pre_answers_the_hull_class():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--seed", "7"],
        input=_small_craft_answers(),
    )
    assert result.exit_code == 0, result.stderr
    assert "Hull class" not in result.stderr


def test_ship_generate_interactive_unknown_hull_class_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "11"],
        input=_answers(hull_class="battleship\nstarship"),
    )
    assert result.exit_code == 0, result.stderr
    assert "battleship is not a known hull class" in result.stderr


def test_ship_generate_interactive_small_craft_power_prompt_offers_what_the_maneuver_allows():
    """A 15-ton craft with a 1-G drive has room for a plant at 1 or 2 only."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--hull", "15", "--seed", "7"],
        input=_small_craft_answers(skip=("hull",), maneuver="1", power="4\n2"),
    )
    assert result.exit_code == 0, result.stderr
    assert "power rating 4 is not available" in result.stderr
    assert "available: 1-2" in result.stderr


def test_ship_generate_interactive_power_prompt_names_no_value_when_the_hull_can_carry_none():
    """Decision 9's one reachable path to FR-012's empty form: Enter at hull
    tonnage lets a 6-G manoeuvre rating pass the broad, unnarrowed check;
    revising the tonnage down to 10 then finds no plant fits beside it.

    The illegal `distributed` + `fuel_scoops` combination is what reaches the
    referee's own choice of fields to revise (`_ask_which_to_revise`), rather
    than the automatic re-ask an *unmet* constraint would drive instead.
    """
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(
            hull_class="small craft",
            skip=("jump", "bay"),
            pad=False,
            configuration="distributed",
            maneuver="6",
            fitting="fuel_scoops",
        )
        + "hull tons, power rating\n10\n6\n",
    )
    assert result.exit_code == 1
    assert "Power plant rating (a 10-ton hull can carry none, at least 6) [roll]:" in result.stderr
    assert (
        "a 10-ton hull can carry none, at least 6"
        in result.stderr.split(
            "Power plant rating (a 10-ton hull can carry none, at least 6) [roll]:"
        )[1]
    )


def test_ship_generate_interactive_small_craft_energy_weapon_beyond_the_plant_is_reasked():
    """The craft's armament is capped by its power plant, and the prompt knows
    the plant once its rating is pinned."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--hull", "15", "--seed", "7"],
        input=_small_craft_answers(
            skip=("hull",),
            maneuver="1",
            power="1",
            turrets="1\nsingle\npulse_laser\nsandcaster",
        ),
    )
    assert result.exit_code == 0, result.stderr
    assert "runs 0 energy weapon(s), so it cannot mount pulse_laser in a single" in result.stderr


def test_ship_generate_interactive_small_craft_refuses_a_maneuver_the_craft_cannot_carry():
    """Refused at its own prompt, so the power question that follows is never
    left with no acceptable answer: a 40-ton craft has no 4-G option once a
    plant and a cockpit have to sit beside the drive."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--hull", "40", "--seed", "7"],
        input=_small_craft_answers(skip=("hull",), maneuver="4\n2"),
    )
    assert result.exit_code == 0, result.stderr
    assert "cannot carry a 4-G drive and a power plant beside it" in result.stderr
    assert "power rating" not in result.stderr  # the power prompt had real options


def test_ship_generate_interactive_small_craft_energy_weapon_is_counted_per_slot():
    """A triple carries three of the weapon, so a plant that runs one energy
    weapon cannot fill it. Counting the mount's slots is what keeps the prompt
    and `build_ship` agreeing."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--hull", "40", "--seed", "7"],
        input=_small_craft_answers(
            skip=("hull",),
            maneuver="1",
            power="3",
            turrets="1\ntriple\npulse_laser\nsandcaster",
        ),
    )
    assert result.exit_code == 0, result.stderr
    assert "cannot mount pulse_laser in a triple" in result.stderr


def test_ship_generate_interactive_hull_flag_that_the_chosen_class_forbids_is_reasked():
    """`--hull` pre-answers the tonnage, but the referee picks the ruleset after
    the flag was written, so a stale pre-answer is reported and the question asked."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "7", "--toml"],
        input=_answers(hull_class="small craft", hull="40", skip=_SMALL_CRAFT_SKIPS),
    )
    assert result.exit_code == 0, result.stderr
    assert "200 tons is not a tabulated small-craft hull size" in result.stderr

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).hull_tons == 40


def test_ship_generate_interactive_asks_for_a_turret_count_showing_its_default():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",)),
    )
    assert result.exit_code == 0
    assert "Turrets (1-20, none) [roll]:" in result.stderr


def test_ship_generate_interactive_a_pinned_count_asks_for_each_turret_in_turn():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), turrets="2\ntriple\npulse_laser\nsingle\nsandcaster"),
    )
    assert result.exit_code == 0, result.stderr
    assert "Turret 1 mount (single, double, triple, pop up, fixed) [roll]:" in result.stderr
    assert (
        "Turret 1 weapon (missile rack, pulse laser, sandcaster, particle beam) [roll]:"
        in result.stderr
    )
    assert "Turret 2 mount (single, double, triple, pop up, fixed) [roll]:" in result.stderr

    from cetools.engine.ships import loads_design

    turrets = loads_design(result.stdout).turrets
    assert [(t.mount, t.weapons) for t in turrets] == [
        ("triple", ("pulse_laser",) * 3),
        ("single", ("sandcaster",)),
    ]


def test_ship_generate_interactive_a_pinned_count_alone_asks_but_rolls_the_details():
    """Enter through the inner questions and the count still holds."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), turrets="2\n\n\n\n"),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert len(loads_design(result.stdout).turrets) == 2


def test_ship_generate_interactive_a_pinned_weapon_may_ride_a_rolled_mount():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), turrets="1\n\nsandcaster"),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    (turret,) = loads_design(result.stdout).turrets
    assert set(turret.weapons) == {"sandcaster"}


def test_ship_generate_interactive_none_turrets_leaves_the_ship_unarmed():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), turrets="none"),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).turrets == ()


def test_ship_generate_interactive_zero_is_an_alternate_spelling_of_none_at_turrets():
    """FR-002: `0` pins the same deliberate zero as `none` at the turret count
    too, and is not itself named—`none` already says it."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11", "--toml"],
        input=_answers(skip=("hull",), turrets="0"),
    )
    assert result.exit_code == 0, result.stderr
    assert "Turrets (1-2, none) [roll]:" in result.stderr
    assert "0" not in result.stderr.split("Turrets")[1].split("[roll]:")[0]

    from cetools.engine.ships import loads_design

    assert loads_design(result.stdout).turrets == ()


def test_ship_generate_interactive_a_turret_count_is_taken_on_trust_when_the_hull_rolls():
    """With the hull left to the dice the wizard cannot know the hardpoints yet,
    so the count is accepted and the hull it lands on rules on it."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "11", "--toml"],
        input=_answers(turrets="1\nsingle\nsandcaster"),
    )
    assert result.exit_code == 0, result.stderr

    from cetools.engine.ships import loads_design

    assert len(loads_design(result.stdout).turrets) == 1


def test_ship_generate_interactive_a_count_above_the_hardpoints_is_reasked():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "11"],
        input=_answers(skip=("hull",), turrets="5\nnone"),
    )
    assert result.exit_code == 0, result.stderr
    assert (
        "a 200-ton starship has 2 hardpoint(s), so it cannot mount 5; available: 1-2, none"
        in result.stderr
    )
    assert result.stderr.count("Turrets (1-2, none) [roll]:") == 2


def test_ship_generate_interactive_unnarrowed_turrets_name_the_ruleset_maximum():
    """Trap 3 (FR-011): with no tonnage pinned the prompt cannot narrow to a
    hull, so it names the ruleset's own widest hull instead of staying silent."""
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "11"], input=_answers()
    )
    assert result.exit_code == 0, result.stderr
    assert "Turrets (1-50 on some starship hull, none) [roll]:" in result.stderr


def test_ship_generate_interactive_small_craft_unnarrowed_turrets_name_one():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(hull_class="small craft", skip=_SMALL_CRAFT_SKIPS),
    )
    assert result.exit_code == 0, result.stderr
    assert "Turrets (1 on some small craft hull, none) [roll]:" in result.stderr


def test_ship_generate_interactive_an_unnarrowed_count_above_the_maximum_is_reasked():
    """Trap 3 (FR-002): today an unpinned tonnage means no count is refused at
    all; a count above the ruleset's own maximum must now be caught here too."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "11"],
        input=_answers(turrets="51\nnone"),
    )
    assert result.exit_code == 0, result.stderr
    assert (
        "any starship hull has at most 50 hardpoint(s), so it cannot mount 51; "
        "available: 1-50, none" in result.stderr
    )
    assert result.stderr.count("Turrets (1-50 on some starship hull, none) [roll]:") == 2


@pytest.mark.parametrize(
    "answers,reason",
    [
        ("1\nswivel\nsingle\npulse_laser", "unknown turret mount 'swivel'"),
        ("1\nsingle\nbeam_laser\npulse_laser", "unknown turret weapon 'beam_laser'"),
        ("lots\nnone", "lots is not a number of turrets"),
        ("-1\nnone", "turrets cannot be negative"),
    ],
)
def test_ship_generate_interactive_unknown_turret_parts_are_reasked(answers, reason):
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "2000", "--seed", "11"],
        input=_answers(skip=("hull",), turrets=answers),
    )
    assert result.exit_code == 0, result.stderr
    assert reason in result.stderr


def test_ship_generate_interactive_asks_for_each_drive_as_a_rating():
    """A referee answers Jump-2, not drive C: the question is the rating."""
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "7"], input=_ENTER_THROUGH
    )
    assert result.exit_code == 0
    assert "Jump rating (1-6 on some starship hull) [roll]:" in result.stderr
    assert "Maneuver rating (1-6 on some starship hull) [roll]:" in result.stderr
    assert "Power plant rating (1-6 on some starship hull) [roll]:" in result.stderr


def test_ship_generate_interactive_pins_a_jump_rating_to_its_lightest_code():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3", "--toml"],
        input=_answers(skip=("hull",), jump="1"),
    )
    assert result.exit_code == 0

    from cetools.engine.ships import build_ship, loads_design

    ship = build_ship(loads_design(result.stdout))
    assert ship.jump_rating == 1
    assert ship.design.jump_code == "B"  # the lightest code delivering Jump-1 at 400 tons


def test_ship_generate_interactive_power_prompt_states_the_floor_its_drives_set():
    """The floor is `max(jump, maneuver)`, and the referee should not have to
    work it out. It can only be stated once both are pinned."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3"],
        input=_answers(skip=("hull",), jump="1", maneuver="3"),
    )
    assert result.exit_code == 0
    assert "Power plant rating (1-6, at least 3) [roll]:" in result.stderr


def test_ship_generate_interactive_power_below_its_floor_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3"],
        input=_answers(skip=("hull",), jump="2", maneuver="3", power="1\n3"),
    )
    assert result.exit_code == 0
    assert "power plant rating 1 is below the 3 its drives require" in result.stderr
    assert result.stderr.count("Power plant rating (1-6, at least 3) [roll]:") == 2


def test_ship_generate_interactive_power_floor_holds_when_only_one_drive_is_pinned():
    """A floor known in part is still a floor: Jump-2 alone puts the plant at 2,
    even with the manoeuvre drive left to the dice.

    The floor counts only the drives the referee pinned, because those are the
    only ones it can count. The drive left to chance needs no floor: it is drawn
    from what the pinned plant can run, so a plant that clears the prompt is
    never then refused over a rating nobody asked for. This seed rolled a
    manoeuvre drive of 5 before that cap existed, and the session lost the ship.
    """
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3", "--toml"],
        input=_answers(skip=("hull",), jump="2", power="1\n2"),
    )
    assert "Power plant rating (1-6, at least 2) [roll]:" in result.stderr
    assert "power plant rating 1 is below the 2 its drives require" in result.stderr
    assert result.exit_code == 0, result.stderr

    # The plant the referee asked for, first time, and a rolled drive it can run.
    assert "Accept this ship or revise" not in result.stderr

    from cetools.engine.ships import build_ship, loads_design

    ship = build_ship(loads_design(result.stdout))
    assert ship.power_rating == 2
    assert ship.maneuver_rating <= 2


def test_ship_generate_interactive_untabulated_rating_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3"],
        input=_answers(skip=("hull",), jump="9\n1"),
    )
    assert result.exit_code == 0
    assert "jump rating 9 is not tabulated for a 400-ton hull; available: 1-6" in result.stderr
    assert result.stderr.count("Jump rating (1-6) [roll]:") == 2


def test_ship_generate_interactive_non_numeric_rating_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3"],
        input=_answers(jump="two\n1"),
    )
    assert result.exit_code == 0
    assert "two is not a drive rating" in result.stderr


def test_ship_generate_interactive_checks_a_rating_against_every_hull_when_none_is_pinned():
    """With the hull left to the dice the wizard cannot know what this hull can
    deliver, but it can still refuse a rating no hull could."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "3"],
        input=_answers(jump="9\n1"),
    )
    assert result.exit_code == 0
    assert "not tabulated for any starship hull; available: 1-6" in result.stderr


_ARMOR_PROMPT = (
    "Armor (titanium steel, crystaliron, bonded superdense, each with a percent, or none) [roll]:"
)


def test_ship_generate_interactive_asks_for_armor_showing_its_default():
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "7"], input=_ENTER_THROUGH
    )
    assert result.exit_code == 0
    assert _ARMOR_PROMPT in result.stderr


def test_ship_generate_interactive_pins_an_armor_type_and_percent():
    """Seed 7 draws no armour, so armour on this ship can only be the answer.

    Both spellings of the percent are accepted, because a referee reading
    "10% of the hull" off the SRD will type the sign as often as not.
    """
    from cetools.engine.ships import ArmorType, loads_design

    for answer in ("crystaliron 10", "crystaliron 10%"):
        result = runner.invoke(
            app,
            ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
            input=_answers(armor=answer),
        )
        assert result.exit_code == 0, answer

        design = loads_design(result.stdout)
        assert [(fit.type, fit.percent) for fit in design.armor] == [(ArmorType.CRYSTALIRON, 10)]


def test_ship_generate_interactive_none_pins_an_unarmored_ship():
    """Seed 0 draws crystaliron, so an unarmoured ship here is the `none` answer."""
    rolled = runner.invoke(app, ["ship", "generate", "--seed", "0", "--toml"])
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "0", "--toml"],
        input=_answers(armor="none"),
    )
    assert result.exit_code == 0

    from cetools.engine.ships import loads_design

    assert loads_design(rolled.stdout).armor != ()
    assert loads_design(result.stdout).armor == ()


def test_ship_generate_interactive_malformed_armor_answers_are_reasked_with_the_reason():
    for answer, reason in (
        ("crystaliron", "give an armor type and a percent"),
        ("crystaliron ten", "ten is not a percent of the hull"),
        ("crystaliron 0", "armor percent must be positive"),
    ):
        result = runner.invoke(
            app,
            ["ship", "generate", "--interactive", "--seed", "7"],
            input=_answers(armor=f"{answer}\ncrystaliron 10"),
        )
        assert result.exit_code == 0, answer
        assert reason in result.stderr, answer


def test_ship_generate_interactive_armor_percent_rule_surfaces_at_assembly_not_the_prompt():
    """The multiple-of-5 rule lives in `build_ship` and is deliberately not
    duplicated outward, so 7% is accepted at the prompt and rejected on
    assembly.

    Since #51 that refusal is a question rather than an exit: the armour prompt
    comes back, and answering it legally yields a ship.
    """
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(pad=False, armor="crystaliron 7")
        + "armor\ncrystaliron 5\n\n",  # revised armor pins a layer, options asked again
    )
    assert result.exit_code == 0, result.stderr
    assert "armor must be added in 5% increments" in result.stderr
    assert result.stderr.count(_ARMOR_PROMPT) == 2  # asked, refused, asked again


def test_ship_generate_interactive_unknown_armor_type_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(armor="adamantium 10\ncrystaliron 10"),
    )
    assert result.exit_code == 0
    assert "adamantium is not a known armor type" in result.stderr
    assert result.stderr.count(_ARMOR_PROMPT) == 2


# --- T042-T044 (US4): armour options can be pinned (FR-017 to FR-021) ---


_ARMOR_OPTIONS_PROMPT = "Armor options (reflec, self sealing, stealth) [none]:"


def test_ship_generate_interactive_armor_options_asked_directly_after_a_pinned_type():
    """AS 4.1: the question follows the armour question with nothing between
    them, and does not name `none`—the `[none]` default already says it."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(armor="crystaliron 10"),
    )
    assert result.exit_code == 0, result.stderr
    after_armor = result.stderr.split(_ARMOR_PROMPT, 1)[1]
    assert after_armor.startswith(f" {_ARMOR_OPTIONS_PROMPT}")


def test_ship_generate_interactive_enter_at_armor_options_pins_no_options():
    """AS 4.3."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(armor="crystaliron 10"),
    )
    assert result.exit_code == 0, result.stderr
    assert loads_design(result.stdout).armor[0].options == ()


def test_ship_generate_interactive_armor_options_literal_none_pins_no_options():
    """FR-018: `none` is accepted though the prompt does not name it."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(armor="crystaliron 10", armor_options="none"),
    )
    assert result.exit_code == 0, result.stderr
    assert loads_design(result.stdout).armor[0].options == ()


@pytest.mark.parametrize("answer", ["reflec stealth", "reflec, stealth"])
def test_ship_generate_interactive_armor_options_space_or_comma_separates(answer):
    """FR-018: spaces or commas separate several options in one answer."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(armor="crystaliron 10", armor_options=answer),
    )
    assert result.exit_code == 0, answer
    assert loads_design(result.stdout).armor[0].options == ("reflec", "stealth")


def test_ship_generate_interactive_armor_options_self_sealing_typed_as_shown_is_one_option():
    """The case trap: `self sealing` typed exactly as displayed is one option,
    not two unknown words."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(armor="crystaliron 10", armor_options="self sealing"),
    )
    assert result.exit_code == 0, result.stderr
    assert loads_design(result.stdout).armor[0].options == ("self_sealing",)


def test_ship_generate_interactive_armor_options_reflec_self_sealing_is_two_options():
    """FR-015: the greedy scan takes the longest run that names a value, so a
    three-word answer here is two options rather than three unknown words."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(armor="crystaliron 10", armor_options="reflec self sealing"),
    )
    assert result.exit_code == 0, result.stderr
    assert loads_design(result.stdout).armor[0].options == ("reflec", "self_sealing")


def test_ship_generate_interactive_repeated_armor_option_is_reasked_with_the_reason():
    """AS 4.6."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(armor="crystaliron 10", armor_options="reflec reflec\nreflec"),
    )
    assert result.exit_code == 0, result.stderr
    assert "armor options must not repeat" in result.stderr
    assert result.stderr.count(_ARMOR_OPTIONS_PROMPT) == 2


def test_ship_generate_interactive_armor_options_mixed_valid_and_unknown_is_refused_whole():
    """FR-018, spec Edge Cases: `reflec bogus` pins neither option."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(armor="crystaliron 10", armor_options="reflec bogus\nreflec"),
    )
    assert result.exit_code == 0, result.stderr
    assert "bogus" in result.stderr
    assert loads_design(result.stdout).armor[0].options == ("reflec",)


def test_ship_generate_interactive_armor_options_not_asked_when_armor_answered_none():
    """AS 4.4, FR-019."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "0"],
        input=_answers(armor="none"),
    )
    assert result.exit_code == 0, result.stderr
    assert _ARMOR_OPTIONS_PROMPT not in result.stderr


def test_ship_generate_interactive_armor_options_not_asked_when_armor_is_rolled():
    """AS 4.5, FR-019: Enter at armour leaves it to the dice, and no `ArmorFit`
    exists yet for the options question to attach to."""
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "42"], input=_ENTER_THROUGH
    )
    assert result.exit_code == 0, result.stderr
    assert _ARMOR_OPTIONS_PROMPT not in result.stderr


def test_ship_generate_interactive_revising_armor_re_asks_the_options_question():
    """AS 4.7: the options question follows a revised armour answer too, and
    the new answer replaces rather than merges with the old one."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(pad=False, armor="crystaliron 7", armor_options="reflec")
        + "armor\ncrystaliron 5\nstealth\n",
    )
    assert result.exit_code == 0, result.stderr
    assert result.stderr.count(_ARMOR_OPTIONS_PROMPT) == 2  # asked, revised, asked again
    assert loads_design(result.stdout).armor[0].options == ("stealth",)


def test_ship_generate_interactive_revising_another_field_leaves_armor_options_untouched():
    """FR-021: an answer nothing implicated keeps its options too."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        _OVERLOADED + ["--toml"],
        input=_answers(pad=False, armor_options="reflec", **_OVERLOADED_ANSWERS)
        + "revise\n4\nnone\n",
    )
    assert result.exit_code == 0, result.stderr

    after_revise = result.stderr.split("Accept this ship or revise")[1]
    assert _ARMOR_OPTIONS_PROMPT not in after_revise
    assert loads_design(result.stdout).armor[0].options == ("reflec",)


def test_ship_generate_interactive_revising_armor_to_none_drops_its_options():
    """FR-021: options go with the layer they belonged to, since revising
    armour to `none` leaves nothing for them to attach to."""
    from cetools.engine.ships import loads_design

    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7", "--toml"],
        input=_answers(pad=False, armor="crystaliron 7", armor_options="reflec") + "armor\nnone\n",
    )
    assert result.exit_code == 0, result.stderr
    assert loads_design(result.stdout).armor == ()


def test_ship_generate_interactive_asks_for_the_hull_tonnage_showing_its_default():
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "42"], input=_ENTER_THROUGH
    )
    assert result.exit_code == 0
    assert (
        "Hull tonnage (100-1000 by 100, 1200-2000 by 200, 3000-5000 by 1000) [roll]:"
        in result.stderr
    )


def test_ship_generate_interactive_pressing_enter_yields_the_unprompted_ship():
    """Enter rolls, so answering nothing collapses to today's behaviour exactly.

    Byte equality on stdout also pins that no prompt reaches it, which is what
    lets `--interactive` compose with `--toml` and `--out`.
    """
    prompted = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "42"], input=_ENTER_THROUGH
    )
    rolled = runner.invoke(app, ["ship", "generate", "--seed", "42"])

    assert prompted.exit_code == 0
    assert prompted.stdout == rolled.stdout


def test_ship_generate_interactive_toml_stdout_is_still_a_readable_design():
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "42", "--toml"], input=_ENTER_THROUGH
    )
    assert result.exit_code == 0

    from cetools.engine.ships import build_ship, loads_design

    build_ship(loads_design(result.stdout))


def test_ship_generate_interactive_an_answered_tonnage_pins_the_hull():
    """Seed 42 rolls a 400-ton hull, so pinning 200 is visibly the answer and
    not the dice."""
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "42"], input=_answers(hull="200")
    )
    assert result.exit_code == 0
    assert "200-ton hull" in result.stdout


def test_ship_generate_interactive_untabulated_tonnage_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "42"],
        input=_answers(hull="150\n200"),
    )
    assert result.exit_code == 0
    assert (
        "150 tons is not a tabulated hull size; "
        "valid: 100-1000 by 100, 1200-2000 by 200, 3000-5000 by 1000" in result.stderr
    )
    assert (
        result.stderr.count(
            "Hull tonnage (100-1000 by 100, 1200-2000 by 200, 3000-5000 by 1000) [roll]:"
        )
        == 2
    )
    assert "200-ton hull" in result.stdout


def test_ship_generate_interactive_a_non_numeric_answer_is_reasked():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "42"],
        input=_answers(hull="biggish\n200"),
    )
    assert result.exit_code == 0
    assert "biggish is not a number of tons" in result.stderr
    assert "200-ton hull" in result.stdout


def test_ship_generate_interactive_small_craft_rejects_a_starship_tonnage():
    """The prompt validates against the ruleset in play, not against hulls at large."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--seed", "7"],
        input=_small_craft_answers(hull="200\n40"),
    )
    assert result.exit_code == 0
    assert "200 tons is not a tabulated small-craft hull size" in result.stderr
    assert "40-ton hull" in result.stdout


def test_ship_generate_interactive_end_of_input_aborts_without_a_ship():
    result = runner.invoke(app, ["ship", "generate", "--interactive", "--seed", "42"], input="")
    assert result.exit_code == 1
    assert not result.stdout.strip()


def test_ship_generate_interactive_hull_flag_pre_answers_the_prompt():
    """A flag and a prompt must not ask the same thing twice."""
    prompted = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "200", "--seed", "42"],
        input=_ENTER_THROUGH,
    )
    flagged = runner.invoke(app, ["ship", "generate", "--hull", "200", "--seed", "42"])

    assert prompted.exit_code == 0
    assert "Hull tonnage" not in prompted.stderr
    assert prompted.stdout == flagged.stdout


def test_ship_generate_interactive_small_craft_hull_flag_pre_answers_the_prompt():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--hull", "40", "--seed", "7"],
        input=_small_craft_answers(skip=("hull",)),
    )
    assert result.exit_code == 0
    assert "Hull tonnage" not in result.stderr
    assert "40-ton hull" in result.stdout


# --- small craft descriptions (T045, FR-026, FR-027) ---

_FIGHTER_TOML = "tests/data/ships/fighter.toml"


def test_ship_generate_small_craft_prints_a_jump_free_description():
    result = runner.invoke(
        app, ["ship", "generate", "--small-craft", "--hull", "40", "--seed", "7"]
    )
    assert result.exit_code == 0

    lines = _description_lines(result.stdout)
    assert len(lines) == 3
    assert lines[0].startswith("TL")
    assert lines[1] == ""
    assert "40-ton hull" in lines[2]
    assert "is a small craft." in lines[2]
    assert "cockpit" in lines[2]
    assert "jump" not in lines[2].lower()


# --- T012 (US1): `cetools ship generate` names the ship (FR-012, SC-004) ---


def test_ship_generate_names_the_ship_no_unnamed_ship():
    result = runner.invoke(app, ["ship", "generate", "--seed", "42"])
    assert result.exit_code == 0

    lines = _description_lines(result.stdout)
    assert "Unnamed Ship" not in lines[0]
    assert lines[0].split(" ", 1)[1]


def test_ship_generate_small_craft_names_the_ship_no_unnamed_ship():
    result = runner.invoke(app, ["ship", "generate", "--small-craft", "--seed", "7"])
    assert result.exit_code == 0

    lines = _description_lines(result.stdout)
    assert "Unnamed Ship" not in lines[0]
    assert lines[0].split(" ", 1)[1]


def test_ship_generate_toml_carries_a_name_key():
    result = runner.invoke(app, ["ship", "generate", "--seed", "42", "--toml"])
    assert result.exit_code == 0
    assert 'name = "' in result.stdout


# --- T038, T039 (US3): the displayed == accepted invariant (contract §7) ---
#
# One table of (accessor, reader) rows, driven directly against the private
# readers in `cetools.cli.ship` rather than through a scripted session: the
# invariant is about what a reader *accepts*, and the exact prompt text each
# accessor produces is already pinned, string for string, by Phase 3 and 4's
# tests. A row per narrowing state a hull-dependent prompt can reach, per the
# contract.


def _closed_row(row_id, raw_values, reader, reader_name, *, kind, takes_known, none=False, refuse):
    """One row: the accessor's raw values, and a single-argument `accept`
    bound to the reader that checks them—so the same call answers "is this
    value accepted" for every clause of the invariant."""
    raw_values = tuple(raw_values)
    known = (
        [prompts.spell(v) for v in raw_values]
        if kind == "word"
        else list(prompts.numbers(raw_values))
    )
    if none:
        known = known + ["none"]
    accept = (lambda answer, _known=known: reader(_known, answer)) if takes_known else reader
    return {
        "id": row_id,
        "kind": kind,
        "raw_values": raw_values,
        "none": none,
        "known": known,
        "accept": accept,
        "refuse_answer": refuse,
        "reader_name": reader_name,
    }


_ARMOR_TYPE_KNOWN = [prompts.spell(kind.value) for kind in ArmorType]


def _accept_armor(answer: str) -> None:
    """The armour type alone, typed back; the percent is the free part FR-002
    excludes from the count, so a fixed one is appended for the reader."""
    ship._read_armor(_ARMOR_TYPE_KNOWN, f"{answer} 15")


_SMALL_CRAFT_WEAPON_HULL_TONS = 40
_SMALL_CRAFT_WEAPON_POWER_RATING = 3
_SMALL_CRAFT_WEAPON_MOUNT = "triple"
_SMALL_CRAFT_WEAPON_VALUES = small_craft_weapons(
    _SMALL_CRAFT_WEAPON_HULL_TONS, _SMALL_CRAFT_WEAPON_POWER_RATING, _SMALL_CRAFT_WEAPON_MOUNT
)
_SMALL_CRAFT_WEAPON_KNOWN = [prompts.spell(v) for v in _SMALL_CRAFT_WEAPON_VALUES]


def _accept_small_craft_weapon(answer: str) -> None:
    ship._read_small_craft_weapon(
        _SMALL_CRAFT_WEAPON_KNOWN,
        _SMALL_CRAFT_WEAPON_HULL_TONS,
        _SMALL_CRAFT_WEAPON_POWER_RATING,
        _SMALL_CRAFT_WEAPON_MOUNT,
        answer,
    )


_ACCEPTABLE_VALUES_TABLE = [
    _closed_row(
        "hull_class",
        [c.value for c in HullClass],
        ship._read_hull_class,
        "_read_hull_class",
        kind="word",
        takes_known=True,
        refuse="battleship",
    ),
    _closed_row(
        "configuration",
        [c.value for c in Configuration],
        ship._read_configuration,
        "_read_configuration",
        kind="word",
        takes_known=True,
        refuse="wedge",
    ),
    _closed_row(
        "hull_tonnage_starship",
        hull_tonnages(HullClass.STARSHIP),
        partial(ship._read_hull_tons, HullClass.STARSHIP),
        "_read_hull_tons",
        kind="number",
        takes_known=False,
        refuse="150",
    ),
    _closed_row(
        "hull_tonnage_small_craft",
        hull_tonnages(HullClass.SMALL_CRAFT),
        partial(ship._read_hull_tons, HullClass.SMALL_CRAFT),
        "_read_hull_tons",
        kind="number",
        takes_known=False,
        refuse="200",
    ),
    _closed_row(
        "jump_rating_narrowed",
        available_ratings(HullClass.STARSHIP, 400),
        partial(ship._read_rating, HullClass.STARSHIP, 400, Drive.JUMP, None),
        "_read_rating",
        kind="number",
        takes_known=False,
        refuse="9",
    ),
    _closed_row(
        "jump_rating_unnarrowed",
        available_ratings(HullClass.STARSHIP, None),
        partial(ship._read_rating, HullClass.STARSHIP, None, Drive.JUMP, None),
        "_read_rating",
        kind="number",
        takes_known=False,
        refuse="9",
    ),
    _closed_row(
        "maneuver_rating_narrowed",
        available_ratings(HullClass.STARSHIP, 400),
        partial(ship._read_maneuver_rating, HullClass.STARSHIP, 400),
        "_read_maneuver_rating",
        kind="number",
        takes_known=False,
        refuse="9",
    ),
    _closed_row(
        "maneuver_rating_unnarrowed",
        available_ratings(HullClass.STARSHIP, None),
        partial(ship._read_maneuver_rating, HullClass.STARSHIP, None),
        "_read_maneuver_rating",
        kind="number",
        takes_known=False,
        refuse="9",
    ),
    _closed_row(
        "maneuver_rating_narrowed_small_craft",
        small_craft_maneuver_ratings(40),
        partial(ship._read_maneuver_rating, HullClass.SMALL_CRAFT, 40),
        "_read_maneuver_rating",
        kind="number",
        takes_known=False,
        refuse="4",
    ),
    _closed_row(
        "power_rating_narrowed",
        available_ratings(HullClass.STARSHIP, 400),
        partial(ship._read_power_rating, HullClass.STARSHIP, 400, None, None),
        "_read_power_rating",
        kind="number",
        takes_known=False,
        refuse="9",
    ),
    _closed_row(
        "power_rating_unnarrowed",
        available_ratings(HullClass.STARSHIP, None),
        partial(ship._read_power_rating, HullClass.STARSHIP, None, None, None),
        "_read_power_rating",
        kind="number",
        takes_known=False,
        refuse="9",
    ),
    _closed_row(
        "power_rating_narrowed_small_craft",
        small_craft_power_ratings(15, 1),
        partial(ship._read_power_rating, HullClass.SMALL_CRAFT, 15, 1, 1),
        "_read_power_rating",
        kind="number",
        takes_known=False,
        refuse="4",
    ),
    {
        "id": "armor",
        "kind": "word",
        "raw_values": tuple(kind.value for kind in ArmorType),
        "none": False,
        "known": _ARMOR_TYPE_KNOWN,
        "accept": _accept_armor,
        "refuse_answer": "adamantium",
        "reader_name": "_read_armor",
    },
    _closed_row(
        "armor_options",
        armor_options(),
        ship._read_armor_options,
        "_read_armor_options",
        kind="word",
        takes_known=True,
        refuse="bogus",
    ),
    _closed_row(
        "computer",
        computer_models(),
        ship._read_computer,
        "_read_computer",
        kind="number",
        takes_known=True,
        none=True,
        refuse="99",
    ),
    _closed_row(
        "electronics",
        electronics_packages(),
        ship._read_electronics,
        "_read_electronics",
        kind="word",
        takes_known=True,
        none=True,
        refuse="psychic",
    ),
    _closed_row(
        "fitting",
        fitting_kinds(),
        ship._read_fitting,
        "_read_fitting",
        kind="word",
        takes_known=True,
        none=True,
        refuse="swimming_pool",
    ),
    _closed_row(
        "bay",
        bay_kinds(),
        ship._read_bay,
        "_read_bay",
        kind="word",
        takes_known=True,
        none=True,
        refuse="railgun",
    ),
    _closed_row(
        "screen",
        screen_kinds(),
        ship._read_screen,
        "_read_screen",
        kind="word",
        takes_known=True,
        none=True,
        refuse="deflector",
    ),
    _closed_row(
        "turret_mount",
        turret_mounts(),
        ship._read_turret_mount,
        "_read_turret_mount",
        kind="word",
        takes_known=True,
        refuse="swivel",
    ),
    _closed_row(
        "turret_weapon",
        turret_weapons(),
        ship._read_turret_weapon,
        "_read_turret_weapon",
        kind="word",
        takes_known=True,
        refuse="beam_laser",
    ),
    {
        "id": "turret_weapon_small_craft_narrowed",
        "kind": "word",
        "raw_values": tuple(_SMALL_CRAFT_WEAPON_VALUES),
        "none": False,
        "known": _SMALL_CRAFT_WEAPON_KNOWN,
        "accept": _accept_small_craft_weapon,
        "refuse_answer": "laser_cannon",
        "reader_name": "_read_small_craft_weapon",
    },
    _closed_row(
        "turret_count_narrowed",
        range(1, hardpoints(HullClass.STARSHIP, 200) + 1),
        partial(ship._read_turret_count, HullClass.STARSHIP, 200),
        "_read_turret_count",
        kind="number",
        takes_known=False,
        none=True,
        refuse="5",
    ),
    _closed_row(
        "turret_count_unnarrowed",
        range(1, hardpoints(HullClass.STARSHIP, None) + 1),
        partial(ship._read_turret_count, HullClass.STARSHIP, None),
        "_read_turret_count",
        kind="number",
        takes_known=False,
        none=True,
        refuse="51",
    ),
]


@pytest.mark.parametrize(
    "row", _ACCEPTABLE_VALUES_TABLE, ids=[row["id"] for row in _ACCEPTABLE_VALUES_TABLE]
)
def test_acceptable_values_invariant(row):
    """Contract §7's four clauses, per row."""
    accept = row["accept"]
    raw_values = row["raw_values"]

    # 1. Every displayed value, typed back verbatim, is accepted.
    for value in raw_values:
        accept(prompts.spell(value))
    if row["none"]:
        accept("none")

    # 2. Its stored and hyphenated spellings are accepted (word rows only—a
    #    number has no alternate spelling).
    if row["kind"] == "word":
        for value in raw_values:
            accept(value)
            accept(prompts.spell(value).replace(" ", "-"))

    # 3. The displayed set equals the accessor's set, expanded rather than
    #    left as range notation (a `1-6` contributes six values, not one).
    expected_known = (
        [prompts.spell(v) for v in raw_values]
        if row["kind"] == "word"
        else list(prompts.numbers(raw_values))
    )
    if row["none"]:
        expected_known = expected_known + ["none"]
    assert row["known"] == expected_known

    # 4. A value outside the set is refused, naming the set in the displayed
    #    spelling and the displayed notation.
    with pytest.raises(ValueError) as excinfo:
        accept(row["refuse_answer"])
    assert ", ".join(row["known"]) in str(excinfo.value)


_OPEN_OR_OUTSIDE_SEC7_READERS = frozenset(
    {
        "_read_staterooms",  # FR-006: open answer, §2 not §1
        "_read_name",  # FR-006: open answer, §2 not §1
        "_read_purpose",  # FR-006: open answer, §2 not §1
        "_read_fields",  # §3's revise prompt, outside §7's closed-set scope
        "_read_verdict",  # §3's accept-or-revise prompt, outside §7's scope
    }
)


def test_acceptable_values_table_covers_every_closed_set_reader_in_ship_py():
    """The completeness half of Decision 5: a question added to `ship.py`
    without a row here fails this test rather than escaping silently."""
    all_readers = {
        name
        for name, obj in inspect.getmembers(ship, inspect.isfunction)
        if name.startswith("_read_") and obj.__module__ == ship.__name__
    }
    covered = {row["reader_name"] for row in _ACCEPTABLE_VALUES_TABLE}
    accounted_for = covered | _OPEN_OR_OUTSIDE_SEC7_READERS
    assert all_readers == accounted_for


def test_ship_build_fighter_prints_a_jump_free_description():
    result = runner.invoke(app, ["ship", "build", _FIGHTER_TOML])
    assert result.exit_code == 0

    lines = _description_lines(result.stdout)
    assert len(lines) == 3
    assert lines[0] == "TL8 Wasp"
    assert lines[1] == ""
    assert "the Wasp is a small craft." in lines[2]
    assert (
        "It mounts maneuver drive sB and power plant sG, "
        "giving a performance of 1-G acceleration."
    ) in lines[2]
    assert "Fuel tankage of 7.3 tons supports the power plant for one week." in lines[2]
    assert "jump" not in lines[2].lower()
    # A fractional capacity renders in digits, never as a word (FR-022b).
    assert "Cargo capacity is 6.2 tons." in lines[2]
