from __future__ import annotations

from dataclasses import dataclass

from cetools.engine import mishaps
from cetools.engine.aging import AGING_STARTS_AT_AGE, apply_aging
from cetools.engine.background import background_skills
from cetools.engine.benefits import muster_out
from cetools.engine.careers.base import Career
from cetools.engine.careers.registry import CAREERS, DRAFT_TABLE
from cetools.engine.models import (
    STAT_NAMES,
    Benefit,
    Character,
    GenerationFailure,
    MishapOutcome,
    Term,
    characteristic_check,
)
from cetools.engine.names import generate_name
from cetools.engine.pseudohex import encode_upp
from cetools.engine.psionics import roll_psionics
from cetools.engine.ranks import grant_rank_bonus, progress
from cetools.engine.rolls import RandomRolls, RollName, Rolls
from cetools.engine.rules import HOUSE, Rules
from cetools.engine.training import roll_skill, rolls_this_term

_PENSION = {5: 10000, 6: 12000, 7: 14000, 8: 16000}

_MAX_TERMS = 7

# Enough that real dice will never exhaust it; small enough that a rolls source
# which can never qualify fails fast instead of hanging. Mirrors the same guard in
# benefits.roll_material_benefit.
_MAX_QUALIFICATION_ATTEMPTS = 100


def _pension(terms_served: int) -> int | None:
    if terms_served < 5:
        return None
    if terms_served <= 8:
        return _PENSION.get(terms_served, 16000 + (terms_served - 8) * 2000)
    return 16000 + (terms_served - 8) * 2000


@dataclass(frozen=True)
class Draft:
    """Assignment: take whatever career the draft table hands out."""


@dataclass(frozen=True)
class RandomCareer:
    """Assignment: any career, drawn uniformly."""


DRAFT = Draft()
RANDOM = RandomCareer()

Assignment = Career | Draft | RandomCareer
"""How a character comes to be in a career: a Career means "this one"."""


def _roll_characteristics(rolls: Rolls) -> dict[str, int]:
    return {stat: rolls.two_d6(RollName.CHARACTERISTIC) for stat in STAT_NAMES}


def _roll_until_qualified(career: Career, rolls: Rolls) -> dict[str, int]:
    """Reroll characteristics until the career will have them.

    A raw comparison against the career's target, not a dice check: under HOUSE
    rules a character gets the career they asked for, so enlistment cannot fail.
    """
    for _ in range(_MAX_QUALIFICATION_ATTEMPTS):
        characteristics = _roll_characteristics(rolls)
        if career.qualification_stat is None or career.qualification_target is None:
            return characteristics
        if characteristics[career.qualification_stat] >= career.qualification_target:
            return characteristics

    # A rolls source that can never clear the target (e.g. a ScriptedRolls pinned
    # to a 2D6 below it) would otherwise spin here for ever. Real dice do not: the
    # highest target any career sets is 8, which 2D6 clears about 42% of the time,
    # so exhausting these attempts by chance is a ~1-in-10^23 event.
    raise RuntimeError(
        f"Career '{career.name}' still unqualified after"
        f" {_MAX_QUALIFICATION_ATTEMPTS} attempts:"
        f" this rolls source cannot produce {career.qualification_stat}"
        f" {career.qualification_target}+"
    )


def _assign(assignment: Assignment, rolls: Rolls) -> tuple[Career, bool]:
    """The career, and whether the character was drafted into it.

    The draft table holds careers, not names, so a draft can never land on a
    career that does not exist.
    """
    if isinstance(assignment, Draft):
        return DRAFT_TABLE[rolls.d6(RollName.DRAFT) - 1], True

    if isinstance(assignment, RandomCareer):
        return rolls.choose(CAREERS, RollName.CAREER), False

    return assignment, False


def generate(
    assignment: Assignment,
    rolls: Rolls | None = None,
    rules: Rules = HOUSE,
) -> Character | GenerationFailure:
    """A whole character: pick the career, serve the terms, muster out.

    `assignment` is a Career, or DRAFT, or RANDOM.

    Under HOUSE rules this cannot fail: characteristics are rerolled until the
    career accepts them, and the draft table holds careers rather than names, so
    there is nothing left to fail at. `GenerationFailure` is returned only under
    SRD rules, whose enlistment is a check the character can miss.
    """
    rolls = rolls or RandomRolls()

    career, drafted = _assign(assignment, rolls)

    if rules.reroll_until_qualified:
        characteristics = _roll_until_qualified(career, rolls)
    else:
        characteristics = _roll_characteristics(rolls)

    skills: dict[str, int] = background_skills(characteristics, rolls)

    if (
        not rules.reroll_until_qualified
        and career.qualification_stat is not None
        and career.qualification_target is not None
    ):
        if not characteristic_check(
            rolls,
            characteristics,
            career.qualification_stat,
            career.qualification_target,
            RollName.QUALIFICATION,
        ):
            return GenerationFailure(reason=f"{career.name} enlistment failed")

    rank = 0
    skills = grant_rank_bonus(career.ranks[rank], skills)

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

        if not characteristic_check(
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
            resolved = mishaps.resolve_survival_mishap(rolls, characteristics)
            mishap = resolved.outcome
            characteristics = resolved.characteristics
            debt += resolved.debt
            age += 2
            if mishap.imprisoned:
                age += 4
            break

        advanced = progress(career, rank, characteristics, skills, rolls)
        rank = advanced.rank
        skills = advanced.skills
        commissioned_this_term = advanced.commissioned
        promoted_this_term = advanced.promoted

        skill_rolls = rolls_this_term(
            career, commissioned=commissioned_this_term, promoted=promoted_this_term
        )

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
            if reenlist_roll == 12 and rules.natural_12_forces_extra_term:
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
        career=career,
        rank=rank,
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
