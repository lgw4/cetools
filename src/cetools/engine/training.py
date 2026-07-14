from __future__ import annotations

from dataclasses import dataclass

from cetools.engine.careers.base import Career
from cetools.engine.models import apply_stat_boost, parse_stat_boost
from cetools.engine.rolls import RollName, Rolls

ADVANCED_EDUCATION_MINIMUM = 8


@dataclass(frozen=True)
class Training:
    """What one Skills and Training roll produced."""

    entry: str
    characteristics: dict[str, int]
    skills: dict[str, int]


def _tables(career: Career, characteristics: dict[str, int]) -> list[tuple[str, ...]]:
    tables = [
        career.personal_development,
        career.service_skills,
        career.specialist_skills,
    ]
    if characteristics.get("Education", 0) >= ADVANCED_EDUCATION_MINIMUM:
        tables.append(career.advanced_education)
    return tables


def apply_entry(
    entry: str, characteristics: dict[str, int], skills: dict[str, int]
) -> tuple[dict[str, int], dict[str, int]]:
    """Apply one table entry, which is either a stat boost or a skill.

    A skill the character does not already have is taken at level 1; one they do
    have goes up a level. Level 0 comes only from basic training and background
    skills, and a roll takes such a skill to 1 either way.
    """
    boost = parse_stat_boost(entry)
    if boost is not None:
        return apply_stat_boost(characteristics, boost), dict(skills)

    trained = dict(skills)
    trained[entry] = trained.get(entry, 0) + 1
    return dict(characteristics), trained


def roll_skill(
    career: Career,
    characteristics: dict[str, int],
    skills: dict[str, int],
    rolls: Rolls,
) -> Training:
    """One Skills and Training roll: choose a table, then roll 1D6 on it.

    The SRD says to *choose* a table, so the choice is uniform over the tables on
    offer — Advanced Education among them only at Education 8+. Rolling on the
    chosen table is a real 1D6.
    """
    table = rolls.choose(_tables(career, characteristics), RollName.SKILL_TABLE)
    entry = table[rolls.d6(RollName.SKILL_ENTRY) - 1]
    characteristics, skills = apply_entry(entry, characteristics, skills)
    return Training(entry=entry, characteristics=characteristics, skills=skills)
