from __future__ import annotations

from cetools.engine import mishaps
from cetools.engine.careers.base import Career
from cetools.engine.careers.registry import CAREER_REGISTRY, DRAFT_TABLE
from cetools.engine.dice import DiceRoller, RandomDiceRoller
from cetools.engine.models import (
    STAT_ABBREV,
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


def _check(roller: DiceRoller, characteristics: dict[str, int], stat: str, target: int) -> bool:
    return roller.roll(6, count=2) + _dm(characteristics, stat) >= target


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


def _apply_stat_boost(name: str, characteristics: dict[str, int]) -> bool:
    """Return True if `name` is a "+1 X" entry, whether or not X is a known stat."""
    if not name.startswith("+1 "):
        return False
    stat = STAT_ABBREV.get(name[3:])
    if stat:
        characteristics[stat] = min(33, characteristics.get(stat, 0) + 1)
    return True


def _apply_skill_entry(
    entry: str, characteristics: dict[str, int], skills: dict[str, int]
) -> None:
    if not _apply_stat_boost(entry, characteristics):
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
            mat_max = len(career.material_benefits) - 1
            idx = max(0, min(mat_max, roller.roll(6) + material_dm - 1))
            name = career.material_benefits[idx]
            _apply_material_benefit(name, characteristics, skills)
            benefits.append(Benefit(kind="material", material_name=name))

    return benefits


def _apply_material_benefit(
    name: str, characteristics: dict[str, int], skills: dict[str, int]
) -> None:
    _apply_stat_boost(name, characteristics)


def _pension(terms_served: int) -> int | None:
    if terms_served < 5:
        return None
    if terms_served <= 8:
        return _PENSION.get(terms_served, 16000 + (terms_served - 8) * 2000)
    return 16000 + (terms_served - 8) * 2000


def generate_character(
    career: Career,
    roller: DiceRoller | None = None,
    preset_characteristics: dict[str, int] | None = None,
    bypass_qualification: bool = False,
    hard_max_terms: bool = False,
    drafted: bool = False,
) -> Character | GenerationFailure:
    if roller is None:
        roller = RandomDiceRoller()

    if preset_characteristics is not None:
        missing = [s for s in STAT_NAMES if s not in preset_characteristics]
        if missing:
            raise ValueError(f"preset_characteristics missing required stats: {missing}")
        characteristics: dict[str, int] = dict(preset_characteristics)
    else:
        characteristics = {stat: roller.roll(6, count=2) for stat in STAT_NAMES}

    skills: dict[str, int] = {}
    for i in range(3):
        bg_skill = _BACKGROUND_SKILLS[i % len(_BACKGROUND_SKILLS)]
        skills[bg_skill] = skills.get(bg_skill, -1) + 1

    if not bypass_qualification:
        if not _check(
            roller, characteristics, career.qualification_stat, career.qualification_target
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

        if not _check(roller, characteristics, career.survival_stat, career.survival_target):
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
            mishap, mishap_debt = mishaps.resolve_survival_mishap(roller, characteristics)
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
            if _check(roller, characteristics, career.commission_stat, career.commission_target):
                rank = 1
                commissioned_this_term = True
                _grant_rank_bonus(career.ranks[rank], characteristics, skills)
                if career.advancement_stat is not None and career.advancement_target is not None:
                    if _check(
                        roller, characteristics, career.advancement_stat, career.advancement_target
                    ):
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
            if _check(roller, characteristics, career.advancement_stat, career.advancement_target):
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
        benefits = _muster_out(career, terms_served, rank, skills, characteristics, roller)
        pension = _pension(terms_served)
    name = generate_name(roller)

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
    )


def roll_until_qualified(career: Career, roller: DiceRoller | None = None) -> dict[str, int]:
    if roller is None:
        roller = RandomDiceRoller()
    while True:
        characteristics = {stat: roller.roll(6, count=2) for stat in STAT_NAMES}
        if characteristics[career.qualification_stat] >= career.qualification_target:
            return characteristics


def draft_character(roller: DiceRoller | None = None) -> Character | GenerationFailure:
    if roller is None:
        roller = RandomDiceRoller()
    roll = roller.roll(6)
    name = DRAFT_TABLE[roll - 1]
    career = CAREER_REGISTRY.get(name)
    if career is None:
        return GenerationFailure(reason=f"Draft assigned unimplemented career '{name}'")
    return generate_career_character(career, roller, drafted=True)


def generate_career_character(
    career: Career,
    roller: DiceRoller | None = None,
    drafted: bool = False,
) -> Character | GenerationFailure:
    if roller is None:
        roller = RandomDiceRoller()
    characteristics = roll_until_qualified(career, roller)
    return generate_character(
        career,
        roller=roller,
        preset_characteristics=characteristics,
        bypass_qualification=True,
        hard_max_terms=True,
        drafted=drafted,
    )
