"""FR-051, FR-053c, FR-053d, FR-054, SC-012: the `npc` command's streams,
exit codes, and cross-locale behavior.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cetools.cli import app

runner = CliRunner()

_NAVY = (
    Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"
).read_text(encoding="utf-8")
_DATA = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data"
_MISHAPS = (_DATA / "chargen" / "mishaps.toml").read_text(encoding="utf-8")
_CHARGEN_PARAMETERS = (_DATA / "chargen" / "chargen-parameters.toml").read_text(encoding="utf-8")

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


@pytest.mark.parametrize("mode", [[], ["--json"]], ids=["text", "json"])
def test_inconsistent_override_data_fails_before_any_character_exists(tmp_path, mode):
    broken = _NAVY.replace('"Comms"', '"Coms"', 1)
    (tmp_path / "navy.toml").write_text(broken, encoding="utf-8")

    result = runner.invoke(
        app, ["npc", "--rules-data", str(tmp_path), "--seed", "session-alpha"] + mode
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "navy.toml" in result.stderr
    assert "Coms" in result.stderr


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


def test_a_name_carrying_a_tab_or_a_newline_is_a_usage_error():
    # T170: the same reasoning T148's empty-name refusal uses — FR-047
    # requires a supplied name verbatim, and a tab or a newline is a name
    # that cannot be rendered verbatim without breaking FR-046's tab count
    # or FR-048a's blank-line batch separator.
    for name in ("Alex\tRivera", "Alex\n\nRivera"):
        result = runner.invoke(app, ["npc", "--name", name])
        assert result.exit_code == 2
        assert result.stdout == ""


def test_a_render_time_failure_is_reported_cleanly_not_as_a_traceback(monkeypatch):
    # T175: `as_text`/`as_json` are called outside the command's
    # `try/except CetoolsError`, so a render-time failure (e.g.
    # `CharacteristicRegistry.symbol` raising `RulesDataError` for a score
    # outside the declared range) writes an unhandled traceback rather
    # than the reason FR-054 requires, after `Seed:` and `Rules:` have
    # already gone to standard error.
    from cetools.errors import CetoolsError

    def _boom(*args, **kwargs):
        raise CetoolsError("boom")

    monkeypatch.setattr("cetools.cli.as_text", _boom)
    result = runner.invoke(app, ["npc", "--seed", "session-alpha"])
    assert result.exit_code == 1
    assert result.stdout == ""
    # A raw `CetoolsError` propagating uncaught reaches Click's own
    # top-level exception handling and never writes "boom" anywhere; only
    # the command's own `except CetoolsError` block does, which is what
    # distinguishes a clean, reported failure from a crash intercepted by
    # accident.
    assert "boom" in result.stderr
    assert not isinstance(result.exception, CetoolsError)


def test_a_generation_time_out_of_range_table_read_is_reported_cleanly(tmp_path):
    # T181: a die able to produce a total outside a chargen table's array
    # used to raise a bare `IndexError` mid-walk rather than the
    # `RulesDataError` FR-054 requires reported on standard error with
    # nothing on standard output.
    mishaps_text = _MISHAPS.replace('roll = "1d6"', 'roll = "2d6"', 1)
    assert mishaps_text != _MISHAPS
    params_text = _CHARGEN_PARAMETERS.replace("natural-failure = 2", "natural-failure = 12", 1)
    assert params_text != _CHARGEN_PARAMETERS
    (tmp_path / "mishaps.toml").write_text(mishaps_text, encoding="utf-8")
    (tmp_path / "chargen-parameters.toml").write_text(params_text, encoding="utf-8")
    result = runner.invoke(app, ["npc", "--rules-data", str(tmp_path), "--seed", "0"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.strip()
    assert not isinstance(result.exception, IndexError)


def test_count_zero_is_a_usage_error_naming_count(strip_ansi):
    result = runner.invoke(app, ["npc", "--seed", "session-alpha", "--count", "0"])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "--count" in strip_ansi(result.output)


def test_count_negative_is_a_usage_error_naming_count(strip_ansi):
    result = runner.invoke(app, ["npc", "--seed", "session-alpha", "--count", "-1"])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "--count" in strip_ansi(result.output)


def test_name_with_count_above_one_is_a_usage_error_naming_both(strip_ansi):
    result = runner.invoke(
        app, ["npc", "--seed", "session-alpha", "--name", "Alex Rivera", "--count", "12"]
    )
    assert result.exit_code == 2
    assert result.stdout == ""
    output = strip_ansi(result.output)
    assert "--name" in output
    assert "--count" in output


def test_json_standard_error_is_silent_on_success():
    result = runner.invoke(app, ["npc", "--seed", "session-alpha", "--json"])
    assert result.exit_code == 0
    assert result.stderr == ""


def test_json_carries_the_seed_version_and_provenance_in_document():
    result = runner.invoke(app, ["npc", "--seed", "session-alpha", "--json"])
    payload = json.loads(result.stdout)
    assert payload["kind"] == "npc"
    assert payload["seed"]
    assert payload["provenance"]["version"]


def test_full_with_json_is_accepted_and_changes_nothing():
    with_full = runner.invoke(app, ["npc", "--seed", "session-alpha", "--json", "--full"])
    without_full = runner.invoke(app, ["npc", "--seed", "session-alpha", "--json"])
    assert with_full.exit_code == 0
    assert with_full.stdout == without_full.stdout


def test_json_never_changes_an_exit_code():
    ok = runner.invoke(app, ["npc", "--seed", "session-alpha", "--json"])
    assert ok.exit_code == 0

    load_failure = runner.invoke(app, ["npc", "--rules-data", "/does/not/exist", "--json"])
    assert load_failure.exit_code == 2

    usage_error = runner.invoke(app, ["npc", "--name", "   ", "--json"])
    assert usage_error.exit_code == 2


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
