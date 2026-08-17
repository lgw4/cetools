import re
from pathlib import Path

import pytest

SEEDED_LITERAL = "session-alpha"

# Typer forces Rich's color mode on whenever GITHUB_ACTIONS, FORCE_COLOR, or
# PY_COLORS is set, and Rich styles an option's first dash separately from the
# rest: `\x1b[1;36m-\x1b[0m\x1b[1;36m-seed\x1b[0m`. The escape codes land
# *between* the dashes, so `--seed` is never contiguous text and a plain
# `"--seed" in stdout` finds nothing at all. Any assertion against captured CLI
# output has to strip them first, or it passes locally and fails on every CI
# runner. These live here, rather than in the module that first needed them,
# because that trap has now caught out two test modules and silently weakened a
# third: the licensing guard searches help screens for a trademark, and styling
# that split the phrase would hide it from the search.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_OPTION_TOKEN = re.compile(r"--[a-z][a-z0-9-]*")

# Golden files and JSON fixtures hold the installed package version as this
# placeholder rather than the literal, so a release rewrites none of them
# (SC-009). The `normalize_version` fixture substitutes it back in at
# comparison time.
VERSION_PLACEHOLDER = "{VERSION}"

# The SRD's Section 15 copyright-notice chain, whitespace-normalized, in the
# order it must appear. The constitution requires it "verbatim" and "complete",
# so these are literals: deriving them from `LICENSE-OGL.txt` would only assert
# the file agrees with itself. The last entry is this project's own game-data
# line, which the constitution requires the inherited chain be extended with.
SECTION_15_NOTICES = (
    "Open Game License v 1.0a Copyright 2000, Wizards of the Coast, Inc.",
    "High Guard System Reference Document Copyright © 2008, Mongoose Publishing.",
    "Mercenary System Reference Document Copyright © 2008, Mongoose Publishing.",
    "Modern System Reference Document Copyright 2002-2004, Wizards of the Coast, "
    "Inc.; Authors Bill Slavicsek, Jeff Grubb, Rich Redman, Charles Ryan, Eric "
    "Cagle, David Noonan, Stan!, Christopher Perkins, Rodney Thompson, and JD "
    "Wiker, based on material by Jonathan Tweet, Monte Cook, Skip Williams, "
    "Richard Baker, Peter Adkison, Bruce R. Cordell, John Tynes, Andy Collins, and "
    "JD Wiker.",
    "Swords & Wizardry Core Rules, Copyright 2008, Matthew J. Finch",
    "System Reference Document, Copyright 2000, Wizards of the Coast, Inc.; "
    "Authors Jonathan Tweet, Monte Cook, Skip Williams, based on original material "
    "by E. Gary Gygax and Dave Arneson.",
    "T20 - The Traveller's Handbook Copyright 2002, Quiklink Interactive, Inc. "
    "Traveller is a trademark of Far Future Enterprises and is used under license.",
    "Traveller System Reference Document Copyright © 2008, Mongoose Publishing.",
    "Traveller is © 2008 Mongoose Publishing. Traveller and related logos, "
    "character, names, and distinctive likenesses thereof are trademarks of Far "
    "Future Enterprises unless otherwise noted. All Rights Reserved. Mongoose "
    "Publishing Ltd Authorized User.",
    "Cepheus Engine System Reference Document, Copyright © 2016 Samardan Press; "
    'Author Jason "Flynn" Kemp.',
    "cetools rules data (src/cetools/data/), Copyright 2026, the cetools " "contributors.",
)


def _assert_section_15_chain(text: str, where: str) -> None:
    """Assert `text` carries the whole Section 15 chain, in order.

    A heading check alone would let any single notice be deleted, which is
    exactly what the OGL forbids: the chain travels with the content.
    """
    normalized = " ".join(text.split())
    position = -1
    for notice in SECTION_15_NOTICES:
        found = normalized.find(notice)
        assert found != -1, f"{where} is missing the Section 15 notice: {notice[:60]}..."
        assert found > position, f"{where} has Section 15 out of order at: {notice[:60]}..."
        position = found


@pytest.fixture
def assert_section_15_chain():
    """The chain checker, shared by the source-tree and built-artifact guards."""
    return _assert_section_15_chain


@pytest.fixture
def section_15_notices() -> tuple[str, ...]:
    return SECTION_15_NOTICES


@pytest.fixture(autouse=True)
def _clear_rules_cache():
    from cetools.rules import load_rules

    load_rules.cache_clear()
    yield
    load_rules.cache_clear()


@pytest.fixture
def strip_ansi():
    """Remove Rich's styling escapes from captured CLI output."""

    def _strip(text: str) -> str:
        return _ANSI.sub("", text)

    return _strip


@pytest.fixture
def help_text(strip_ansi):
    """A command's `--help` screen as plain text, escapes already stripped.

    Takes the command as a list, so `help_text([])` is the top-level screen
    and `help_text(["check"])` is a subcommand's.
    """
    from typer.testing import CliRunner

    from cetools.cli import app

    runner = CliRunner()

    def _help(command: list[str]) -> str:
        result = runner.invoke(app, [*command, "--help"])
        assert result.exit_code == 0, f"{command} --help exited {result.exit_code}"
        return strip_ansi(result.stdout)

    return _help


@pytest.fixture
def options_in_help(help_text):
    """The set of long options a command's `--help` lists."""

    def _options(command: list[str]) -> set[str]:
        plain = help_text(command)
        found = set(_OPTION_TOKEN.findall(plain))
        # An empty set means the help screen was not parsed, not that the
        # command has no options; without this the caller's comparison reports
        # a confusing "set() != {...}" instead of what the runner returned.
        assert found, f"no option tokens found in help output: {plain!r}"
        return found

    return _options


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def seeded_roller():
    from cetools import Roller

    return Roller(SEEDED_LITERAL)


@pytest.fixture
def read_golden():
    golden_dir = Path(__file__).resolve().parent / "golden"

    def _read(name: str) -> str:
        return (golden_dir / name).read_text(encoding="utf-8")

    return _read


@pytest.fixture
def normalize_version():
    """Substitute VERSION_PLACEHOLDER in golden/fixture text with the installed version."""
    from importlib.metadata import version

    installed = version("cetools")

    def _normalize(text: str) -> str:
        return text.replace(VERSION_PLACEHOLDER, installed)

    return _normalize
