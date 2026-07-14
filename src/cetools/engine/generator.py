from __future__ import annotations

from cetools.engine import mishaps
from cetools.engine.careers.base import Career
from cetools.engine.careers.registry import CAREER_REGISTRY, DRAFT_TABLE
from cetools.engine.dice import DiceRoller, as_rolls
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
from cetools.engine.psionics import roll_psionics
from cetools.engine.rolls import RollName, Rolls

_PHYSICAL_STATS = ("Strength", "Dexterity", "Endurance")

_EDUCATION_SKILLS = (
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

_HOMEWORLD_SKILLS = (
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

_PENSION = {5: 10000, 6: 12000, 7: 14000, 8: 16000}

_RANK_BONUS_ROLLS = {4: 1, 5: 2, 6: 3}

_MAX_TERMS = 7
_MAX_CASH_ROLLS = 3
_UNIQUE_MATERIAL_BENEFITS = frozenset({"Explorers' Society", "Research Vessel", "Courier Vessel"})
_SHIP_SHARES_BENEFIT = "1D6 Ship Shares"
_MAX_MATERIAL_REROLLS = 100


def _dm(characteristics: dict[str, int], stat: str) -> int:
    return characteristic_modifier(characteristics[stat])


def _draw_distinct(
    pool: tuple[str, ...],
    count: int,
    roller: "DiceRoller | Rolls",
    exclude: tuple[str, ...] = (),
) -> list[str]:
    rolls = as_rolls(roller)
    remaining = [skill for skill in pool if skill not in exclude]
    chosen: list[str] = []
    for _ in range(min(count, len(remaining))):
        pick = rolls.choose(remaining, RollName.BACKGROUND_SKILL)
        remaining.remove(pick)
        chosen.append(pick)
    return chosen


def _grant_background_skills(
    characteristics: dict[str, int], skills: dict[str, int], roller: "DiceRoller | Rolls"
) -> None:
    rolls = as_rolls(roller)
    count = max(0, 3 + characteristic_modifier(characteristics.get("Education", 0)))
    homeworld_count = min(2, count)
    education_count = count - homeworld_count
    homeworld = _draw_distinct(_HOMEWORLD_SKILLS, homeworld_count, rolls)
    education = _draw_distinct(_EDUCATION_SKILLS, education_count, rolls, exclude=tuple(homeworld))
    for name in homeworld + education:
        skills[name] = 0


def _check(
    rolls: Rolls,
    characteristics: dict[str, int],
    stat: str,
    target: int,
    name: RollName,
) -> bool:
    return rolls.check(_dm(characteristics, stat), target, name)


def _roll_skill(
    career: Career,
    characteristics: dict[str, int],
    skills: dict[str, int],
    rolls: Rolls,
) -> str:
    tables = [
        career.personal_development,
        career.service_skills,
        career.specialist_skills,
    ]
    if characteristics.get("Education", 0) >= 8:
        tables.append(career.advanced_education)
    # A 1D6 modulo the table count, not a uniform pick: with Advanced Education
    # in play (4 tables) this favours the first two. Preserved as-is — the seam
    # refactor does not change any distribution.
    table = tables[(rolls.d6(RollName.SKILL_TABLE) - 1) % len(tables)]
    entry = table[(rolls.d6(RollName.SKILL_ENTRY) - 1) % 6]
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


def _apply_aging(characteristics: dict[str, int], terms_served: int, rolls: Rolls) -> None:
    roll = rolls.two_d6(RollName.AGING) - terms_served
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
    roller: "DiceRoller | Rolls",
) -> list[Benefit]:
    rolls = as_rolls(roller)
    bonus_rolls = _RANK_BONUS_ROLLS.get(rank, 0)
    total_rolls = terms_served + bonus_rolls
    cash_rolls_used = 0
    benefits: list[Benefit] = []
    granted_material_names: set[str] = set()

    cash_dm = 1 if skills.get("Gambling", -1) >= 0 else 0
    material_dm = 1 if rank >= 5 else 0

    for _ in range(total_rolls):
        use_cash = cash_rolls_used < _MAX_CASH_ROLLS
        if use_cash:
            idx = max(0, min(6, rolls.d6(RollName.CASH_BENEFIT) + cash_dm - 1))
            amount = career.cash_benefits[idx]
            benefits.append(Benefit(kind="cash", cash_amount=amount))
            cash_rolls_used += 1
        else:
            name = _roll_material_benefit(career, material_dm, rolls, granted_material_names)
            if name == _SHIP_SHARES_BENEFIT:
                quantity = rolls.d6(RollName.SHIP_SHARES)
                benefits.append(
                    Benefit(
                        kind="material",
                        material_name="Ship Shares",
                        material_quantity=quantity,
                    )
                )
                granted_material_names.add(name)
            else:
                _apply_material_benefit(name, characteristics, skills)
                granted_material_names.add(name)
                benefits.append(Benefit(kind="material", material_name=name))

    return benefits


def _roll_material_benefit(
    career: Career,
    material_dm: int,
    roller: "DiceRoller | Rolls",
    granted_names: set[str],
) -> str:
    rolls = as_rolls(roller)
    mat_max = len(career.material_benefits) - 1
    for _ in range(_MAX_MATERIAL_REROLLS):
        idx = max(0, min(mat_max, rolls.d6(RollName.MATERIAL_BENEFIT) + material_dm - 1))
        name = career.material_benefits[idx]
        if name in _UNIQUE_MATERIAL_BENEFITS and name in granted_names:
            continue
        return name
    # A degenerate roller (e.g. a fixed-value test roller) that keeps landing
    # on an already-granted once-only benefit would otherwise loop forever.
    # Fall back deterministically to the first table entry that is not an
    # already-granted once-only benefit — every real career table has one.
    for name in career.material_benefits:
        if not (name in _UNIQUE_MATERIAL_BENEFITS and name in granted_names):
            return name
    raise RuntimeError(
        f"Career '{career.name}' has no material benefit outside the"
        f" already-granted once-only set"
        f" {sorted(_UNIQUE_MATERIAL_BENEFITS & granted_names)}"
    )


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
    roller: "DiceRoller | Rolls | None" = None,
    preset_characteristics: dict[str, int] | None = None,
    bypass_qualification: bool = False,
    hard_max_terms: bool = False,
    drafted: bool = False,
) -> Character | GenerationFailure:
    rolls = as_rolls(roller)

    if preset_characteristics is not None:
        missing = [s for s in STAT_NAMES if s not in preset_characteristics]
        if missing:
            raise ValueError(f"preset_characteristics missing required stats: {missing}")
        characteristics: dict[str, int] = dict(preset_characteristics)
    else:
        characteristics = {stat: rolls.two_d6(RollName.CHARACTERISTIC) for stat in STAT_NAMES}

    skills: dict[str, int] = {}
    _grant_background_skills(characteristics, skills, rolls)

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
            if _check(
                rolls,
                characteristics,
                career.advancement_stat,
                career.advancement_target,
                RollName.ADVANCEMENT,
            ):
                if rank < 6:
                    rank += 1
                    promoted_this_term = True
                    _grant_rank_bonus(career.ranks[rank], characteristics, skills)

        skill_rolls = 1
        if not commissioned_this_term and not promoted_this_term:
            skill_rolls = 2

        for _ in range(skill_rolls):
            skills_gained_this_term.append(_roll_skill(career, characteristics, skills, rolls))

        age += 4
        terms_served += 1

        if age >= 34:
            _apply_aging(characteristics, terms_served, rolls)

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
        benefits = _muster_out(career, terms_served, rank, skills, characteristics, rolls)
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


