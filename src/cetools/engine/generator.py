from __future__ import annotations

from cetools.engine import mishaps
from cetools.engine.aging import AGING_STARTS_AT_AGE, apply_aging
from cetools.engine.background import background_skills
from cetools.engine.benefits import muster_out
from cetools.engine.careers.base import Career
from cetools.engine.careers.registry import CAREER_REGISTRY, DRAFT_TABLE
from cetools.engine.models import (
    STAT_NAMES,
    Benefit,
    Character,
    GenerationFailure,
    MishapOutcome,
    Term,
    characteristic_modifier,
)
from cetools.engine.names import generate_name
from cetools.engine.pseudohex import encode_upp
from cetools.engine.psionics import roll_psionics
from cetools.engine.rolls import RandomRolls, RollName, Rolls
from cetools.engine.training import roll_skill

_PENSION = {5: 10000, 6: 12000, 7: 14000, 8: 16000}

_MAX_TERMS = 7
_MAX_RANK = 6


def _dm(characteristics: dict[str, int], stat: str) -> int:
    return characteristic_modifier(characteristics[stat])


def _check(
    rolls: Rolls,
    characteristics: dict[str, int],
    stat: str,
    target: int,
    name: RollName,
) -> bool:
    return rolls.check(_dm(characteristics, stat), target, name)


def _grant_rank_bonus(rank_entry, characteristics: dict[str, int], skills: dict[str, int]) -> None:
    for skill_name in rank_entry.bonus_skills:
        skills[skill_name] = skills.get(skill_name, 0) + 1


def _pension(terms_served: int) -> int | None:
    if terms_served < 5:
        return None
    if terms_served <= 8:
        return _PENSION.get(terms_served, 16000 + (terms_served - 8) * 2000)
    return 16000 + (terms_served - 8) * 2000


