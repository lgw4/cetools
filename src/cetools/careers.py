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

from cetools.errors import ValidationProblem, type_name
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
from cetools.schema import (
    optional_bool,
    require_dict,
    require_int,
    require_roll,
    require_string,
    unrecognized_key_problems,
)

type SkillTableEntry = SkillReference | SkillGrant | CharacteristicAdjustment

_HEADER_KEYS = frozenset({"schema", "schema-version"})
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
    file: str,
    location: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> object | ValidationProblem:
    if not isinstance(value, str):
        return ValidationProblem(
            file=file, location=location, found=type_name(value), expected="a notation string"
        )

    parsed = parse_entry(value, context)
    if isinstance(parsed, NotationProblem):
        return ValidationProblem(
            file=file, location=location, found=parsed.found, expected=parsed.expected
        )

    match parsed:
        case CharacteristicCheck(characteristic=code) | CharacteristicAdjustment(
            characteristic=code
        ):
            if code not in characteristics:
                return ValidationProblem(
                    file=file,
                    location=location,
                    found=code,
                    expected="a code in the characteristics registry",
                )
        case SkillGrant(skill=reference):
            problem = _skill_problem(skills.resolve(reference), reference, file, location)
            if problem is not None:
                return problem
        case SkillReference() as reference:
            problem = _skill_problem(skills.resolve(reference), reference, file, location)
            if problem is not None:
                return problem
        case BenefitItem(name=name) | QuantifiedBenefit(name=name):
            if name not in benefits:
                return ValidationProblem(
                    file=file,
                    location=location,
                    found=name,
                    expected="a name in the benefits registry",
                )

    return parsed


def _skill_problem(
    resolution: SkillResolution, reference: SkillReference, file: str, location: str
) -> ValidationProblem | None:
    """Every outcome but `VALID` names the skills registry, because FR-013
    asks a rejected name to report which registry it was checked against.
    """
    if resolution is SkillResolution.VALID:
        return None
    if resolution is SkillResolution.UNRECOGNIZED_SKILL:
        return ValidationProblem(
            file=file,
            location=location,
            found=(
                f"{reference.name} ({reference.specialty})"
                if reference.specialty is not None
                else reference.name
            ),
            expected="a name in the skills registry",
        )
    if resolution is SkillResolution.SPECIALTY_NOT_ALLOWED:
        return ValidationProblem(
            file=file,
            location=location,
            found=f"{reference.name} ({reference.specialty})",
            expected=f"a bare {reference.name}: the skills registry gives it no specialties",
        )
    return ValidationProblem(
        file=file,
        location=location,
        found=f"{reference.name} ({reference.specialty})",
        expected=f"a specialty the skills registry gives {reference.name}",
    )


def _parse_throw(
    value: object,
    file: str,
    location: str,
    characteristics: CharacteristicRegistry,
    problems: list[ValidationProblem],
    *,
    admits_characteristic: bool = True,
) -> Throw | None:
    table = require_dict(value, file, location, "a throw table", problems)
    if table is None:
        return None

    allowed_keys = {"target", "dice"} | ({"characteristic"} if admits_characteristic else set())
    problems.extend(unrecognized_key_problems(table, allowed_keys, file, f"{location}."))

    characteristic = None
    if "characteristic" in table and admits_characteristic:
        code = table["characteristic"]
        if not isinstance(code, str):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.characteristic",
                    found=type_name(code),
                    expected="a string",
                )
            )
        elif code not in characteristics:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.characteristic",
                    found=code,
                    expected="a code in the characteristics registry",
                )
            )
        else:
            characteristic = code

    target = require_int(table, "target", file, f"{location}.target", problems, minimum=1)
    dice = require_roll(table, "dice", file, f"{location}.dice", problems)
    if target is None or dice is None:
        return None
    return Throw(characteristic=characteristic, target=target, dice=dice)


def _parse_throws(
    raw: object,
    file: str,
    characteristics: CharacteristicRegistry,
    problems: list[ValidationProblem],
) -> Mapping[str, Throw]:
    if not isinstance(raw, dict):
        problems.append(
            ValidationProblem(
                file=file, location="throws", found=type_name(raw), expected="a throws table"
            )
        )
        return {}

    problems.extend(unrecognized_key_problems(raw, _ALL_THROWS, file, "throws."))
    for key in _REQUIRED_THROWS:
        if key not in raw:
            problems.append(
                ValidationProblem(
                    file=file, location=f"throws.{key}", found="missing", expected="a throw"
                )
            )

    throws: dict[str, Throw] = {}
    for key, value in raw.items():
        if key not in _ALL_THROWS:
            continue
        throw = _parse_throw(
            value,
            file,
            f"throws.{key}",
            characteristics,
            problems,
            admits_characteristic=key != "re-enlistment",
        )
        if throw is not None:
            throws[key] = throw
    return throws


