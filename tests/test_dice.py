"""Tests for the dice module."""

from cetools.dice import roll
from cetools.exceptions import InvalidInputError


def test_roll_simple():
    r = roll("2d6+1", seed=42)
    assert r.expression == "2d6+1"
    assert isinstance(r.breakdown, list)
    assert r.total == sum(r.breakdown) + 1


def test_roll_multiple_terms():
    r = roll("1d4,1d6+2", seed=123)
    assert r.expression == "1d4,1d6+2"
    assert len(r.breakdown) == 2


def test_seed_deterministic():
    a = roll("3d6", seed=1)
    b = roll("3d6", seed=1)
    assert a.breakdown == b.breakdown
    assert a.total == b.total


def test_invalid_expression():
    try:
        roll("abc")
        assert False, "Expected InvalidInputError"
    except InvalidInputError:
        pass


def test_large_dice_count_rejected():
    # 1001d1 should be rejected by the MAX_DICE guard
    try:
        roll("1001d1")
        assert False, "Expected InvalidInputError for large dice count"
    except InvalidInputError:
        pass


# This file contains GitHub Copilot generated content.