def generate_character(
    career: Career,
    rolls: Rolls | None = None,
    preset_characteristics: dict[str, int] | None = None,
    bypass_qualification: bool = False,
    hard_max_terms: bool = False,
    drafted: bool = False,
) -> Character | GenerationFailure:
    rolls = rolls or RandomRolls()

    if preset_characteristics is not None:
        missing = [s for s in STAT_NAMES if s not in preset_characteristics]
        if missing:
            raise ValueError(f"preset_characteristics missing required stats: {missing}")
        characteristics: dict[str, int] = dict(preset_characteristics)
    else:
        characteristics = {stat: rolls.two_d6(RollName.CHARACTERISTIC) for stat in STAT_NAMES}

    skills: dict[str, int] = background_skills(characteristics, rolls)

    if (
        not bypass_qualification
        and career.qualification_stat is not None
        and career.qualification_target is not None
    ):
        if not _check(
            rolls,
            characteristics,
            career.qualification_stat,
            career.qualification_target,
            RollName.QUALIFICATION,
        ):
            return GenerationFailure(reason=f"{career.name} enlistment failed")

    rank = 0
    _grant_rank_bonus(career.ranks[rank], characteristics, skills)

    age = 18
    terms_served = 0
    term_history: list[Term] = []
    mandatory_extra = False
    mishap: MishapOutcome | None = None
    debt = 0

    for _term_iter in range(_MAX_TERMS + 1):
        term_num = terms_served + 1
        commissioned_this_term = False
        promoted_this_term = False
        skills_gained_this_term: list[str] = []

        if terms_served == 0:
            for skill_name in career.service_skills:
                if skill_name not in skills:
                    skills[skill_name] = 0
                skills_gained_this_term.append(skill_name)

        if not _check(
            rolls,
            characteristics,
            career.survival_stat,
            career.survival_target,
            RollName.SURVIVAL,
        ):
            term_history.append(
                Term(
                    number=term_num,
                    survived=False,
                    commissioned=False,
                    promoted=False,
                    rank_at_end=rank,
                    skills_gained=skills_gained_this_term,
                )
            )
            mishap, mishap_debt = mishaps.resolve_survival_mishap(rolls, characteristics)
            debt += mishap_debt
            age += 2
            if mishap.imprisoned:
                age += 4
            break

        commission_attempted = False

        if (
            rank == 0
            and career.commission_stat is not None
            and career.commission_target is not None
        ):
            commission_attempted = True
            if _check(
                rolls,
                characteristics,
                career.commission_stat,
                career.commission_target,
                RollName.COMMISSION,
            ):
                rank = 1
                commissioned_this_term = True
                _grant_rank_bonus(career.ranks[rank], characteristics, skills)
                if career.advancement_stat is not None and career.advancement_target is not None:
                    if _check(
                        rolls,
                        characteristics,
                        career.advancement_stat,
                        career.advancement_target,
                        RollName.ADVANCEMENT,
                    ):
                        if rank < _MAX_RANK:
                            rank += 1
                            promoted_this_term = True
                            _grant_rank_bonus(career.ranks[rank], characteristics, skills)

        if (
            not commission_attempted
            and rank >= 1
            and career.advancement_stat is not None
            and career.advancement_target is not None
        ):
            if _check(
                rolls,
                characteristics,
                career.advancement_stat,
                career.advancement_target,
                RollName.ADVANCEMENT,
            ):
                if rank < _MAX_RANK:
                    rank += 1
                    promoted_this_term = True
                    _grant_rank_bonus(career.ranks[rank], characteristics, skills)

        skill_rolls = 1
        if not commissioned_this_term and not promoted_this_term:
            skill_rolls = 2

        for _ in range(skill_rolls):
            training = roll_skill(career, characteristics, skills, rolls)
            characteristics = training.characteristics
            skills = training.skills
            skills_gained_this_term.append(training.entry)

        age += 4
        terms_served += 1

        if age >= AGING_STARTS_AT_AGE:
            characteristics = apply_aging(characteristics, terms_served, rolls)

        term_history.append(
            Term(
                number=term_num,
                survived=True,
                commissioned=commissioned_this_term,
                promoted=promoted_this_term,
                rank_at_end=rank,
                skills_gained=skills_gained_this_term,
            )
        )

        if mandatory_extra:
            break

        reenlist_roll = rolls.two_d6(RollName.REENLISTMENT)
        if terms_served >= _MAX_TERMS:
            if reenlist_roll == 12 and not hard_max_terms:
                mandatory_extra = True
            else:
                break
        else:
            if reenlist_roll < career.reenlistment_target:
                break

    if mishap is not None and mishap.discharge_type == "dishonorable":
        benefits: list[Benefit] = []
        pension = None
    else:
        mustered = muster_out(career, terms_served, rank, skills, characteristics, rolls)
        benefits = mustered.benefits
        characteristics = mustered.characteristics
        pension = _pension(terms_served)
    name = generate_name(rolls)
    psi_strength, talents = roll_psionics(terms_served, rolls)

    return Character(
        characteristics=characteristics,
        upp=encode_upp(characteristics),
        age=age,
        career=career.name,
        rank=rank,
        rank_title=career.ranks[rank].title,
        terms_served=terms_served,
        name=name,
        skills=skills,
        benefits=benefits,
        pension=pension,
        terms=term_history,
        drafted=drafted,
        mishap=mishap,
        debt=debt,
        psi_strength=psi_strength,
        talents=talents,
    )


def roll_until_qualified(career: Career, rolls: Rolls | None = None) -> dict[str, int]:
    rolls = rolls or RandomRolls()
    while True:
        characteristics = {stat: rolls.two_d6(RollName.CHARACTERISTIC) for stat in STAT_NAMES}
        if career.qualification_stat is None or career.qualification_target is None:
            return characteristics
        if characteristics[career.qualification_stat] >= career.qualification_target:
            return characteristics


def draft_character(rolls: Rolls | None = None) -> Character | GenerationFailure:
    rolls = rolls or RandomRolls()
    name = DRAFT_TABLE[rolls.d6(RollName.DRAFT) - 1]
    career = CAREER_REGISTRY.get(name)
    if career is None:
        return GenerationFailure(reason=f"Draft assigned unimplemented career '{name}'")
    return generate_career_character(career, rolls, drafted=True)


def generate_career_character(
    career: Career,
    rolls: Rolls | None = None,
    drafted: bool = False,
) -> Character | GenerationFailure:
    rolls = rolls or RandomRolls()
    characteristics = roll_until_qualified(career, rolls)
    return generate_character(
        career,
        rolls=rolls,
        preset_characteristics=characteristics,
        bypass_qualification=True,
        hard_max_terms=True,
        drafted=drafted,
    )


def random_career_character(
    rolls: Rolls | None = None,
    drafted: bool = False,
) -> Character | GenerationFailure:
    rolls = rolls or RandomRolls()
    careers = sorted(CAREER_REGISTRY.values(), key=lambda c: c.name)
    career = rolls.choose(careers, RollName.CAREER)
    return generate_career_character(career, rolls, drafted=drafted)
