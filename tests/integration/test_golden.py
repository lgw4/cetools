from pathlib import Path

import pytest
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


def test_check_difficult_matches_golden_file(read_golden, normalize_version):
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
    assert result.stdout == normalize_version(read_golden("check_difficult.txt"))


def test_check_unskilled_matches_golden_file(read_golden, normalize_version):
    result = runner.invoke(app, ["check", "--seed", "1"])
    assert result.exit_code == 0
    assert result.stdout == normalize_version(read_golden("check_unskilled.txt"))


# --- SC-009: comparison against the frozen pre-loader evidence ---


def _pre_loader(name: str) -> str:
    return (Path(__file__).resolve().parent.parent / "golden" / "pre-loader" / name).read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("name", ["roll_1d6.txt", "roll_2d6_plus1.txt", "roll_d66.txt"])
def test_sc009_roll_goldens_are_byte_identical_to_the_pre_loader_evidence(name, read_golden):
    assert read_golden(name) == _pre_loader(name)


@pytest.mark.parametrize(
    "args,name",
    [
        (
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
            "check_difficult.txt",
        ),
        (["check", "--seed", "1"], "check_unskilled.txt"),
    ],
)
def test_sc009_check_goldens_equal_pre_loader_evidence_plus_exactly_the_provenance_block(
    args, name, normalize_version
):
    result = runner.invoke(app, args)
    assert result.exit_code == 0

    before = _pre_loader(name).splitlines()
    after = normalize_version(result.stdout).splitlines()

    # Every line the pre-loader output had is unchanged, in the same order,
    # and exactly one line (the provenance block) is added at the end.
    assert after[: len(before)] == before
    assert len(after) == len(before) + 1
    assert after[-1].startswith("  Rules: ")


def test_sc009_check_difficult_fields_are_unchanged_field_by_field(normalize_version):
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
    before = _pre_loader("check_difficult.txt")
    after = normalize_version(result.stdout)
    for field in (
        "1, 5 (sum 6)",  # dice
        "Difficulty (Difficult) -2",
        "Characteristic 9       +1",
        "Skill 2                +2",
        "cover                  -2",
        "5 vs target 8",  # total vs target
        "14333185781139156525",  # seed
        "FAILURE",  # outcome
    ):
        assert field in before
        assert field in after


# --- the worked examples in README.md, which ship as the PyPI description ---


def _readme_blocks() -> dict[str, str]:
    """Every `$ cetools ...` invocation in README.md with the output shown
    beneath it, keyed by the command line.

    The README is the `Description` in both the wheel's METADATA and the
    sdist's PKG-INFO, so it is what PyPI renders. The project's own rule is
    that changing human-readable CLI output means updating the committed
    reference output in the same commit, and the one command whose output this
    feature changed was documented as it was before the change: the `check`
    block was byte-for-byte the *pre-loader* golden while the real command had
    carried one line more since the provenance block landed.
    """
    lines = (
        (Path(__file__).resolve().parents[2] / "README.md")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    blocks: dict[str, str] = {}
    index = 0
    while index < len(lines):
        if not lines[index].startswith("$ "):
            index += 1
            continue
        command = lines[index][2:]
        index += 1
        # A command line long enough to wrap is continued with a backslash.
        while command.endswith("\\"):
            command = command[:-1].rstrip() + " " + lines[index].strip()
            index += 1
        output: list[str] = []
        while index < len(lines) and lines[index].strip() and not lines[index].startswith("```"):
            output.append(lines[index])
            index += 1
        blocks[command] = "\n".join(output) + "\n"
    return blocks


README_EXAMPLES = {
    "cetools roll 2d6+1 --seed session-alpha": ["roll", "2d6+1", "--seed", "session-alpha"],
    "cetools roll d66 --seed session-alpha": ["roll", "d66", "--seed", "session-alpha"],
    "cetools check --difficulty Difficult --characteristic 9 --skill 2 "
    '--dm "cover=-2" --seed session-alpha': [
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
    "cetools validate": ["validate"],
}


def test_every_documented_example_is_actually_parsed_out_of_the_readme():
    """A parser that matched nothing would make every case below vacuous."""
    blocks = _readme_blocks()
    assert set(README_EXAMPLES) <= set(blocks), sorted(set(README_EXAMPLES) - set(blocks))


@pytest.mark.parametrize("documented", sorted(README_EXAMPLES))
def test_the_readme_shows_what_the_command_actually_prints(documented):
    result = runner.invoke(app, README_EXAMPLES[documented])
    assert result.exit_code == 0
    assert _readme_blocks()[documented] == result.stdout
