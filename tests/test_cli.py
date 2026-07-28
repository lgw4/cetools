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


_ENTER_THROUGH = "\n" * 12
"""More Enters than the wizard has questions, so a test that means "take every
default" keeps meaning that as later tickets add prompts."""

_QUESTIONS = ("hull", "jump", "maneuver", "power", "armor")
"""The wizard's questions, in the order it asks them.

Piped input is positional, so every test that answers one question has to know
where the others sit. Keeping that knowledge here means a ticket which adds a
question edits one line rather than every test that answers a later one.
"""


def _answers(*, skip: tuple[str, ...] = (), **given: str) -> str:
    """Piped input answering the named questions and pressing Enter through the rest.

    `skip` names questions this invocation never asks, because a flag already
    pre-answered them: `--hull` means the hull question is not asked, and every
    answer after it would otherwise land one slot early.
    """
    unknown = (set(given) | set(skip)) - set(_QUESTIONS)
    assert not unknown, f"no such question: {sorted(unknown)}"
    asked = (question for question in _QUESTIONS if question not in skip)
    return "".join(f"{given.get(question, '')}\n" for question in asked) + _ENTER_THROUGH


def test_ship_generate_interactive_asks_for_each_drive_as_a_rating():
    """A referee answers Jump-2, not drive C: the question is the rating."""
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "7"], input=_ENTER_THROUGH
    )
    assert result.exit_code == 0
    assert "Jump rating [roll]:" in result.stderr
    assert "Maneuver rating [roll]:" in result.stderr
    assert "Power plant rating [roll]:" in result.stderr


def test_ship_generate_interactive_pins_a_jump_rating_to_its_lightest_code():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3", "--toml"],
        input="1" + _ENTER_THROUGH,
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
        input="1\n3" + _ENTER_THROUGH,
    )
    assert result.exit_code == 0
    assert "Power plant rating (at least 3) [roll]:" in result.stderr


def test_ship_generate_interactive_power_below_its_floor_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3"],
        input="2\n3\n1\n3" + _ENTER_THROUGH,
    )
    assert result.exit_code == 0
    assert "power plant rating 1 is below the 3 its drives require" in result.stderr
    assert result.stderr.count("Power plant rating (at least 3) [roll]:") == 2


def test_ship_generate_interactive_power_floor_holds_when_only_one_drive_is_pinned():
    """A floor known in part is still a floor: Jump-2 alone puts the plant at 2,
    even with the manoeuvre drive left to the dice.

    It is only a partial floor, and this seed shows the limit: the manoeuvre
    drive rolls a 5, so a plant at 2 clears the prompt and is refused by
    `build_ship`, which is the authority. The revise loop that turns that into
    another question rather than an exit is #51.
    """
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3"],
        input=_answers(skip=("hull",), jump="2", power="1\n2"),
    )
    assert "Power plant rating (at least 2) [roll]:" in result.stderr
    assert "power plant rating 1 is below the 2 its drives require" in result.stderr

    assert result.exit_code == 1
    assert "power plant rating 2 below required 5" in result.stderr


def test_ship_generate_interactive_untabulated_rating_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--hull", "400", "--seed", "3"],
        input="9\n1" + _ENTER_THROUGH,
    )
    assert result.exit_code == 0
    assert "jump rating 9 is not tabulated for a 400-ton hull" in result.stderr
    assert result.stderr.count("Jump rating [roll]:") == 2


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
    assert "not tabulated for any starship hull" in result.stderr


def test_ship_generate_interactive_asks_for_armor_showing_its_default():
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "7"], input=_ENTER_THROUGH
    )
    assert result.exit_code == 0
    assert "Armor [roll]:" in result.stderr


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
    assembly (ADR-0001). The revise loop that catches this is #51.
    """
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(armor="crystaliron 7"),
    )
    assert result.exit_code == 1
    assert "armor must be added in 5% increments" in result.stderr
    assert result.stderr.count("Armor [roll]:") == 1


def test_ship_generate_interactive_unknown_armor_type_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "7"],
        input=_answers(armor="adamantium 10\ncrystaliron 10"),
    )
    assert result.exit_code == 0
    assert "adamantium is not a known armor type" in result.stderr
    assert result.stderr.count("Armor [roll]:") == 2


def test_ship_generate_interactive_asks_for_the_hull_tonnage_showing_its_default():
    result = runner.invoke(
        app, ["ship", "generate", "--interactive", "--seed", "42"], input=_ENTER_THROUGH
    )
    assert result.exit_code == 0
    assert "Hull tonnage [roll]:" in result.stderr


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
        app, ["ship", "generate", "--interactive", "--seed", "42"], input="200" + _ENTER_THROUGH
    )
    assert result.exit_code == 0
    assert "200-ton hull" in result.stdout


def test_ship_generate_interactive_untabulated_tonnage_is_reasked_with_the_reason():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "42"],
        input="150\n200" + _ENTER_THROUGH,
    )
    assert result.exit_code == 0
    assert "150 tons is not a tabulated hull size" in result.stderr
    assert result.stderr.count("Hull tonnage [roll]:") == 2
    assert "200-ton hull" in result.stdout


def test_ship_generate_interactive_a_non_numeric_answer_is_reasked():
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--seed", "42"],
        input="biggish\n200" + _ENTER_THROUGH,
    )
    assert result.exit_code == 0
    assert "biggish is not a number of tons" in result.stderr
    assert "200-ton hull" in result.stdout


def test_ship_generate_interactive_small_craft_rejects_a_starship_tonnage():
    """The prompt validates against the ruleset in play, not against hulls at large."""
    result = runner.invoke(
        app,
        ["ship", "generate", "--interactive", "--small-craft", "--seed", "7"],
        input="200\n40" + _ENTER_THROUGH,
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
        input=_ENTER_THROUGH,
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