def _parse_skill_table(
    value: object,
    file: str,
    location: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
    problems: list[ValidationProblem],
) -> SkillTable | None:
    table = require_dict(value, file, location, "a table", problems)
    if table is None:
        return None

    problems.extend(
        unrecognized_key_problems(table, {"requires", "entries"}, file, f"{location}.")
    )

    requires = None
    if "requires" in table:
        resolved = _notation_field(
            table["requires"],
            EntryContext.GATE,
            file=file,
            location=f"{location}.requires",
            characteristics=characteristics,
            skills=skills,
            benefits=benefits,
        )
        if isinstance(resolved, ValidationProblem):
            problems.append(resolved)
        else:
            requires = resolved

    entries: tuple[SkillTableEntry, ...] | None = None
    if "entries" not in table:
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.entries",
                found="missing",
                expected="a non-empty array",
            )
        )
    else:
        raw_entries = table["entries"]
        if not isinstance(raw_entries, list) or not raw_entries:
            found = (
                type_name(raw_entries) if not isinstance(raw_entries, list) else "an empty array"
            )
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.entries",
                    found=found,
                    expected="at least one entry",
                )
            )
        else:
            parsed_entries = []
            ok = True
            for index, item in enumerate(raw_entries):
                resolved = _notation_field(
                    item,
                    EntryContext.SKILL_TABLE,
                    file=file,
                    location=f"{location}.entries[{index}]",
                    characteristics=characteristics,
                    skills=skills,
                    benefits=benefits,
                )
                if isinstance(resolved, ValidationProblem):
                    problems.append(resolved)
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
    file: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
    problems: list[ValidationProblem],
) -> Mapping[str, SkillTable]:
    if not isinstance(raw, dict):
        problems.append(
            ValidationProblem(
                file=file, location="tables", found=type_name(raw), expected="a tables table"
            )
        )
        return {}

    problems.extend(unrecognized_key_problems(raw, _ALL_TABLES, file, "tables."))
    for key in _REQUIRED_TABLES:
        if key not in raw:
            problems.append(
                ValidationProblem(
                    file=file, location=f"tables.{key}", found="missing", expected="a table"
                )
            )

    tables: dict[str, SkillTable] = {}
    for key, value in raw.items():
        if key not in _ALL_TABLES:
            continue
        table = _parse_skill_table(
            value, file, f"tables.{key}", characteristics, skills, benefits, problems
        )
        if table is not None:
            tables[key] = table
    return tables


def _parse_rank(
    value: object,
    file: str,
    location: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
    problems: list[ValidationProblem],
) -> Rank | None:
    table = require_dict(value, file, location, "a rank table", problems)
    if table is None:
        return None

    problems.extend(
        unrecognized_key_problems(table, {"rank", "title", "bonus"}, file, f"{location}.")
    )

    rank_position = require_int(table, "rank", file, f"{location}.rank", problems, minimum=0)

    title = ""
    if "title" in table:
        raw_title = table["title"]
        if not isinstance(raw_title, str) or not raw_title:
            found = "an empty string" if raw_title == "" else type_name(raw_title)
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.title",
                    found=found,
                    expected="a non-empty string",
                )
            )
            title = None
        else:
            title = raw_title

    bonus = None
    if "bonus" in table:
        resolved = _notation_field(
            table["bonus"],
            EntryContext.SKILL_TABLE,
            file=file,
            location=f"{location}.bonus",
            characteristics=characteristics,
            skills=skills,
            benefits=benefits,
        )
        if isinstance(resolved, ValidationProblem):
            problems.append(resolved)
        else:
            bonus = resolved

    if rank_position is None or title is None:
        return None
    return Rank(rank=rank_position, title=title, bonus=bonus)


