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

from cetools.errors import ValidationProblem
from cetools.notation import (
    BenefitItem,
    CharacteristicAdjustment,
    CharacteristicCheck,
    EntryContext,
    NotationProblem,
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

type SkillTableEntry = SkillReference | SkillGrant | CharacteristicAdjustment

_HEADER_KEYS = frozenset({"schema", "schema-version"})
_REQUIRED_THROWS = ("qualification", "survival", "promotion", "re-enlistment")
_OPTIONAL_THROWS = ("commission",)
_ALL_THROWS = frozenset(_REQUIRED_THROWS) | frozenset(_OPTIONAL_THROWS)
_REQUIRED_TABLES = ("personal", "service", "advanced")
_OPTIONAL_TABLES = ("advanced-education",)
_ALL_TABLES = frozenset(_REQUIRED_TABLES) | frozenset(_OPTIONAL_TABLES)


@dataclass(frozen=True, slots=True)
class Throw:
    """`characteristic` is `None` when the throw takes no characteristic
    modifier, which is how re-enlistment is thrown. `target` is a plain
    value, never notation (FR-004a, FR-014).
    """

    characteristic: str | None
    target: int


@dataclass(frozen=True, slots=True)
class SkillTable:
    """`requires` is the gate (FR-015); `None` for an ungated table."""

    requires: CharacteristicCheck | None
    entries: tuple[SkillTableEntry, ...]


@dataclass(frozen=True, slots=True)
class Rank:
    """`bonus` admits the same forms as a skill table entry (FR-016)."""

    rank: int
    title: str
    bonus: SkillTableEntry | None


@dataclass(frozen=True, slots=True)
class RankLadder:
    name: str
    ranks: tuple[Rank, ...]


@dataclass(frozen=True, slots=True)
class MusteringOut:
    cash: tuple[int, ...]
    benefits: tuple[BenefitItem | CharacteristicAdjustment, ...]


@dataclass(frozen=True, slots=True)
class CareerDefinition:
    """`name` is a human label, not the composition identity (FR-019a)."""

    name: str
    throws: Mapping[str, Throw]
    tables: Mapping[str, SkillTable]
    ladders: tuple[RankLadder, ...]
    mustering_out: MusteringOut


def _unrecognized_key_problems(
    data: Mapping[str, object], allowed: frozenset[str], file: str, prefix: str = ""
) -> list[ValidationProblem]:
    extra = sorted(set(data) - allowed)
    return [
        ValidationProblem(
            file=file,
            location=f"{prefix}{key}",
            found=f"unrecognized key {key!r}",
            expected=f"one of: {', '.join(sorted(allowed))}",
        )
        for key in extra
    ]


def _require_dict(
    value: object, file: str, location: str, expected: str, problems: list[ValidationProblem]
) -> dict | None:
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type(value).__name__, expected=expected
            )
        )
        return None
    return value


def _require_string(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> str | None:
    if key not in container:
        problems.append(
            ValidationProblem(file=file, location=location, found="missing", expected="a string")
        )
        return None
    value = container[key]
    if not isinstance(value, str) or not value:
        found = type(value).__name__ if not isinstance(value, str) else "an empty string"
        problems.append(
            ValidationProblem(
                file=file, location=location, found=found, expected="a non-empty string"
            )
        )
        return None
    return value


def _require_int(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
    *,
    minimum: int | None = None,
) -> int | None:
    if key not in container:
        problems.append(
            ValidationProblem(file=file, location=location, found="missing", expected="an integer")
        )
        return None
    value = container[key]
    if not isinstance(value, int) or isinstance(value, bool):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type(value).__name__, expected="an integer"
            )
        )
        return None
    if minimum is not None and value < minimum:
        expected = "a positive integer" if minimum == 1 else f"an integer >= {minimum}"
        problems.append(
            ValidationProblem(file=file, location=location, found=str(value), expected=expected)
        )
        return None
    return value


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
            file=file, location=location, found=type(value).__name__, expected="a notation string"
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
                    expected="a known characteristic code",
                )
        case SkillGrant(skill=reference):
            problem = _skill_problem(skills.resolve(reference), reference, file, location)
            if problem is not None:
                return problem
        case SkillReference() as reference:
            problem = _skill_problem(skills.resolve(reference), reference, file, location)
            if problem is not None:
                return problem
        case BenefitItem(name=name):
            if name not in benefits:
                return ValidationProblem(
                    file=file, location=location, found=name, expected="a known benefit item"
                )

    return parsed


