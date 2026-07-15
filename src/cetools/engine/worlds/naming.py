"""Hybrid stem-based world name generation."""

from __future__ import annotations

from cetools.engine.rolls import RandomRolls, RollName, Rolls

_STEMS: tuple[str, ...] = tuple(
    f"{consonant}{vowel}" for consonant in "bcdfghjklmnprstvz" for vowel in "aeiou"
)
"""A curated pool of consonant-vowel syllable fragments (research.md D4)."""

_STEM_COUNTS: tuple[int, ...] = (2, 3)


def generate_world_name(rolls: Rolls | None = None) -> str:
    """An invented, pronounceable world name: 2-3 stems, title-cased.

    Deterministic under a seeded `rolls`. Not deduplicated here—a subsector's
    per-hex uniqueness guard is `generate_subsector`'s job, not this function's.
    """
    rolls = rolls or RandomRolls()
    count = rolls.choose(_STEM_COUNTS, RollName.WORLD_NAME_STEM)
    stems = [rolls.choose(_STEMS, RollName.WORLD_NAME_STEM) for _ in range(count)]
    return "".join(stems).capitalize()