def _parse_ranks(
    raw: object,
    file: str,
    location: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
    problems: list[ValidationProblem],
) -> tuple[Rank, ...] | None:
    if not isinstance(raw, list) or not raw:
        found = type_name(raw) if not isinstance(raw, list) else "an empty array"
        problems.append(
            ValidationProblem(
                file=file, location=location, found=found, expected="at least one rank"
            )
        )
        return None

    ranks: list[Rank] = []
    positions_seen: set[int] = set()
    ok = True
    for index, item in enumerate(raw):
        rank = _parse_rank(
            item, file, f"{location}[{index}]", characteristics, skills, benefits, problems
        )
        if rank is None:
            ok = False
            continue
        if rank.rank in positions_seen:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}[{index}].rank",
                    found=str(rank.rank),
                    expected="a position distinct within its ladder",
                )
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
        problems.append(
            ValidationProblem(
                file=file,
                location=location,
                found=f"positions {sorted(positions_seen)}",
                expected=f"contiguous from {base}: missing {missing}",
            )
        )
        return None

    return tuple(sorted(ranks, key=lambda rank: rank.rank))


def _parse_ladder(
    value: object,
    file: str,
    location: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
    problems: list[ValidationProblem],
) -> RankLadder | None:
    table = require_dict(value, file, location, "a ladder table", problems)
    if table is None:
        return None

    problems.extend(
        unrecognized_key_problems(table, {"name", "role", "ranks"}, file, f"{location}.")
    )

    name = require_string(table, "name", file, f"{location}.name", problems)

    role = None
    if "role" not in table:
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.role",
                found="missing",
                expected=f"one of: {', '.join(sorted(_LADDER_ROLES))}",
            )
        )
    else:
        raw_role = table["role"]
        if raw_role not in _LADDER_ROLES:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.role",
                    found=repr(raw_role),
                    expected=f"one of: {', '.join(sorted(_LADDER_ROLES))}",
                )
            )
        else:
            role = raw_role

    ranks: tuple[Rank, ...] | None = None
    if "ranks" not in table:
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.ranks",
                found="missing",
                expected="at least one rank",
            )
        )
    else:
        ranks = _parse_ranks(
            table["ranks"], file, f"{location}.ranks", characteristics, skills, benefits, problems
        )

    if name is None or role is None or ranks is None:
        return None
    return RankLadder(name=name, role=role, ranks=ranks)


def _parse_ladders(
    raw: object,
    file: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
    problems: list[ValidationProblem],
) -> tuple[RankLadder, ...] | None:
    if not isinstance(raw, list) or not raw:
        found = type_name(raw) if not isinstance(raw, list) else "an empty array"
        problems.append(
            ValidationProblem(
                file=file, location="ladders", found=found, expected="at least one ladder"
            )
        )
        return None

    ladders: list[RankLadder] = []
    names_seen: set[str] = set()
    ok = True
    for index, item in enumerate(raw):
        ladder = _parse_ladder(
            item, file, f"ladders[{index}]", characteristics, skills, benefits, problems
        )
        if ladder is None:
            ok = False
            continue
        if ladder.name in names_seen:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"ladders[{index}].name",
                    found=ladder.name,
                    expected="a name distinct within the career",
                )
            )
            ok = False
            continue
        names_seen.add(ladder.name)
        ladders.append(ladder)

    if not ok:
        return None

    entry_count = sum(1 for ladder in ladders if ladder.role == "entry")
    if entry_count != 1:
        problems.append(
            ValidationProblem(
                file=file,
                location="ladders",
                found=f"{entry_count} ladders with role 'entry'",
                expected="exactly one ladder with role 'entry'",
            )
        )
        ok = False

    commissioned_count = sum(1 for ladder in ladders if ladder.role == "commissioned")
    if commissioned_count > 1:
        problems.append(
            ValidationProblem(
                file=file,
                location="ladders",
                found=f"{commissioned_count} ladders with role 'commissioned'",
                expected="at most one ladder with role 'commissioned'",
            )
        )
        ok = False

    # `run()` (generator.py) grants the entry ladder's rank-zero bonus
    # unconditionally on entering a career (FR-007); a ladder with no
    # rank 0 has nothing for that bare `next(...)` to find (T182).
    for index, ladder in enumerate(ladders):
        if ladder.role == "entry" and not any(rank.rank == 0 for rank in ladder.ranks):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"ladders[{index}].ranks",
                    found="no rank 0",
                    expected="a rank 0, since the entry ladder's bonus is always granted there",
                )
            )
            ok = False

    if not ok:
        return None
    return tuple(ladders)


