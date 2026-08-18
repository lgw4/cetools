import os
import re
import tempfile
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
    "cetools rules data, every .toml file under (src/cetools/data/) as distributed in "
    "source and under (cetools/data/) as installed, Copyright 2026, the cetools "
    "contributors.",
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


_NOTICE_PATH = re.compile(r"\(([^()]+)\)")
_NOTICE_SUFFIX = re.compile(r"every (\.[a-z0-9]+) file")


@pytest.fixture
def game_data_covered_paths(section_15_notices) -> tuple[str, ...]:
    """The paths this project's own game-data notice names.

    Read out of the notice rather than written into a test, because SC-016
    requires the coverage check to derive what must be covered from what is
    actually shipped. A check that globs the covered directory and then
    asserts every result sits under it is true by construction, which is the
    tautology FR-047 exists to remove. Shared by the working-tree guard in
    `tests/unit/test_licensing.py` and the built-artifact guards in
    `tests/guards/test_packaging.py`, which differ only in where they get the
    file list.

    The notice names two, because the content ships at two paths: a wheel
    holds `cetools/data/` and nothing called `src/`, so a notice naming only
    the source path named a path that exists in no wheel, and the wheel guard
    had to fabricate the prefix as `f"src/{name}"` to make its own check line
    up — papering over the mismatch rather than reporting it.
    """
    covered = tuple(_NOTICE_PATH.findall(section_15_notices[-1]))
    assert covered, "the game-data notice names no path, so it covers nothing"
    return covered


@pytest.fixture
def game_data_covered_suffix(section_15_notices) -> str:
    """The extension the game-data notice qualifies its directories with.

    Read out of the notice for the same reason the paths are. The notice
    designates every `.toml` file under the data directory rather than the
    directory entire, because `src/cetools/data/__init__.py` ships there and
    is Python source, which CONTRIBUTING.md licenses as GPL-3.0 and which
    Open Game Content cannot be sublicensed under. Nothing copyrightable is
    double-licensed today — the file is empty — but the constitution requires
    the designation to be unambiguous, and a check that read only the
    directory prefix would call any file placed there covered.
    """
    match = _NOTICE_SUFFIX.search(section_15_notices[-1])
    assert match, "the game-data notice does not say which files it covers"
    return match.group(1)


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
    """A command's `--help` screen as plain text, escapes already stripped and
    rendered wide enough that nothing is elided.

    Takes the command as a list, so `help_text([])` is the top-level screen
    and `help_text(["check"])` is a subcommand's.

    `COLUMNS` is forced here rather than at each call site. Rich sizes its box
    to the terminal and *truncates* an argument's help with an ellipsis when
    it does not fit, so at the default eighty columns a search for the second
    half of a help string finds nothing while the string is perfectly present.
    That is the same shape of trap as the ANSI escapes above — an assertion
    that passes or fails on how the output happened to be drawn — and it is
    settled in the same place, so no test has to remember it.
    """
    from typer.testing import CliRunner

    from cetools.cli import app

    runner = CliRunner()

    def _help(command: list[str]) -> str:
        result = runner.invoke(app, [*command, "--help"], env={"COLUMNS": "200"})
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


# The override tests reach for two POSIX facilities to build the inputs they
# pin, and neither is available everywhere the suite runs: CI covers Windows
# as well as Linux and macOS, and the whole suite may be run as root. Both are
# settled here for the same reason the ANSI escapes above are — the trap had
# already caught four test modules, and the alternative is nine copies of a
# platform condition that has to stay in agreement with itself.


def _posix_special_files_exist() -> bool:
    """Whether this platform has FIFOs and device nodes at all.

    `os.mkfifo` is simply absent on Windows, and a path such as `/dev/zero`
    names nothing there, so a test that builds a directory entry which is
    neither a regular file nor a directory has no input to build.
    """
    return hasattr(os, "mkfifo")


def _chmod_denials_are_enforced() -> bool:
    """Whether `chmod(0o000)` actually denies *this* process access.

    Root ignores the mode entirely, and Windows has no POSIX mode bits for
    `Path.chmod` to clear — there it toggles the read-only attribute, which
    stops neither a read nor a directory listing. Probing for the denial beats
    naming the two cases, because the denial is what these tests need; a
    filesystem that grants access for some third reason is caught too, rather
    than skipped only where someone thought to look.
    """
    with tempfile.TemporaryDirectory() as name:
        locked_dir = Path(name) / "dir"
        locked_dir.mkdir()
        locked_file = Path(name) / "file"
        locked_file.write_bytes(b"")
        try:
            locked_dir.chmod(0o000)
            locked_file.chmod(0o000)
            try:
                list(locked_dir.iterdir())
                locked_file.read_bytes()
            except OSError:
                return True
            return False
        finally:
            # Restored unconditionally: on Windows a read-only entry defeats
            # the temporary directory's own cleanup.
            locked_dir.chmod(0o700)
            locked_file.chmod(0o600)


_UNMET_REQUIREMENTS = {
    "needs_posix_special_files": (
        None
        if _posix_special_files_exist()
        else "this platform has no FIFOs or device nodes to point an override at"
    ),
    "needs_enforced_chmod": (
        None
        if _chmod_denials_are_enforced()
        else "chmod(0o000) does not deny this process access, so there is nothing to report"
    ),
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        for marker, reason in _UNMET_REQUIREMENTS.items():
            if reason is not None and marker in item.keywords:
                item.add_marker(pytest.mark.skip(reason=reason))
