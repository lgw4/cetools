"""Dice rolling utilities for cetools.

This file contains GitHub Copilot generated content.
"""

from __future__ import annotations

import random
import re
from typing import List

from .exceptions import InvalidInputError
from .models import RollResult

_DICE_RE = re.compile(r"^\s*(?:(?P<count>\d*)d(?P<sides>\d+)(?P<mod>[+-]\d+)?)\s*$", re.I)


def _parse_term(term: str):
    """Parse a single dice term like '2d6+1' or 'd20' or '4d8-2'.

    Returns (count:int, sides:int, modifier:int)
    Raises InvalidInputError for bad formats.
    """
    m = _DICE_RE.match(term)
    if not m:
        raise InvalidInputError(f"Invalid dice expression: {term!r}")

    count = m.group("count")
    sides = m.group("sides")
    mod = m.group("mod")

    count = int(count) if count else 1
    sides = int(sides)
    modifier = int(mod) if mod else 0

    if count < 1:
        raise InvalidInputError("Dice count must be >= 1")
    if sides < 1:
        raise InvalidInputError("Dice sides must be >= 1")

    return count, sides, modifier


def roll(expression: str, seed: int | None = None) -> RollResult:
    """Roll dice for an expression and return a RollResult.

    Supports comma-separated expressions (e.g. '2d6+1,1d4'). Breakdown contains
    only individual die rolls; modifiers are applied to the total but not included
    in `breakdown`.

    The function is deterministic when `seed` is provided.
    """
    if not isinstance(expression, str) or not expression.strip():
        raise InvalidInputError("Expression must be a non-empty string")

    rng = random.Random(seed)

    parts = [p.strip() for p in expression.split(",") if p.strip()]
    if not parts:
        raise InvalidInputError("No dice expressions found")

    breakdown: List[int] = []
    total = 0

    MAX_DICE = 1000

    for part in parts:
        count, sides, modifier = _parse_term(part)

        if count > MAX_DICE:
            raise InvalidInputError(f"Dice count too large: {count}")

        for _ in range(count):
            roll_val = rng.randint(1, sides)
            breakdown.append(roll_val)
            total += roll_val

        total += modifier

    return RollResult(expression=expression, breakdown=breakdown, total=total)


# This file contains GitHub Copilot generated content.
