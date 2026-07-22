from __future__ import annotations

from cetools.engine.models import characteristic_modifier
from cetools.engine.rolls import RollName, Rolls

EDUCATION_SKILLS: tuple[str, ...] = (
    "Admin",
    "Advocate",
    "Animals",
    "Carousing",
    "Comms",
    "Computer",
    "Electronics",
    "Engineering",
    "Life Sciences",
    "Linguistics",
    "Mechanics",
    "Medicine",
    "Physical Sciences",
    "Social Sciences",
    "Space Sciences",
)

HOMEWORLD_SKILLS: tuple[str, ...] = (
    "Animals",
    "Broker",
    "Carousing",
    "Computer",
    "Gun Combat",
    "Melee Combat",
    "Streetwise",
    "Survival",
    "Watercraft",
    "Zero-G",
)

_MAX_HOMEWORLD_SKILLS = 2


def draw_distinct(
    pool: tuple[str, ...],
    count: int,
    rolls: Rolls,
    exclude: tuple[str, ...] = (),
) -> list[str]:
    """`count` distinct skills drawn from `pool`, or as many as the pool holds."""
    remaining = [skill for skill in pool if skill not in exclude]
    chosen: list[str] = []
    for _ in range(min(count, len(remaining))):
        pick = rolls.choose(remaining, RollName.BACKGROUND_SKILL)
        remaining.remove(pick)
        chosen.append(pick)
    return chosen


def background_skills(characteristics: dict[str, int], rolls: Rolls) -> dict[str, int]:
    """The skills a character brings to their first career, all at level 0.

    A character gets 3 + their Education DM of them (none, if that is negative or
    zero): up to two from their homeworld, the rest from their education. The two
    pools overlap, so an education draw never repeats a homeworld skill.
    """
    count = max(0, 3 + characteristic_modifier(characteristics.get("Education", 0)))
    homeworld_count = min(_MAX_HOMEWORLD_SKILLS, count)

    homeworld = draw_distinct(HOMEWORLD_SKILLS, homeworld_count, rolls)
    education = draw_distinct(
        EDUCATION_SKILLS, count - homeworld_count, rolls, exclude=tuple(homeworld)
    )
    return {skill: 0 for skill in homeworld + education}
