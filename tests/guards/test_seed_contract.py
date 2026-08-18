import os
import random
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from cetools import Roller, check, d66, load_rules, throw, throw_dice
from cetools.cli import app

runner = CliRunner()

# SC-005 binds *any* operation, so the guard walks both commands rather than
# `roll` alone: `check` loads rules data and takes a different code path, and a
# regression that reached for module-level `random` there would otherwise ship.
CLI_INVOCATIONS = [
    ["roll", "2d6", "--seed", "session-alpha"],
    ["roll", "d66", "--seed", "session-alpha"],
    ["roll", "2d6"],
    ["check", "--difficulty", "Difficult", "--characteristic", "9", "--skill", "2"],
    ["check", "--seed", "1", "--dm", "cover=-2"],
]


@pytest.mark.parametrize("mode", [[], ["--json"]], ids=["text", "json"])
@pytest.mark.parametrize("command", CLI_INVOCATIONS, ids=lambda c: " ".join(c))
def test_guard_a_cli_invocation_does_not_touch_module_random_state(command, mode):
    before = random.getstate()
    result = runner.invoke(app, command + mode)
    assert result.exit_code == 0
    assert random.getstate() == before


def test_guard_a_library_calls_do_not_touch_module_random_state():
    # 001-dice-task-engine FR-001 binds the library, and that feature's SC-011
    # asks for capabilities to be verified without the CLI in the way, so every
    # generator is exercised directly here.
    before = random.getstate()
    throw(Roller("session-alpha"), "2d6+1")
    throw_dice(Roller(1), 3, 6, -2)
    d66(Roller("session-alpha"))
    check(Roller(1), difficulty="Difficult", characteristic=9, skill=2)
    check(Roller(None), rules=load_rules())
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
