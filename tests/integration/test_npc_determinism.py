"""SC-001, Constitution Principle IV made concrete: the same seed and the
same package version always produce the same character, byte for byte, and
across process boundaries — so anything seeded per-process rather than by
the seed itself is caught rather than hidden by one process's stable hash.
"""

import dataclasses
import subprocess
import sys

from cetools.dice import Roller
from cetools.generator import generate_character
from cetools.render import as_text
from cetools.rules import load_rules

RULES = load_rules()
FIXED_SEEDS = ["session-alpha", "session-beta", 1, 42, "a seed with spaces"]


def test_generating_the_same_seed_repeatedly_never_differs():
    for seed in FIXED_SEEDS:
        first = generate_character(Roller(seed), RULES)
        second = generate_character(Roller(seed), RULES)
        assert dataclasses.asdict(first) == dataclasses.asdict(second)
        assert as_text(first).encode("utf-8") == as_text(second).encode("utf-8")
        assert as_text(first, full=False) == as_text(second, full=False)


def _run(seed) -> bytes:
    result = subprocess.run(
        [sys.executable, "-m", "cetools", "npc", "--seed", str(seed)],
        capture_output=True,
        check=True,
    )
    return result.stdout


def test_generating_the_same_seed_twice_across_process_boundaries_never_differs():
    for seed in FIXED_SEEDS:
        first = _run(seed)
        second = _run(seed)
        assert first == second
