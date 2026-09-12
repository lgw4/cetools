"""The career file schema: `CareerDefinition` and the types beneath it
(contracts/data-files.md).

`parse_career` validates one file's already-parsed TOML dict against the
registries the caller already built, resolving every notation-bearing field
against the registry its position or its form implies, and collects every
problem rather than raising on the first (research R7). The throw targets
and mustering-out cash amounts are typed by position, never routed through
the notation (FR-004a).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from cetools.errors import type_name
from cetools.notation import (
    BenefitItem,
    CharacteristicAdjustment,
    CharacteristicCheck,
    EntryContext,
    NotationProblem,
    QuantifiedBenefit,
    SkillGrant,
    SkillReference,
    parse_entry,
)
from cetools.registries import (
    BenefitRegistry,
    CharacteristicRegistry,
    SkillRegistry,
    SkillResolution,
)
from cetools.schema import HEADER_KEYS, ParseContext

type SkillTableEntry = SkillReference | SkillGrant | CharacteristicAdjustment

_REQUIRED_THROWS = ("qualification", "survival", "re-enlistment")
_OPTIONAL_THROWS = ("commission", "promotion")
_ALL_THROWS = frozenset(_REQUIRED_THROWS) | frozenset(_OPTIONAL_THROWS)
_REQUIRED_TABLES = ("personal", "service", "specialist", "advanced-education")
_ALL_TABLES = frozenset(_REQUIRED_TABLES)
_LADDER_ROLES = frozenset({"entry", "commissioned"})


@dataclass(frozen=True, slots=True)
class Throw:
    """`characteristic` is `None` when the throw takes no characteristic
    modifier, which is how re-enlistment is thrown. `target` is a plain
    value, never notation (FR-004a, FR-014). `dice` is the throw's own dice
    notation, so no die anywhere in the walk is held in engine code
    (FR-038, Constitution V).
    """

    characteristic: str | None
    target: int
    dice: str


@dataclass(frozen=True, slots=True)
class SkillTable:
    """`requires` is the gate (FR-015); `None` for an ungated table."""

    requires: CharacteristicCheck | None
    entries: tuple[SkillTableEntry, ...]


@dataclass(frozen=True, slots=True)
class Rank:
    """`bonus` admits the same forms as a skill table entry (FR-016).

    `title` defaults to `""` for a rank the source prints no title for
    (FR-007, FR-013, D2): absence is written by omitting the key, not by
    writing an empty value.
    """

    rank: int
    title: str = ""
    bonus: SkillTableEntry | None = None


@dataclass(frozen=True, slots=True)
class RankLadder:
    """`role` is `"entry"` or `"commissioned"` (FR-007b). Exactly one ladder
    in a career carries `entry`; at most one carries `commissioned`, and a
    career declaring `throws.commission` must declare one (checked as a
    cross-file rule in `rules.py`, alongside the other checks that need a
    fully parsed `CareerDefinition`).
    """

    name: str
    role: str
    ranks: tuple[Rank, ...]


@dataclass(frozen=True, slots=True)
class MusteringOut:
    cash: tuple[int, ...]
    benefits: tuple[BenefitItem | CharacteristicAdjustment | QuantifiedBenefit, ...]


@dataclass(frozen=True, slots=True)
class CareerDefinition:
    """`name` is a human label, not the composition identity (FR-019a)."""

    name: str
    medical_tier: str
    always_available: bool
    re_enterable: bool
    throws: Mapping[str, Throw]
    tables: Mapping[str, SkillTable]
    ladders: tuple[RankLadder, ...]
    mustering_out: MusteringOut


def _notation_field(
    value: object,
    context: EntryContext,
    *,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> object | None:
    if not isinstance(value, str):
        ctx.report(found=type_name(value), expected="a notation string")
        return None

    parsed = parse_entry(value, context)
    if isinstance(parsed, NotationProblem):
        ctx.report(found=parsed.found, expected=parsed.expected)
        return None

    match parsed:
        case CharacteristicCheck(characteristic=code) | CharacteristicAdjustment(
            characteristic=code
        ):
            if code not in characteristics:
                ctx.report(found=code, expected="a code in the characteristics registry")
                return None
        case SkillGrant(skill=reference):
            if _skill_problem(skills.resolve(reference), reference, ctx):
                return None
        case SkillReference() as reference:
            if _skill_problem(skills.resolve(reference), reference, ctx):
                return None
        case BenefitItem(name=name) | QuantifiedBenefit(name=name):
            if name not in benefits:
                ctx.report(found=name, expected="a name in the benefits registry")
                return None

    return parsed


def _skill_problem(
    resolution: SkillResolution, reference: SkillReference, ctx: ParseContext
) -> bool:
    """Report a skill-resolution problem through `ctx` and return whether one
    was reported. Every outcome but `VALID` names the skills registry,
    because FR-013 asks a rejected name to report which registry it was
    checked against.
    """
    if resolution is SkillResolution.VALID:
        return False
    if resolution is SkillResolution.UNRECOGNIZED_SKILL:
        ctx.report(
            found=(
                f"{reference.name} ({reference.specialty})"
                if reference.specialty is not None
                else reference.name
            ),
            expected="a name in the skills registry",
        )
        return True
    if resolution is SkillResolution.SPECIALTY_NOT_ALLOWED:
        ctx.report(
            found=f"{reference.name} ({reference.specialty})",
            expected=f"a bare {reference.name}: the skills registry gives it no specialties",
        )
        return True
    ctx.report(
        found=f"{reference.name} ({reference.specialty})",
        expected=f"a specialty the skills registry gives {reference.name}",
    )
    return True


def _parse_throw(
    value: object,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    *,
    admits_characteristic: bool = True,
) -> Throw | None:
    table = ctx.require_dict(value, expected="a throw table")
    if table is None:
        return None

    allowed_keys = {"target", "dice"} | ({"characteristic"} if admits_characteristic else set())
    ctx.unrecognized_keys(table, allowed_keys)

    characteristic = None
    if "characteristic" in table and admits_characteristic:
        code = table["characteristic"]
        if not isinstance(code, str):
            ctx.at("characteristic").report(found=type_name(code), expected="a string")
        elif code not in characteristics:
            ctx.at("characteristic").report(
                found=code, expected="a code in the characteristics registry"
            )
        else:
            characteristic = code

    target = ctx.require_int(table, "target", minimum=1)
    dice = ctx.require_roll(table, "dice")
    if target is None or dice is None:
        return None
    return Throw(characteristic=characteristic, target=target, dice=dice)


def _parse_throws(
    raw: object, ctx: ParseContext, characteristics: CharacteristicRegistry
) -> Mapping[str, Throw]:
    if not isinstance(raw, dict):
        ctx.report(found=type_name(raw), expected="a throws table")
        return {}

    ctx.unrecognized_keys(raw, _ALL_THROWS)
    for key in _REQUIRED_THROWS:
        if key not in raw:
            ctx.at(key).report(found="missing", expected="a throw")

    throws: dict[str, Throw] = {}
    for key, value in raw.items():
        if key not in _ALL_THROWS:
            continue
        throw = _parse_throw(
            value, ctx.at(key), characteristics, admits_characteristic=key != "re-enlistment"
        )
        if throw is not None:
            throws[key] = throw
    return throws


def _parse_skill_table(
    value: object,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> SkillTable | None:
    table = ctx.require_dict(value, expected="a table")
    if table is None:
        return None

    ctx.unrecognized_keys(table, {"requires", "entries"})

    requires = None
    if "requires" in table:
        requires = _notation_field(
            table["requires"],
            EntryContext.GATE,
            ctx=ctx.at("requires"),
            characteristics=characteristics,
            skills=skills,
            benefits=benefits,
        )

    entries: tuple[SkillTableEntry, ...] | None = None
    raw_entries = ctx.require_list(
        table, "entries", expected="at least one entry", expected_missing="a non-empty array"
    )
    if raw_entries is not None:
        parsed_entries = []
        ok = True
        for index, item in enumerate(raw_entries):
            resolved = _notation_field(
                item,
                EntryContext.SKILL_TABLE,
                ctx=ctx.at("entries", index),
                characteristics=characteristics,
                skills=skills,
                benefits=benefits,
            )
            if resolved is None:
                ok = False
            else:
                parsed_entries.append(resolved)
        if ok:
            entries = tuple(parsed_entries)

    if entries is None:
        return None
    return SkillTable(requires=requires, entries=entries)


def _parse_tables(
    raw: object,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> Mapping[str, SkillTable]:
    if not isinstance(raw, dict):
        ctx.report(found=type_name(raw), expected="a tables table")
        return {}

    ctx.unrecognized_keys(raw, _ALL_TABLES)
    for key in _REQUIRED_TABLES:
        if key not in raw:
            ctx.at(key).report(found="missing", expected="a table")

    tables: dict[str, SkillTable] = {}
    for key, value in raw.items():
        if key not in _ALL_TABLES:
            continue
        table = _parse_skill_table(value, ctx.at(key), characteristics, skills, benefits)
        if table is not None:
            tables[key] = table
    return tables


def _parse_rank(
    value: object,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> Rank | None:
    table = ctx.require_dict(value, expected="a rank table")
    if table is None:
        return None

    ctx.unrecognized_keys(table, {"rank", "title", "bonus"})

    rank_position = ctx.require_int(table, "rank", minimum=0)

    title = ""
    if "title" in table:
        raw_title = table["title"]
        if not isinstance(raw_title, str) or not raw_title:
            found = "an empty string" if raw_title == "" else type_name(raw_title)
            ctx.at("title").report(found=found, expected="a non-empty string")
            title = None
        else:
            title = raw_title

    bonus = None
    if "bonus" in table:
        bonus = _notation_field(
            table["bonus"],
            EntryContext.SKILL_TABLE,
            ctx=ctx.at("bonus"),
            characteristics=characteristics,
            skills=skills,
            benefits=benefits,
        )

    if rank_position is None or title is None:
        return None
    return Rank(rank=rank_position, title=title, bonus=bonus)


def _parse_ranks(
    raw: list,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> tuple[Rank, ...] | None:
    ranks: list[Rank] = []
    positions_seen: set[int] = set()
    ok = True
    for index, item in enumerate(raw):
        rank = _parse_rank(item, ctx.at(index), characteristics, skills, benefits)
        if rank is None:
            ok = False
            continue
        if rank.rank in positions_seen:
            ctx.at(index, "rank").report(
                found=str(rank.rank), expected="a position distinct within its ladder"
            )
            ok = False
            continue
        positions_seen.add(rank.rank)
        ranks.append(rank)

    if not ok:
        return None

    base = min(positions_seen)
    contiguous = set(range(base, base + len(positions_seen)))
    if positions_seen != contiguous:
        missing = sorted(contiguous - positions_seen)
        ctx.report(
            found=f"positions {sorted(positions_seen)}",
            expected=f"contiguous from {base}: missing {missing}",
        )
        return None

    return tuple(sorted(ranks, key=lambda rank: rank.rank))


def _parse_ladder(
    value: object,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> RankLadder | None:
    table = ctx.require_dict(value, expected="a ladder table")
    if table is None:
        return None

    ctx.unrecognized_keys(table, {"name", "role", "ranks"})

    name = ctx.require_string(table, "name")

    role = None
    if "role" not in table:
        ctx.at("role").report(
            found="missing", expected=f"one of: {', '.join(sorted(_LADDER_ROLES))}"
        )
    else:
        raw_role = table["role"]
        if raw_role not in _LADDER_ROLES:
            ctx.at("role").report(
                found=repr(raw_role), expected=f"one of: {', '.join(sorted(_LADDER_ROLES))}"
            )
        else:
            role = raw_role

    raw_ranks = ctx.require_list(table, "ranks", expected="at least one rank")
    ranks = (
        _parse_ranks(raw_ranks, ctx.at("ranks"), characteristics, skills, benefits)
        if raw_ranks is not None
        else None
    )

    if name is None or role is None or ranks is None:
        return None
    return RankLadder(name=name, role=role, ranks=ranks)


def _parse_ladders(
    raw: list,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> tuple[RankLadder, ...] | None:
    ladders: list[RankLadder] = []
    names_seen: set[str] = set()
    ok = True
    for index, item in enumerate(raw):
        ladder = _parse_ladder(item, ctx.at(index), characteristics, skills, benefits)
        if ladder is None:
            ok = False
            continue
        if ladder.name in names_seen:
            ctx.at(index, "name").report(
                found=ladder.name, expected="a name distinct within the career"
            )
            ok = False
            continue
        names_seen.add(ladder.name)
        ladders.append(ladder)

    if not ok:
        return None

    entry_count = sum(1 for ladder in ladders if ladder.role == "entry")
    if entry_count != 1:
        ctx.report(
            found=f"{entry_count} ladders with role 'entry'",
            expected="exactly one ladder with role 'entry'",
        )
        ok = False

    commissioned_count = sum(1 for ladder in ladders if ladder.role == "commissioned")
    if commissioned_count > 1:
        ctx.report(
            found=f"{commissioned_count} ladders with role 'commissioned'",
            expected="at most one ladder with role 'commissioned'",
        )
        ok = False

    # `run()` (generator.py) grants the entry ladder's rank-zero bonus
    # unconditionally on entering a career (FR-007); a ladder with no
    # rank 0 has nothing for that bare `next(...)` to find (T182).
    for index, ladder in enumerate(ladders):
        if ladder.role == "entry" and not any(rank.rank == 0 for rank in ladder.ranks):
            ctx.at(index, "ranks").report(
                found="no rank 0",
                expected="a rank 0, since the entry ladder's bonus is always granted there",
            )
            ok = False

    if not ok:
        return None
    return tuple(ladders)


def _parse_mustering_out(
    value: object,
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> MusteringOut | None:
    table = ctx.require_dict(value, expected="a mustering-out table")
    if table is None:
        return None

    ctx.unrecognized_keys(table, {"cash", "benefits"})

    cash: tuple[int, ...] | None = None
    raw_cash = ctx.require_list(
        table, "cash", expected="at least one amount", expected_missing="a non-empty array"
    )
    if raw_cash is not None:
        amounts = []
        ok = True
        for index, item in enumerate(raw_cash):
            if not isinstance(item, int) or isinstance(item, bool):
                ctx.at("cash", index).report(found=type_name(item), expected="an integer")
                ok = False
            elif item < 0:
                ctx.at("cash", index).report(found=str(item), expected="a non-negative integer")
                ok = False
            else:
                amounts.append(item)
        if ok:
            cash = tuple(amounts)

    mustering_benefits: (
        tuple[BenefitItem | CharacteristicAdjustment | QuantifiedBenefit, ...] | None
    ) = None
    raw_benefits = ctx.require_list(
        table, "benefits", expected="at least one benefit", expected_missing="a non-empty array"
    )
    if raw_benefits is not None:
        items = []
        ok = True
        for index, item in enumerate(raw_benefits):
            resolved = _notation_field(
                item,
                EntryContext.BENEFIT_TABLE,
                ctx=ctx.at("benefits", index),
                characteristics=characteristics,
                skills=skills,
                benefits=benefits,
            )
            if resolved is None:
                ok = False
            else:
                items.append(resolved)
        if ok:
            mustering_benefits = tuple(items)

    if cash is None or mustering_benefits is None:
        return None
    return MusteringOut(cash=cash, benefits=mustering_benefits)


def parse_career(
    data: Mapping[str, object],
    ctx: ParseContext,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> CareerDefinition | None:
    ctx.unrecognized_keys(
        data,
        HEADER_KEYS
        | {
            "name",
            "medical-tier",
            "always-available",
            "re-enterable",
            "throws",
            "tables",
            "ladders",
            "mustering-out",
        },
    )

    name = ctx.require_string(data, "name")
    medical_tier = ctx.require_string(data, "medical-tier")

    always_available = ctx.optional_bool(data, "always-available")
    re_enterable = ctx.optional_bool(data, "re-enterable")

    throws: Mapping[str, Throw] = {}
    if "throws" not in data:
        ctx.at("throws").report(found="missing", expected="a throws table")
    else:
        throws = _parse_throws(data["throws"], ctx.at("throws"), characteristics)

    tables: Mapping[str, SkillTable] = {}
    if "tables" not in data:
        ctx.at("tables").report(found="missing", expected="a tables table")
    else:
        tables = _parse_tables(data["tables"], ctx.at("tables"), characteristics, skills, benefits)

    raw_ladders = ctx.require_list(data, "ladders", expected="at least one ladder")
    ladders = (
        _parse_ladders(raw_ladders, ctx.at("ladders"), characteristics, skills, benefits)
        if raw_ladders is not None
        else None
    )

    mustering_out: MusteringOut | None = None
    if "mustering-out" not in data:
        ctx.at("mustering-out").report(found="missing", expected="a mustering-out table")
    else:
        mustering_out = _parse_mustering_out(
            data["mustering-out"], ctx.at("mustering-out"), characteristics, skills, benefits
        )

    if ctx.failed or name is None or medical_tier is None:
        return None

    return CareerDefinition(
        name=name,
        medical_tier=medical_tier,
        always_available=always_available,
        re_enterable=re_enterable,
        throws=MappingProxyType(dict(throws)),
        tables=MappingProxyType(dict(tables)),
        ladders=ladders,
        mustering_out=mustering_out,
    )
