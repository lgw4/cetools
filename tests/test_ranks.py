import dataclasses

from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.ranks import MAX_RANK, grant_rank_bonus, progress
from cetools.engine.rolls import RollName
from conftest import scripted

_STATS = {stat: 10 for stat in ("Intelligence", "Education", "Social Standing")}


def _navy(rank: int, skills: dict[str, int] | None = None, **overrides):
    return progress(NAVY_CAREER, rank, _STATS, skills or {}, scripted(**overrides))


# --- Commission ---


def test_a_rank_0_character_who_commissions_becomes_rank_1() -> None:
    # The advancement check that follows a commission is scripted to fail, so this
    # isolates the commission itself.
    result = _navy(0, checks={RollName.ADVANCEMENT: False})
    assert result.rank == 1
    assert result.commissioned is True
    assert result.promoted is False


def test_a_failed_commission_leaves_the_character_at_rank_0() -> None:
    result = _navy(0, checks={RollName.COMMISSION: False})
    assert result.rank == 0
    assert result.commissioned is False
    assert result.promoted is False


def test_a_commission_can_be_followed_by_an_advancement_in_the_same_term() -> None:
    result = _navy(0)  # every check passes
    assert result.rank == 2
    assert result.commissioned is True
    assert result.promoted is True


# --- Advancement ---


def test_a_ranked_character_advances_without_attempting_a_commission() -> None:
    # A commission is only ever attempted at rank 0. Scripting it to fail proves
    # it is not attempted here: were it, the character would not advance.
    result = _navy(3, checks={RollName.COMMISSION: False})
    assert result.rank == 4
    assert result.commissioned is False
    assert result.promoted is True


def test_a_failed_advancement_leaves_the_rank_alone() -> None:
    result = _navy(3, checks={RollName.ADVANCEMENT: False})
    assert result.rank == 3
    assert result.promoted is False


def test_the_top_rank_is_a_ceiling() -> None:
    result = _navy(MAX_RANK)
    assert result.rank == MAX_RANK
    assert result.promoted is False


def test_a_career_without_a_commission_never_leaves_rank_0() -> None:
    # Scout has no commission, so it has no route off rank 0—which is why its
    # characters get two skill rolls a term instead of one.
    result = progress(SCOUT_CAREER, 0, _STATS, {}, scripted())
    assert result.rank == 0
    assert result.commissioned is False
    assert result.promoted is False


def test_a_career_without_an_advancement_check_never_promotes() -> None:
    no_advancement = dataclasses.replace(
        NAVY_CAREER, advancement_stat=None, advancement_target=None
    )
    result = progress(no_advancement, 1, _STATS, {}, scripted())
    assert result.rank == 1
    assert result.promoted is False


# --- Rank bonus skills ---


def test_a_promotion_grants_the_new_rank_s_bonus_skills() -> None:
    # Navy rank 3 (Lt Commander) carries Tactics.
    result = _navy(2, checks={RollName.ADVANCEMENT: True})
    assert result.rank == 3
    assert result.skills["Tactics"] == 1


def test_grant_rank_bonus_raises_a_held_skill_by_one() -> None:
    skills = grant_rank_bonus(RankEntry(0, "Starman", ("Zero-G",)), {"Zero-G": 2})
    assert skills["Zero-G"] == 3


def test_grant_rank_bonus_does_not_mutate_its_argument() -> None:
    skills = {"Zero-G": 2}
    grant_rank_bonus(RankEntry(0, "Starman", ("Zero-G",)), skills)
    assert skills == {"Zero-G": 2}


def test_progress_does_not_mutate_the_skills_it_is_given() -> None:
    skills: dict[str, int] = {}
    _navy(2, skills=skills)
    assert skills == {}
