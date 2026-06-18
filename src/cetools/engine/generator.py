from __future__ import annotations

from cetools.engine.careers.base import Career
from cetools.engine.dice import DiceRoller, RandomDiceRoller
from cetools.engine.models import (
    Benefit,
    Character,
    GenerationFailure,
    Term,
    characteristic_modifier,
)
from cetools.engine.pseudohex import encode_upp

_STAT_NAMES = (
    "Strength",
    "Dexterity",
    "Endurance",
    "Intelligence",
    "Education",
    "Social Standing",
)

_PHYSICAL_STATS = ("Strength", "Dexterity", "Endurance")

_BACKGROUND_SKILLS = (
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

_PENSION = {5: 10000, 6: 12000, 7: 14000, 8: 16000}

_RANK_BONUS_ROLLS = {4: 1, 5: 2, 6: 3}

_MAX_TERMS = 7
_MAX_CASH_ROLLS = 3


def _dm(characteristics: dict[str, int], stat: str) -> int:
    return characteristic_modifier(characteristics[stat])


def _roll_skill(
    career: Career,
    characteristics: dict[str, int],
    skills: dict[str, int],
    roller: DiceRoller,
) -> str:
    tables = [
        career.personal_development,
        career.service_skills,
        career.specialist_skills,
    ]
    if characteristics.get("Education", 0) >= 8:
        tables.append(career.advanced_education)
    table = tables[(roller.roll(6) - 1) % len(tables)]
    entry = table[(roller.roll(6) - 1) % 6]
    _apply_skill_entry(entry, characteristics, skills)
    return entry


def _apply_skill_entry(
    entry: str, characteristics: dict[str, int], skills: dict[str, int]
) -> None:
    if entry.startswith("+1 "):
        stat_abbr = entry[3:]
        stat_map = {
            "Str": "Strength",
            "Dex": "Dexterity",
            "End": "Endurance",
            "Int": "Intelligence",
            "Edu": "Education",
            "Soc": "Social Standing",
        }
        full_name = stat_map.get(stat_abbr)
        if full_name:
            characteristics[full_name] = min(33, characteristics.get(full_name, 0) + 1)
    else:
        skills[entry] = skills.get(entry, -1) + 1


def _grant_rank_bonus(rank_entry, characteristics: dict[str, int], skills: dict[str, int]) -> None:
    for skill_name in rank_entry.bonus_skills:
        skills[skill_name] = skills.get(skill_name, 0) + 1


def _apply_aging(characteristics: dict[str, int], terms_served: int, roller: DiceRoller) -> None:
    roll = roller.roll(6, count=2) - terms_served
    if roll >= 1:
        return
    reductions: list[tuple[str, int]] = []
    if roll == 0:
        reductions = [("Strength", 1)]
    elif roll == -1:
        reductions = [("Strength", 1), ("Dexterity", 1)]
    elif roll == -2:
        reductions = [("Strength", 1), ("Dexterity", 1), ("Endurance", 1)]
    elif roll == -3:
        reductions = [("Strength", 2), ("Dexterity", 1), ("Endurance", 1)]
    elif roll == -4:
        reductions = [("Strength", 2), ("Dexterity", 2), ("Endurance", 1)]
    elif roll == -5:
        reductions = [("Strength", 2), ("Dexterity", 2), ("Endurance", 2)]
    else:  # -6 or worse
        reductions = [
            ("Strength", 2),
            ("Dexterity", 2),
            ("Endurance", 2),
            ("Intelligence", 1),
        ]
    for stat, amount in reductions:
        characteristics[stat] = max(0, characteristics[stat] - amount)


def _muster_out(
    career: Career,
    terms_served: int,
    rank: int,
    skills: dict[str, int],
    characteristics: dict[str, int],
    roller: DiceRoller,
) -> list[Benefit]:
    bonus_rolls = _RANK_BONUS_ROLLS.get(rank, 0)
    total_rolls = terms_served + bonus_rolls
    cash_rolls_used = 0
    benefits: list[Benefit] = []

    cash_dm = 1 if skills.get("Gambling", -1) >= 0 else 0
    material_dm = 1 if rank >= 5 else 0

    for _ in range(total_rolls):
        use_cash = cash_rolls_used < _MAX_CASH_ROLLS
        if use_cash:
            idx = max(0, min(6, roller.roll(6) + cash_dm - 1))
            amount = career.cash_benefits[idx]
            benefits.append(Benefit(kind="cash", cash_amount=amount))
            cash_rolls_used += 1
        else:
            idx = max(0, min(6, roller.roll(6) + material_dm - 1))
            name = career.material_benefits[idx]
            _apply_material_benefit(name, characteristics, skills)
            benefits.append(Benefit(kind="material", material_name=name))

    return benefits


def _apply_material_benefit(
    name: str, characteristics: dict[str, int], skills: dict[str, int]
) -> None:
    stat_map = {
        "+1 Str": "Strength",
        "+1 Dex": "Dexterity",
        "+1 End": "Endurance",
        "+1 Int": "Intelligence",
        "+1 Edu": "Education",
        "+1 Soc": "Social Standing",
    }
    if name in stat_map:
        stat = stat_map[name]
        characteristics[stat] = min(33, characteristics.get(stat, 0) + 1)


def _pension(terms_served: int) -> int | None:
    if terms_served < 5:
        return None
    if terms_served <= 8:
        return _PENSION.get(terms_served, 16000 + (terms_served - 8) * 2000)
    return 16000 + (terms_served - 8) * 2000


def generate_character(
    career: Career,
    roller: DiceRoller | None = None,
) -> Character | GenerationFailure:
    if roller is None:
        roller = RandomDiceRoller()

    characteristics: dict[str, int] = {stat: roller.roll(6, count=2) for stat in _STAT_NAMES}

    skills: dict[str, int] = {}
    for i in range(3):
        bg_skill = _BACKGROUND_SKILLS[i % len(_BACKGROUND_SKILLS)]
        skills[bg_skill] = skills.get(bg_skill, -1) + 1

    qual_dm = _dm(characteristics, career.qualification_stat)
    if roller.roll(6, count=2) + qual_dm < career.qualification_target:
        return GenerationFailure(reason=f"{career.name} enlistment failed")

    rank = 0
    _grant_rank_bonus(career.ranks[rank], characteristics, skills)

    age = 18
    terms_served = 0
    term_history: list[Term] = []
    mandatory_extra = False

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

        surv_dm = _dm(characteristics, career.survival_stat)
        if roller.roll(6, count=2) + surv_dm < career.survival_target:
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
            return GenerationFailure(
                reason=f"Character died during term {term_num} survival check"
            )

        commission_attempted = False

        if (
            rank == 0
            and career.commission_stat is not None
            and career.commission_target is not None
        ):
            commission_attempted = True
            comm_dm = _dm(characteristics, career.commission_stat)
            if roller.roll(6, count=2) + comm_dm >= career.commission_target:
                rank = 1
                commissioned_this_term = True
                _grant_rank_bonus(career.ranks[rank], characteristics, skills)
                if career.advancement_stat is not None and career.advancement_target is not None:
                    adv_dm = _dm(characteristics, career.advancement_stat)
                    if roller.roll(6, count=2) + adv_dm >= career.advancement_target:
                        if rank < 6:
                            rank += 1
                            promoted_this_term = True
                            _grant_rank_bonus(career.ranks[rank], characteristics, skills)

        if (
            not commission_attempted
            and rank >= 1
            and career.advancement_stat is not None
            and career.advancement_target is not None
        ):
            adv_dm = _dm(characteristics, career.advancement_stat)
            if roller.roll(6, count=2) + adv_dm >= career.advancement_target:
                if rank < 6:
                    rank += 1
                    promoted_this_term = True
                    _grant_rank_bonus(career.ranks[rank], characteristics, skills)

        skill_rolls = 1
        if not commissioned_this_term and not promoted_this_term:
            skill_rolls = 2

        for _ in range(skill_rolls):
            skills_gained_this_term.append(_roll_skill(career, characteristics, skills, roller))

        age += 4
        terms_served += 1

        if age >= 34:
            _apply_aging(characteristics, terms_served, roller)

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

        reenlist_roll = roller.roll(6, count=2)
        if terms_served >= _MAX_TERMS:
            if reenlist_roll == 12:
                mandatory_extra = True
            else:
                break
        else:
            if reenlist_roll < career.reenlistment_target:
                break

    benefits = _muster_out(career, terms_served, rank, skills, characteristics, roller)

    return Character(
        characteristics=characteristics,
        upp=encode_upp(characteristics),
        age=age,
        career=career.name,
        rank=rank,
        rank_title=career.ranks[rank].title,
        terms_served=terms_served,
        skills=skills,
        benefits=benefits,
        pension=_pension(terms_served),
        terms=term_history,
    )
