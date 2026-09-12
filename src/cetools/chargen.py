"""The universal chargen tables: draft, aging, mishaps, background skills,
medical tiers, and the parameters the walk reads everything else from
(contracts/data-files.md, data-model.md).

Each `parse_*` function turns one file's already-parsed TOML dict into a
table, collecting every problem rather than raising on the first, following
the convention `registries.py` and `careers.py` established.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from cetools.errors import RulesDataError, type_name
from cetools.notation import EntryContext, NotationProblem, SkillGrant, parse_entry
from cetools.registries import SkillRegistry, SkillResolution
from cetools.schema import HEADER_KEYS, ParseContext
from cetools.tasks import _check_dice

_RANGE_SINGLE = re.compile(r"^(-?\d+)$")
_RANGE_BOUNDED = re.compile(r"^(-?\d+)-(-?\d+)$")
_RANGE_UNBOUNDED = re.compile(r"^(-?\d+)\+$")

_AMOUNT_INTEGER = re.compile(r"^[+-]?\d+$")
_AMOUNT_DICE = re.compile(r"^[+-]?\d*[dD]\d+(?:[+-]\d+)?$")


# --- draft-table (contracts/data-files.md) ----------------------------------


@dataclass(frozen=True, slots=True)
class DraftTable:
    """`roll` reads a row of `careers` positionally; row order is
    significant because the die is positional (FR-005).
    """

    roll: str
    careers: tuple[str, ...]


def parse_draft_table(data: Mapping[str, object], ctx: ParseContext) -> DraftTable | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"roll", "careers"})

    roll = ctx.require_roll(data, "roll")

    careers: tuple[str, ...] | None = None
    raw = ctx.require_list(
        data, "careers", expected="at least one entry", expected_missing="a non-empty array"
    )
    if raw is not None:
        parsed: list[str] = []
        ok = True
        for index, item in enumerate(raw):
            if not isinstance(item, str) or not item:
                found = type_name(item) if not isinstance(item, str) else "an empty string"
                ctx.at("careers", index).report(found=found, expected="a non-empty string")
                ok = False
                continue
            parsed.append(item)
        if ok:
            careers = tuple(parsed)

    if ctx.failed or roll is None or careers is None:
        return None
    return DraftTable(roll=roll, careers=careers)


# --- aging-table (contracts/data-files.md) -----------------------------------


@dataclass(frozen=True, slots=True)
class ClassEffect:
    """Reduce `count` distinct characteristics of `characteristic_class` by
    `amount`. Which characteristics are chosen is the generator's decision,
    made at random and recorded in the history.
    """

    characteristic_class: str
    count: int
    amount: int


@dataclass(frozen=True, slots=True)
class AgingRow:
    """`maximum` is `None` for the sole unbounded top row. The lowest row is
    a floor: a modified result below it reads that row.
    """

    minimum: int
    maximum: int | None
    effects: tuple[ClassEffect, ...]


@dataclass(frozen=True, slots=True)
class AgingTable:
    """`rows` sorted by `minimum`, exactly one unbounded above."""

    roll: str
    rows: tuple[AgingRow, ...]


def _parse_range(text: str) -> tuple[int, int | None] | None:
    """`N`, `N-M`, or `N+`, any of which may be negative."""
    if (match := _RANGE_UNBOUNDED.match(text)) is not None:
        return int(match.group(1)), None
    if (match := _RANGE_BOUNDED.match(text)) is not None:
        return int(match.group(1)), int(match.group(2))
    if (match := _RANGE_SINGLE.match(text)) is not None:
        value = int(match.group(1))
        return value, value
    return None


def _parse_class_effect(value: object, ctx: ParseContext) -> ClassEffect | None:
    if not isinstance(value, dict):
        ctx.report(found=type_name(value), expected="a table")
        return None

    ctx.unrecognized_keys(value, {"class", "count", "amount"})

    characteristic_class = ctx.require_string(value, "class")
    count = ctx.require_int(value, "count", minimum=1)

    amount = ctx.require_int(value, "amount")
    if amount == 0:
        ctx.at("amount").report(found="0", expected="a signed, non-zero integer")
        amount = None

    if characteristic_class is None or count is None or amount is None:
        return None
    return ClassEffect(characteristic_class=characteristic_class, count=count, amount=amount)


def _parse_effects(raw: list, ctx: ParseContext) -> tuple[ClassEffect, ...] | None:
    effects: list[ClassEffect] = []
    ok = True
    for index, item in enumerate(raw):
        effect = _parse_class_effect(item, ctx.at(index))
        if effect is None:
            ok = False
        else:
            effects.append(effect)
    if not ok:
        return None
    return tuple(effects)


def _parse_aging_row(value: object, ctx: ParseContext) -> AgingRow | None:
    if not isinstance(value, dict):
        ctx.report(found=type_name(value), expected="a table")
        return None

    ctx.unrecognized_keys(value, {"range", "effects"})

    bounds: tuple[int, int | None] | None = None
    range_text = ctx.require_string(value, "range")
    if range_text is not None:
        bounds = _parse_range(range_text)
        if bounds is None:
            ctx.at("range").report(found=repr(range_text), expected="N, N-M, or N+")

    # Accepts an empty array today and must continue to (inventory.md I-4):
    # an aging row with no effects still validates.
    raw_effects = ctx.require_list(value, "effects", expected="an array", allow_empty=True)
    effects = _parse_effects(raw_effects, ctx.at("effects")) if raw_effects is not None else None

    if bounds is None or effects is None:
        return None
    minimum, maximum = bounds
    return AgingRow(minimum=minimum, maximum=maximum, effects=effects)


def parse_aging_table(data: Mapping[str, object], ctx: ParseContext) -> AgingTable | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"roll", "modifier", "rows"})

    roll = ctx.require_roll(data, "roll")

    modifier = data.get("modifier")
    if modifier != "terms-served":
        ctx.at("modifier").report(
            found="missing" if "modifier" not in data else repr(modifier),
            expected="'terms-served'",
        )

    rows: list[AgingRow] | None = None
    raw_rows = ctx.require_list(
        data, "rows", expected="at least one row", expected_missing="an array"
    )
    if raw_rows is not None:
        parsed_rows: list[AgingRow] = []
        ok = True
        for index, item in enumerate(raw_rows):
            row = _parse_aging_row(item, ctx.at("rows", index))
            if row is None:
                ok = False
            else:
                parsed_rows.append(row)
        if ok:
            rows = parsed_rows

    if rows is not None:
        unbounded_count = sum(1 for row in rows if row.maximum is None)
        if unbounded_count != 1:
            ctx.at("rows").report(
                found=f"{unbounded_count} unbounded rows",
                expected="exactly one row unbounded above",
            )
            rows = None

    if ctx.failed or roll is None or rows is None:
        return None
    rows.sort(key=lambda row: row.minimum)
    return AgingTable(roll=roll, rows=tuple(rows))


# --- mishap-table (contracts/data-files.md) ----------------------------------

_MISHAP_EFFECT_KINDS = frozenset(
    {
        "characteristic-class",
        "debt",
        "years",
        "forfeit-career-benefits",
        "roll-injury",
    }
)
_MISHAP_EFFECT_AMOUNT_KINDS = frozenset({"characteristic-class", "debt", "years"})


@dataclass(frozen=True, slots=True)
class MishapEffect:
    """One consequence of a mishap or an injury row.

    `characteristic_class` and `count` are only meaningful for
    `"characteristic-class"`, `""` and `0` otherwise; `amount` is only
    meaningful for `"characteristic-class"`, `"debt"`, and `"years"`, `""`
    otherwise.
    """

    kind: str
    characteristic_class: str
    count: int
    amount: str


@dataclass(frozen=True, slots=True)
class MishapRow:
    """One row of the mishap table, indexed by the throw's total, like the
    draft table.
    """

    description: str
    effects: tuple[MishapEffect, ...]


@dataclass(frozen=True, slots=True)
class InjuryRow:
    """One row of the injury table, reached only from a `roll-injury`
    effect.
    """

    description: str
    effects: tuple[MishapEffect, ...]


@dataclass(frozen=True, slots=True)
class MishapTable:
    """`rows` from `mishaps`, indexed positionally by `roll`'s total.
    `injuries` lives here because nothing but a `roll-injury` effect reaches
    it, and splitting the two files would let a referee replace one and
    leave a dangling reference in the other.
    """

    roll: str
    rows: tuple[MishapRow, ...]
    injury_roll: str
    injuries: tuple[InjuryRow, ...]


def _valid_amount_text(text: str) -> bool:
    if _AMOUNT_INTEGER.match(text):
        return True
    if not _AMOUNT_DICE.match(text):
        return False
    # Routed through `_check_dice`, the same guard every other
    # dice-notation field in the package uses, so `d66` (a two-digit table
    # die `parse_notation` answers with `None`) and a count or side count
    # below 1 are rejected here rather than reaching `generator.py` as an
    # uncaught `TypeError` or an undiagnosed `DiceError` (T204). The sign
    # this field alone admits — "the roll is negated" — is stripped first;
    # it is `generator.py`'s own concern, not dice notation's.
    body = text[1:] if text[:1] in ("+", "-") else text
    try:
        _check_dice(body)
    except RulesDataError:
        return False
    return True


def _parse_mishap_effect(
    value: object, ctx: ParseContext, allowed_kinds: frozenset[str] = _MISHAP_EFFECT_KINDS
) -> MishapEffect | None:
    if not isinstance(value, dict):
        ctx.report(found=type_name(value), expected="a table")
        return None

    kind = value.get("kind")
    if kind not in allowed_kinds:
        ctx.at("kind").report(
            found="missing" if "kind" not in value else repr(kind),
            expected=f"one of: {', '.join(sorted(allowed_kinds))}",
        )
        ctx.unrecognized_keys(value, {"kind", "class", "count", "amount"})
        return None

    allowed = {"kind"}
    if kind == "characteristic-class":
        allowed |= {"class", "count", "amount"}
    elif kind in ("debt", "years"):
        allowed |= {"amount"}
    ctx.unrecognized_keys(value, allowed)

    characteristic_class = ""
    count = 0
    if kind == "characteristic-class":
        parsed_class = ctx.require_string(value, "class")
        parsed_count = ctx.require_int(value, "count", minimum=1)
        characteristic_class = parsed_class or ""
        count = parsed_count if parsed_count is not None else 0

    amount = ""
    if kind in _MISHAP_EFFECT_AMOUNT_KINDS:
        raw_amount = value.get("amount")
        if not isinstance(raw_amount, str) or not raw_amount:
            found = "missing" if "amount" not in value else type_name(raw_amount)
            ctx.at("amount").report(
                found=found, expected="dice notation or a signed integer, as text"
            )
        elif not _valid_amount_text(raw_amount):
            ctx.at("amount").report(
                found=repr(raw_amount), expected="dice notation or a signed integer, as text"
            )
        else:
            amount = raw_amount

    if ctx.failed:
        return None
    return MishapEffect(
        kind=kind, characteristic_class=characteristic_class, count=count, amount=amount
    )


def _parse_mishap_effects(
    raw: list, ctx: ParseContext, allowed_kinds: frozenset[str] = _MISHAP_EFFECT_KINDS
) -> tuple[MishapEffect, ...] | None:
    effects: list[MishapEffect] = []
    ok = True
    for index, item in enumerate(raw):
        effect = _parse_mishap_effect(item, ctx.at(index), allowed_kinds)
        if effect is None:
            ok = False
        else:
            effects.append(effect)
    if not ok:
        return None
    return tuple(effects)


def _parse_mishap_row(
    value: object, ctx: ParseContext, allowed_kinds: frozenset[str] = _MISHAP_EFFECT_KINDS
) -> tuple[str, tuple[MishapEffect, ...]] | None:
    if not isinstance(value, dict):
        ctx.report(found=type_name(value), expected="a table")
        return None

    ctx.unrecognized_keys(value, {"description", "effects"})

    description = ctx.require_string(value, "description")

    # Accepts an empty array today and must continue to (inventory.md I-4).
    raw_effects = ctx.require_list(value, "effects", expected="an array", allow_empty=True)
    effects = (
        _parse_mishap_effects(raw_effects, ctx.at("effects"), allowed_kinds)
        if raw_effects is not None
        else None
    )

    if description is None or effects is None:
        return None
    return (description, effects)


def _parse_row_array(
    raw: list, ctx: ParseContext, allowed_kinds: frozenset[str] = _MISHAP_EFFECT_KINDS
) -> list[tuple[str, tuple[MishapEffect, ...]]] | None:
    rows: list[tuple[str, tuple[MishapEffect, ...]]] = []
    ok = True
    for index, item in enumerate(raw):
        row = _parse_mishap_row(item, ctx.at(index), allowed_kinds)
        if row is None:
            ok = False
        else:
            rows.append(row)
    if not ok:
        return None
    return rows


def parse_mishap_table(data: Mapping[str, object], ctx: ParseContext) -> MishapTable | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"roll", "injury-roll", "mishaps", "injuries"})

    roll = ctx.require_roll(data, "roll")
    injury_roll = ctx.require_roll(data, "injury-roll")

    mishaps: list[tuple[str, tuple[MishapEffect, ...]]] | None = None
    raw_mishaps = ctx.require_list(
        data, "mishaps", expected="at least one row", expected_missing="an array"
    )
    if raw_mishaps is not None:
        mishaps = _parse_row_array(raw_mishaps, ctx.at("mishaps"))

    injuries: list[tuple[str, tuple[MishapEffect, ...]]] | None = None
    raw_injuries = ctx.require_list(
        data, "injuries", expected="at least one row", expected_missing="an array"
    )
    if raw_injuries is not None:
        # Unlike a mishap row, an injury row is read by nothing but
        # `_apply_class_effect`'s `characteristic-class` handling — a
        # `debt`, `years`, `forfeit-career-benefits`, or `roll-injury`
        # effect there would validate clean and then do nothing (T185).
        injuries = _parse_row_array(
            raw_injuries, ctx.at("injuries"), frozenset({"characteristic-class"})
        )

    if ctx.failed or roll is None or injury_roll is None or mishaps is None or injuries is None:
        return None
    return MishapTable(
        roll=roll,
        rows=tuple(MishapRow(description=d, effects=e) for d, e in mishaps),
        injury_roll=injury_roll,
        injuries=tuple(InjuryRow(description=d, effects=e) for d, e in injuries),
    )


# --- background-skills (contracts/data-files.md) -----------------------------


@dataclass(frozen=True, slots=True)
class BackgroundSkills:
    """The homeworld draw is uniform over the concatenation of `law_level`
    and `trade_code`; duplicates within and across those two lists are
    preserved and meaningful (research R5): a skill named by three trade
    codes is three times as likely as one named by a single code.
    """

    law_level: tuple[SkillGrant, ...]
    trade_code: tuple[SkillGrant, ...]
    education: tuple[SkillGrant, ...]


def _parse_skill_grant(
    text: object, ctx: ParseContext, skills: SkillRegistry
) -> SkillGrant | None:
    if not isinstance(text, str):
        ctx.report(found=type_name(text), expected="a notation string")
        return None

    parsed = parse_entry(text, EntryContext.SKILL_TABLE)
    if isinstance(parsed, NotationProblem):
        ctx.report(found=parsed.found, expected=parsed.expected)
        return None
    if not isinstance(parsed, SkillGrant):
        ctx.report(
            found=text, expected="a skill granted at an explicit level, e.g. 'Gun Combat 0'"
        )
        return None

    resolution = skills.resolve(parsed.skill)
    if resolution is SkillResolution.VALID:
        return parsed
    reference = parsed.skill
    if resolution is SkillResolution.UNRECOGNIZED_SKILL:
        found = (
            f"{reference.name} ({reference.specialty})"
            if reference.specialty is not None
            else reference.name
        )
        expected = "a name in the skills registry"
    elif resolution is SkillResolution.SPECIALTY_NOT_ALLOWED:
        found = f"{reference.name} ({reference.specialty})"
        expected = f"a bare {reference.name}: the skills registry gives it no specialties"
    else:
        found = f"{reference.name} ({reference.specialty})"
        expected = f"a specialty the skills registry gives {reference.name}"
    ctx.report(found=found, expected=expected)
    return None


def _parse_skill_grant_list(
    raw: list, ctx: ParseContext, skills: SkillRegistry
) -> tuple[SkillGrant, ...] | None:
    grants: list[SkillGrant] = []
    ok = True
    for index, item in enumerate(raw):
        grant = _parse_skill_grant(item, ctx.at(index), skills)
        if grant is None:
            ok = False
        else:
            grants.append(grant)
    if not ok:
        return None
    return tuple(grants)


def parse_background_skills(
    data: Mapping[str, object], ctx: ParseContext, skills: SkillRegistry
) -> BackgroundSkills | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"law-level", "trade-code", "education"})

    lists: dict[str, tuple[SkillGrant, ...] | None] = {}
    for key in ("law-level", "trade-code", "education"):
        raw = ctx.require_list(
            data, key, expected="at least one entry", expected_missing="an array"
        )
        lists[key] = _parse_skill_grant_list(raw, ctx.at(key), skills) if raw is not None else None

    if ctx.failed or any(value is None for value in lists.values()):
        return None
    return BackgroundSkills(
        law_level=lists["law-level"],
        trade_code=lists["trade-code"],
        education=lists["education"],
    )


# --- medical-tiers (contracts/data-files.md) ---------------------------------


@dataclass(frozen=True, slots=True)
class MedicalThreshold:
    """The modified total must equal or exceed `target` for `paid_percent`
    to apply. A total below every threshold in a tier pays nothing.
    """

    target: int
    paid_percent: int


@dataclass(frozen=True, slots=True)
class MedicalTiers:
    """`rank_dm` is declared rather than assumed: whether the character's
    rank is added to the total. `tiers` is keyed by name, each tier's
    thresholds sorted highest-target-first so the first match wins.
    """

    roll: str
    rank_dm: bool
    tiers: Mapping[str, tuple[MedicalThreshold, ...]]


def _parse_medical_threshold(value: object, ctx: ParseContext) -> MedicalThreshold | None:
    if not isinstance(value, dict):
        ctx.report(found=type_name(value), expected="a table")
        return None

    ctx.unrecognized_keys(value, {"target", "paid-percent"})

    target = ctx.require_int(value, "target", minimum=0)
    paid_percent = ctx.require_int(value, "paid-percent", minimum=0)
    if paid_percent is not None and paid_percent > 100:
        ctx.at("paid-percent").report(
            found=str(paid_percent), expected="an integer between 0 and 100"
        )
        paid_percent = None

    if target is None or paid_percent is None:
        return None
    return MedicalThreshold(target=target, paid_percent=paid_percent)


def _parse_tier(
    value: object, ctx: ParseContext
) -> tuple[str, tuple[MedicalThreshold, ...]] | None:
    if not isinstance(value, dict):
        ctx.report(found=type_name(value), expected="a table")
        return None

    ctx.unrecognized_keys(value, {"name", "thresholds"})

    name = ctx.require_string(value, "name")

    thresholds: list[MedicalThreshold] | None = None
    raw = ctx.require_list(
        value, "thresholds", expected="at least one entry", expected_missing="an array"
    )
    if raw is not None:
        parsed: list[MedicalThreshold] = []
        ok = True
        targets_seen: set[int] = set()
        for index, item in enumerate(raw):
            threshold = _parse_medical_threshold(item, ctx.at("thresholds", index))
            if threshold is None:
                ok = False
                continue
            if threshold.target in targets_seen:
                ctx.at("thresholds", index, "target").report(
                    found=str(threshold.target), expected="a target distinct within its tier"
                )
                ok = False
                continue
            targets_seen.add(threshold.target)
            parsed.append(threshold)
        if ok:
            thresholds = parsed

    if name is None or thresholds is None:
        return None
    thresholds.sort(key=lambda threshold: threshold.target, reverse=True)
    return (name, tuple(thresholds))


def parse_medical_tiers(data: Mapping[str, object], ctx: ParseContext) -> MedicalTiers | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"roll", "rank-dm", "tiers"})

    roll = ctx.require_roll(data, "roll")
    rank_dm = ctx.require_bool(data, "rank-dm")

    tiers: dict[str, tuple[MedicalThreshold, ...]] | None = None
    raw = ctx.require_list(
        data, "tiers", expected="at least one entry", expected_missing="an array"
    )
    if raw is not None:
        parsed: dict[str, tuple[MedicalThreshold, ...]] = {}
        ok = True
        for index, item in enumerate(raw):
            result = _parse_tier(item, ctx.at("tiers", index))
            if result is None:
                ok = False
                continue
            name, thresholds = result
            if name in parsed:
                ctx.at("tiers", index, "name").report(
                    found=f"both declare the name {name!r}",
                    expected="a name distinct across tiers",
                )
                ok = False
                continue
            parsed[name] = thresholds
        if ok:
            tiers = parsed

    if ctx.failed or roll is None or rank_dm is None or tiers is None:
        return None
    return MedicalTiers(roll=roll, rank_dm=rank_dm, tiers=MappingProxyType(tiers))


# --- chargen-parameters (contracts/data-files.md) ----------------------------

# Every scalar the walk depends on (FR-038), grouped exactly as the file
# groups them. `(kind, minimum)`: `kind` is "roll", "int", "bool", or
# "string"; `minimum` bounds an integer field, `None` where the field is a
# signed modifier with no natural floor. Declarative, so ChargenParameters
# exposes every one of these as a named attribute — a misspelling in this
# table is an `AttributeError` at import, not a `KeyError` mid-walk — without
# forty near-identical `_require_*` call sites to keep in sync with it.
_CHARGEN_GROUPS: dict[str, dict[str, tuple[str, int | None]]] = {
    "characteristics": {"roll": ("roll", None)},
    "background-skills": {
        "base": ("int", 0),
        "characteristic": ("string", None),
        "homeworld-first": ("int", 0),
    },
    "terms": {
        "starting-age": ("int", 0),
        "term-years": ("int", 1),
        "mishap-term-years": ("int", 1),
        "cap": ("int", 1),
        "aging-begins-at-age": ("int", 0),
    },
    "qualification": {
        "penalty-per-previous-career": ("int", None),
        "draft-entries-allowed": ("int", 0),
    },
    "basic-training": {
        "first-career-all": ("bool", None),
        "subsequent-career-count": ("int", 0),
    },
    "survival": {"natural-failure": ("int", 0)},
    "skill-rolls": {
        "per-term": ("int", 0),
        "per-term-without-throws": ("int", 0),
        "on-commission": ("int", 0),
        "on-advancement": ("int", 0),
    },
    "commission": {"drafted-first-term-barred": ("bool", None)},
    "continuation": {"roll": ("roll", None), "target": ("int", 0)},
    "mustering-out": {
        "roll": ("roll", None),
        "cash-choice-roll": ("roll", None),
        "cash-choice-target": ("int", 0),
        "maximum-cash-rolls": ("int", 0),
        "retired-cash-dm": ("int", None),
        "per-term": ("int", 0),
    },
    "pension": {
        "minimum-terms": ("int", 1),
        "base": ("int", 0),
        "per-additional-term": ("int", 0),
    },
    "medical": {
        "crisis-roll": ("roll", None),
        "crisis-multiplier": ("int", 0),
        "crisis-restores-to": ("int", 0),
        "restore-cost-per-point": ("int", 0),
    },
}

# The two mustering-out fields that are arrays of rank-scoped rows rather
# than scalars, keyed by the row's own value field name.
_RANK_BONUS_ARRAYS = {"rank-benefits": "extra", "material-rank-dm": "dm"}


def _chargen_attribute(group: str, key: str) -> str:
    return f"{group.replace('-', '_')}_{key.replace('-', '_')}"


@dataclass(frozen=True, slots=True)
class RankBonus:
    """One row of `mustering-out.rank-benefits` or `.material-rank-dm`: at
    `rank` or above, `amount` applies. The highest matching row wins;
    neither table is cumulative.
    """

    rank: int
    amount: int


@dataclass(frozen=True, slots=True)
class ChargenParameters:
    """Every rules constant the walk depends on, exposed as named
    attributes rather than as a nested mapping (FR-038).
    """

    characteristics_roll: str
    background_skills_base: int
    background_skills_characteristic: str
    background_skills_homeworld_first: int
    terms_starting_age: int
    terms_term_years: int
    terms_mishap_term_years: int
    terms_cap: int
    terms_aging_begins_at_age: int
    qualification_penalty_per_previous_career: int
    qualification_draft_entries_allowed: int
    basic_training_first_career_all: bool
    basic_training_subsequent_career_count: int
    survival_natural_failure: int
    skill_rolls_per_term: int
    skill_rolls_per_term_without_throws: int
    skill_rolls_on_commission: int
    skill_rolls_on_advancement: int
    commission_drafted_first_term_barred: bool
    continuation_roll: str
    continuation_target: int
    mustering_out_roll: str
    mustering_out_cash_choice_roll: str
    mustering_out_cash_choice_target: int
    mustering_out_maximum_cash_rolls: int
    mustering_out_retired_cash_dm: int
    mustering_out_per_term: int
    mustering_out_rank_benefits: tuple[RankBonus, ...]
    mustering_out_material_rank_dm: tuple[RankBonus, ...]
    pension_minimum_terms: int
    pension_base: int
    pension_per_additional_term: int
    medical_crisis_roll: str
    medical_crisis_multiplier: int
    medical_crisis_restores_to: int
    medical_restore_cost_per_point: int


def _parse_rank_bonus(value: object, ctx: ParseContext, value_key: str) -> RankBonus | None:
    table = ctx.require_dict(value, expected="a table")
    if table is None:
        return None

    ctx.unrecognized_keys(table, {"rank", value_key})
    rank = ctx.require_int(table, "rank", minimum=0)
    amount = ctx.require_int(table, value_key)

    if rank is None or amount is None:
        return None
    return RankBonus(rank=rank, amount=amount)


def _parse_rank_bonus_list(
    raw: list, ctx: ParseContext, value_key: str
) -> tuple[RankBonus, ...] | None:
    bonuses: list[RankBonus] = []
    ok = True
    for index, item in enumerate(raw):
        bonus = _parse_rank_bonus(item, ctx.at(index), value_key)
        if bonus is None:
            ok = False
        else:
            bonuses.append(bonus)
    if not ok:
        return None
    return tuple(bonuses)


def _parse_chargen_group(
    data: Mapping[str, object], group: str, ctx: ParseContext
) -> dict[str, object]:
    fields = _CHARGEN_GROUPS[group]
    allowed = set(fields)
    if group == "mustering-out":
        allowed |= set(_RANK_BONUS_ARRAYS)

    table = ctx.require_dict(data.get(group), expected="a table")
    if table is None:
        return {}

    ctx.unrecognized_keys(table, allowed)

    values: dict[str, object] = {}
    for key, (kind, minimum) in fields.items():
        attribute = _chargen_attribute(group, key)
        if kind == "roll":
            values[attribute] = ctx.require_roll(table, key)
        elif kind == "bool":
            values[attribute] = ctx.require_bool(table, key)
        elif kind == "string":
            values[attribute] = ctx.require_string(table, key)
        else:
            values[attribute] = ctx.require_int(table, key, minimum=minimum)

    if group == "mustering-out":
        for array_key, value_key in _RANK_BONUS_ARRAYS.items():
            attribute = _chargen_attribute(group, array_key)
            raw = ctx.require_list(
                table, array_key, expected="at least one entry", expected_missing="an array"
            )
            values[attribute] = (
                _parse_rank_bonus_list(raw, ctx.at(array_key), value_key)
                if raw is not None
                else None
            )

    return values


def parse_chargen_parameters(
    data: Mapping[str, object], ctx: ParseContext
) -> ChargenParameters | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | set(_CHARGEN_GROUPS))

    values: dict[str, object] = {}
    for group in _CHARGEN_GROUPS:
        values.update(_parse_chargen_group(data, group, ctx.at(group)))

    if ctx.failed or any(value is None for value in values.values()):
        return None
    return ChargenParameters(**values)
