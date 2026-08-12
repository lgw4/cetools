import os
import random
import subprocess
import sys

from typer.testing import CliRunner

from cetools.cli import app

runner = CliRunner()


def test_guard_a_cli_invocation_does_not_touch_module_random_state():
    before = random.getstate()
    result = runner.invoke(app, ["roll", "2d6", "--seed", "session-alpha"])
    assert result.exit_code == 0
    assert random.getstate() == before


def _run_in_subprocess(hashseed: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONHASHSEED=hashseed)
    return subprocess.run(
        [sys.executable, "-m", "cetools", "roll", "2d6", "--seed", "session-alpha"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def test_guard_b_text_seed_is_byte_identical_across_hashseeds():
    first = _run_in_subprocess("1")
    second = _run_in_subprocess("2")
    assert first.stdout == second.stdout
