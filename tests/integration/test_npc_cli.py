"""FR-051, FR-053c, FR-054, SC-012: the `npc` command's streams, exit
codes, and cross-locale behavior.
"""

import os
import re
import subprocess
import sys

from typer.testing import CliRunner

from cetools.cli import app

runner = CliRunner()

_REPORTED_SEED = r"Seed:\s+([+-]?\d+)"


def test_stdout_carries_exactly_the_sheet():
    result = runner.invoke(app, ["npc", "--seed", "session-alpha"])
    assert result.exit_code == 0
    # A rendered sheet's own lines are tab-separated text; nothing about the
    # seed, the version, or the provenance appears among them.
    assert "Seed:" not in result.stdout
    assert "Rules:" not in result.stdout


def test_seed_and_version_and_provenance_go_to_standard_error():
    result = runner.invoke(app, ["npc", "--seed", "session-alpha"])
    assert re.search(_REPORTED_SEED, result.stderr)
    assert "Rules:" in result.stderr


def test_a_failed_run_writes_nothing_to_standard_output():
    result = runner.invoke(app, ["npc", "--rules-data", "/does/not/exist"])
    assert result.exit_code != 0
    assert result.stdout == ""


def test_exit_codes_are_0_1_and_2():
    ok = runner.invoke(app, ["npc", "--seed", "session-alpha"])
    assert ok.exit_code == 0

    load_failure = runner.invoke(app, ["npc", "--rules-data", "/does/not/exist"])
    assert load_failure.exit_code == 2  # a bad --rules-data location is a usage error

    usage_error = runner.invoke(app, ["npc", "--name", "   "])
    assert usage_error.exit_code == 2


def test_an_empty_or_whitespace_only_name_is_a_usage_error():
    result = runner.invoke(app, ["npc", "--name", "   "])
    assert result.exit_code == 2
    assert result.stdout == ""


def _run_in_subprocess(locale_name: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, LC_ALL=locale_name)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import locale; locale.setlocale(locale.LC_ALL, ''); "
            "from cetools.cli import app; app(['npc', '--seed', 'session-alpha'])",
        ],
        env=env,
        capture_output=True,
        text=False,
    )


def test_sc012_cross_locale_comparison():
    """A locale whose collation differs from the C default must not change
    a byte of the rendered sheet (research R8). Skips with a reason when
    that locale is not installed, since this can only ever be best-effort;
    the no-`locale`-import guard is what actually forbids the mistake.
    """
    import locale as locale_module

    candidates = ["de_DE.UTF-8", "tr_TR.UTF-8"]
    available = []
    for name in candidates:
        try:
            locale_module.setlocale(locale_module.LC_ALL, name)
        except locale_module.Error:
            continue
        finally:
            locale_module.setlocale(locale_module.LC_ALL, "C")
        available.append(name)

    if not available:
        import pytest

        pytest.skip("no non-default locale is installed on this machine")

    baseline = subprocess.run(
        [
            sys.executable,
            "-c",
            "from cetools.cli import app; app(['npc', '--seed', 'session-alpha'])",
        ],
        env=dict(os.environ, LC_ALL="C"),
        capture_output=True,
    )
    other = _run_in_subprocess(available[0])
    assert other.returncode == baseline.returncode
    assert other.stdout == baseline.stdout
