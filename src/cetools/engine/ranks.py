from __future__ import annotations

from dataclasses import dataclass

from cetools.engine.careers.base import Career, RankEntry
from cetools.engine.models import characteristic_check
from cetools.engine.rolls import RollName, Rolls

MAX_RANK = 6


@dataclass(frozen=True)
class Progress:
    """What one term did to a character's rank."""

    rank: int
    commissioned: bool
    promoted: bool
    skills: dict[str, int]


def grant_rank_bonus(rank_entry: RankEntry, skills: dict[str, int]) -> dict[str, int]:
    """The skills after a rank's bonus skills are granted, each at level 1 or up."""
    granted = dict(skills)
    for skill_name in rank_entry.bonus_skills:
        granted[skill_name] = granted.get(skill_name, 0) + 1
    return granted


def _advance(
    career: Career,
    rank: int,
    characteristics: dict[str, int],
    skills: dict[str, int],
    rolls: Rolls,
) -> tuple[int, bool, dict[str, int]]:
    """One advancement attempt. The rule, written once.

    A character at the top rank stays there: the check is still made, but there is
    nowhere to go.
    """
    if career.advancement_stat is None or career.advancement_target is None:
        return rank, False, skills

    if not characteristic_check(
        rolls,
        characteristics,
        career.advancement_stat,
        career.advancement_target,
        RollName.ADVANCEMENT,
    ):
        return rank, False, skills

    if rank >= MAX_RANK:
        return rank, False, skills

    rank += 1
    return rank, True, grant_rank_bonus(career.ranks[rank], skills)


def progress(
    career: Career,
    rank: int,
    characteristics: dict[str, int],
    skills: dict[str, int],
    rolls: Rolls,
) -> Progress:
    """A term's commission and advancement.

    A Rank 0 character in a career that commissions attempts it, and on success
    may advance again in the same term. A character who already holds a rank
    attempts advancement instead. A career without a commission never advances at
    all: its characters stay at Rank 0, which is why they get two skill rolls a
    term rather than one.
    """
    commissions = career.commission_stat is not None and career.commission_target is not None

    if rank == 0 and commissions:
        if not characteristic_check(
            rolls,
            characteristics,
            career.commission_stat,
            career.commission_target,
            RollName.COMMISSION,
        ):
            return Progress(rank=rank, commissioned=False, promoted=False, skills=skills)

        rank = 1
        skills = grant_rank_bonus(career.ranks[rank], skills)
        rank, promoted, skills = _advance(career, rank, characteristics, skills, rolls)
        return Progress(rank=rank, commissioned=True, promoted=promoted, skills=skills)

    if rank >= 1:
        rank, promoted, skills = _advance(career, rank, characteristics, skills, rolls)
        return Progress(rank=rank, commissioned=False, promoted=promoted, skills=skills)

    return Progress(rank=rank, commissioned=False, promoted=False, skills=skills)