def roll_until_qualified(
    career: Career, roller: "DiceRoller | Rolls | None" = None
) -> dict[str, int]:
    rolls = as_rolls(roller)
    while True:
        characteristics = {stat: rolls.two_d6(RollName.CHARACTERISTIC) for stat in STAT_NAMES}
        if career.qualification_stat is None or career.qualification_target is None:
            return characteristics
        if characteristics[career.qualification_stat] >= career.qualification_target:
            return characteristics


def draft_character(roller: "DiceRoller | Rolls | None" = None) -> Character | GenerationFailure:
    rolls = as_rolls(roller)
    name = DRAFT_TABLE[rolls.d6(RollName.DRAFT) - 1]
    career = CAREER_REGISTRY.get(name)
    if career is None:
        return GenerationFailure(reason=f"Draft assigned unimplemented career '{name}'")
    return generate_career_character(career, rolls, drafted=True)


def generate_career_character(
    career: Career,
    roller: "DiceRoller | Rolls | None" = None,
    drafted: bool = False,
) -> Character | GenerationFailure:
    rolls = as_rolls(roller)
    characteristics = roll_until_qualified(career, rolls)
    return generate_character(
        career,
        roller=rolls,
        preset_characteristics=characteristics,
        bypass_qualification=True,
        hard_max_terms=True,
        drafted=drafted,
    )


def random_career_character(
    roller: "DiceRoller | Rolls | None" = None,
    drafted: bool = False,
) -> Character | GenerationFailure:
    rolls = as_rolls(roller)
    careers = sorted(CAREER_REGISTRY.values(), key=lambda c: c.name)
    career = rolls.choose(careers, RollName.CAREER)
    return generate_career_character(career, rolls, drafted=drafted)