def _skill_problem(
    resolution: SkillResolution, reference: SkillReference, file: str, location: str
) -> ValidationProblem | None:
    if resolution is SkillResolution.VALID:
        return None
    if resolution is SkillResolution.UNRECOGNIZED_SKILL:
        return ValidationProblem(
            file=file, location=location, found=reference.name, expected="a known skill name"
        )
    if resolution is SkillResolution.SPECIALTY_NOT_ALLOWED:
        return ValidationProblem(
            file=file,
            location=location,
            found=f"{reference.name} ({reference.specialty})",
            expected=f"{reference.name} has no specialties",
        )
    return ValidationProblem(
        file=file,
        location=location,
        found=f"{reference.name} ({reference.specialty})",
        expected=f"a specialty {reference.name} recognizes",
    )


def _parse_throw(
    value: object,
    file: str,
    location: str,
    characteristics: CharacteristicRegistry,
    problems: list[ValidationProblem],
) -> Throw | None:
    table = _require_dict(value, file, location, "a throw table", problems)
    if table is None:
        return None

    problems.extend(
        _unrecognized_key_problems(table, {"characteristic", "target"}, file, f"{location}.")
    )

    characteristic = None
    if "characteristic" in table:
        code = table["characteristic"]
        if not isinstance(code, str):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.characteristic",
                    found=type(code).__name__,
                    expected="a string",
                )
            )
        elif code not in characteristics:
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.characteristic",
                    found=code,
                    expected="a known characteristic code",
                )
            )
        else:
            characteristic = code

    target = _require_int(table, "target", file, f"{location}.target", problems, minimum=1)
    if target is None:
        return None
    return Throw(characteristic=characteristic, target=target)


def _parse_throws(
    raw: object,
    file: str,
    characteristics: CharacteristicRegistry,
    problems: list[ValidationProblem],
) -> Mapping[str, Throw]:
    if not isinstance(raw, dict):
        problems.append(
            ValidationProblem(
                file=file, location="throws", found=type(raw).__name__, expected="a throws table"
            )
        )
        return {}

    problems.extend(_unrecognized_key_problems(raw, _ALL_THROWS, file, "throws."))
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
        throw = _parse_throw(value, file, f"throws.{key}", characteristics, problems)
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
    table = _require_dict(value, file, location, "a table", problems)
    if table is None:
        return None

    problems.extend(
        _unrecognized_key_problems(table, {"requires", "entries"}, file, f"{location}.")
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
                type(raw_entries).__name__
                if not isinstance(raw_entries, list)
                else "an empty array"
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
                file=file, location="tables", found=type(raw).__name__, expected="a tables table"
            )
        )
        return {}

    problems.extend(_unrecognized_key_problems(raw, _ALL_TABLES, file, "tables."))
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
    table = _require_dict(value, file, location, "a rank table", problems)
    if table is None:
        return None

    problems.extend(
        _unrecognized_key_problems(table, {"rank", "title", "bonus"}, file, f"{location}.")
    )

    rank_position = _require_int(table, "rank", file, f"{location}.rank", problems, minimum=0)
    title = _require_string(table, "title", file, f"{location}.title", problems)

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
        found = type(raw).__name__ if not isinstance(raw, list) else "an empty array"
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
    table = _require_dict(value, file, location, "a ladder table", problems)
    if table is None:
        return None

    problems.extend(_unrecognized_key_problems(table, {"name", "ranks"}, file, f"{location}."))

    name = _require_string(table, "name", file, f"{location}.name", problems)
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

    if name is None or ranks is None:
        return None
    return RankLadder(name=name, ranks=ranks)


def _parse_ladders(
    raw: object,
    file: str,
    characteristics: CharacteristicRegistry,
    skills: SkillRegistry,
    benefits: BenefitRegistry,
    problems: list[ValidationProblem],
) -> tuple[RankLadder, ...] | None:
    if not isinstance(raw, list) or not raw:
        found = type(raw).__name__ if not isinstance(raw, list) else "an empty array"
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
    table = _require_dict(value, file, location, "a mustering-out table", problems)
    if table is None:
        return None

    problems.extend(_unrecognized_key_problems(table, {"cash", "benefits"}, file, f"{location}."))

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
            found = type(raw_cash).__name__ if not isinstance(raw_cash, list) else "an empty array"
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
                            found=type(item).__name__,
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

    mustering_benefits: tuple[BenefitItem | CharacteristicAdjustment, ...] | None = None
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
                type(raw_benefits).__name__
                if not isinstance(raw_benefits, list)
                else "an empty array"
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
        _unrecognized_key_problems(
            data, _HEADER_KEYS | {"name", "throws", "tables", "ladders", "mustering-out"}, file
        )
    )

    name = _require_string(data, "name", file, "name", problems)

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

    if problems:
        return None, tuple(problems)

    return (
        CareerDefinition(
            name=name,
            throws=MappingProxyType(dict(throws)),
            tables=MappingProxyType(dict(tables)),
            ladders=ladders,
            mustering_out=mustering_out,
        ),
        (),
    )