def _parse_mustering_out(
    value: object,
    file: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
    problems: list[ValidationProblem],
) -> MusteringOut | None:
    location = "mustering-out"
    table = require_dict(value, file, location, "a mustering-out table", problems)
    if table is None:
        return None

    problems.extend(unrecognized_key_problems(table, {"cash", "benefits"}, file, f"{location}."))

    cash: tuple[int, ...] | None = None
    if "cash" not in table:
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.cash",
                found="missing",
                expected="a non-empty array",
            )
        )
    else:
        raw_cash = table["cash"]
        if not isinstance(raw_cash, list) or not raw_cash:
            found = type_name(raw_cash) if not isinstance(raw_cash, list) else "an empty array"
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.cash",
                    found=found,
                    expected="at least one amount",
                )
            )
        else:
            amounts = []
            ok = True
            for index, item in enumerate(raw_cash):
                if not isinstance(item, int) or isinstance(item, bool):
                    problems.append(
                        ValidationProblem(
                            file=file,
                            location=f"{location}.cash[{index}]",
                            found=type_name(item),
                            expected="an integer",
                        )
                    )
                    ok = False
                elif item < 0:
                    problems.append(
                        ValidationProblem(
                            file=file,
                            location=f"{location}.cash[{index}]",
                            found=str(item),
                            expected="a non-negative integer",
                        )
                    )
                    ok = False
                else:
                    amounts.append(item)
            if ok:
                cash = tuple(amounts)

    mustering_benefits: (
        tuple[BenefitItem | CharacteristicAdjustment | QuantifiedBenefit, ...] | None
    ) = None
    if "benefits" not in table:
        problems.append(
            ValidationProblem(
                file=file,
                location=f"{location}.benefits",
                found="missing",
                expected="a non-empty array",
            )
        )
    else:
        raw_benefits = table["benefits"]
        if not isinstance(raw_benefits, list) or not raw_benefits:
            found = (
                type_name(raw_benefits) if not isinstance(raw_benefits, list) else "an empty array"
            )
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.benefits",
                    found=found,
                    expected="at least one benefit",
                )
            )
        else:
            items = []
            ok = True
            for index, item in enumerate(raw_benefits):
                resolved = _notation_field(
                    item,
                    EntryContext.BENEFIT_TABLE,
                    file=file,
                    location=f"{location}.benefits[{index}]",
                    characteristics=characteristics,
                    skills=skills,
                    benefits=benefits,
                )
                if isinstance(resolved, ValidationProblem):
                    problems.append(resolved)
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
    file: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
) -> tuple[CareerDefinition | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(
        unrecognized_key_problems(
            data,
            _HEADER_KEYS
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
            file,
        )
    )

    name = require_string(data, "name", file, "name", problems)
    medical_tier = require_string(data, "medical-tier", file, "medical-tier", problems)

    always_available = optional_bool(data, "always-available", file, "always-available", problems)
    re_enterable = optional_bool(data, "re-enterable", file, "re-enterable", problems)

    throws: Mapping[str, Throw] = {}
    if "throws" not in data:
        problems.append(
            ValidationProblem(
                file=file, location="throws", found="missing", expected="a throws table"
            )
        )
    else:
        throws = _parse_throws(data["throws"], file, characteristics, problems)

    tables: Mapping[str, SkillTable] = {}
    if "tables" not in data:
        problems.append(
            ValidationProblem(
                file=file, location="tables", found="missing", expected="a tables table"
            )
        )
    else:
        tables = _parse_tables(data["tables"], file, characteristics, skills, benefits, problems)

    ladders: tuple[RankLadder, ...] | None = ()
    if "ladders" not in data:
        problems.append(
            ValidationProblem(
                file=file, location="ladders", found="missing", expected="at least one ladder"
            )
        )
        ladders = None
    else:
        ladders = _parse_ladders(
            data["ladders"], file, characteristics, skills, benefits, problems
        )

    mustering_out: MusteringOut | None = None
    if "mustering-out" not in data:
        problems.append(
            ValidationProblem(
                file=file,
                location="mustering-out",
                found="missing",
                expected="a mustering-out table",
            )
        )
    else:
        mustering_out = _parse_mustering_out(
            data["mustering-out"], file, characteristics, skills, benefits, problems
        )

    if problems or name is None or medical_tier is None:
        return None, tuple(problems)

    return (
        CareerDefinition(
            name=name,
            medical_tier=medical_tier,
            always_available=always_available,
            re_enterable=re_enterable,
            throws=MappingProxyType(dict(throws)),
            tables=MappingProxyType(dict(tables)),
            ladders=ladders,
            mustering_out=mustering_out,
        ),
        (),
    )
