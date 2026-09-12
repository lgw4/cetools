"""The two name table kinds and the name roll (contracts/data-files.md).

`GivenNameTable` and `SurnameTable` own their own schemas, exactly as the
registries do; the roll is here beside the tables it weights, because
`roll_name` is what FR-043f's uniform-over-tables-in-force rule constrains.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from cetools.dice import Roller
from cetools.errors import type_name
from cetools.schema import HEADER_KEYS, ParseContext


def _parse_name_array(raw: list, ctx: ParseContext) -> tuple[str, ...] | None:
    names: list[str] = []
    ok = True
    for index, item in enumerate(raw):
        if not isinstance(item, str) or not item:
            found = type_name(item) if not isinstance(item, str) else "an empty string"
            ctx.at(index).report(found=found, expected="a non-empty string")
            ok = False
            continue
        names.append(item)
    if not ok:
        return None
    return tuple(names)


@dataclass(frozen=True, slots=True)
class GivenNameTable:
    """No `gender` field exists anywhere in this schema (FR-043b): the key
    set is closed to `source` and `names`.
    """

    source: str
    names: tuple[str, ...]


def parse_given_names(data: Mapping[str, object], ctx: ParseContext) -> GivenNameTable | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"source", "names"})

    source = ctx.require_string(data, "source")

    raw_names = ctx.require_list(
        data, "names", expected="at least one entry", expected_missing="an array"
    )
    names = _parse_name_array(raw_names, ctx.at("names")) if raw_names is not None else None

    if ctx.failed or source is None or names is None:
        return None
    return GivenNameTable(source=source, names=names)


@dataclass(frozen=True, slots=True)
class SurnameEntry:
    """`people` is required of the shipped indigenous-peoples table by a
    test (FR-043d, SC-015b) and optional here, because an override adding a
    region carries no such obligation.
    """

    name: str
    people: str = ""


def _parse_surname_entry(value: object, ctx: ParseContext) -> SurnameEntry | None:
    if not isinstance(value, dict):
        ctx.report(found=type_name(value), expected="a table")
        return None

    ctx.unrecognized_keys(value, {"name", "people"})

    name = ctx.require_string(value, "name")

    people = ""
    if "people" in value:
        raw_people = value["people"]
        if not isinstance(raw_people, str):
            ctx.at("people").report(found=type_name(raw_people), expected="a string")
        else:
            people = raw_people

    if name is None or ctx.failed:
        return None
    return SurnameEntry(name=name, people=people)


@dataclass(frozen=True, slots=True)
class SurnameTable:
    """`region` is distinct across the tables in force, checked as a
    cross-file rule. No `gender` field exists anywhere in this schema
    (FR-043b): the key set is closed to `region`, `source`, and `names`.
    """

    region: str
    source: str
    names: tuple[SurnameEntry, ...]


def parse_surnames(data: Mapping[str, object], ctx: ParseContext) -> SurnameTable | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"region", "source", "names"})

    region = ctx.require_string(data, "region")
    source = ctx.require_string(data, "source")

    names: tuple[SurnameEntry, ...] | None = None
    raw_names = ctx.require_list(
        data, "names", expected="at least one entry", expected_missing="an array"
    )
    if raw_names is not None:
        parsed: list[SurnameEntry] = []
        ok = True
        for index, item in enumerate(raw_names):
            entry = _parse_surname_entry(item, ctx.at("names", index))
            if entry is None:
                ok = False
            else:
                parsed.append(entry)
        if ok:
            names = tuple(parsed)

    if ctx.failed or region is None or source is None or names is None:
        return None
    return SurnameTable(region=region, source=source, names=names)


@dataclass(frozen=True, slots=True)
class Name:
    """What a roll produces. Not stored on the character, which carries the
    four fields flat.
    """

    given_name: str
    surname: str
    region: str
    full: str


def roll_name(roller: Roller, given: GivenNameTable, surnames: Mapping[str, SurnameTable]) -> Name:
    """Select a region uniformly over the surname tables in force, then a
    surname within it, then a given name uniformly (FR-043f, FR-043g).

    Sorted by region rather than trusting the caller's mapping order:
    `surnames` is keyed by file stem for composition, and this draw's
    determinism must not depend on that key's collation.
    """
    tables = sorted(surnames.values(), key=lambda table: table.region)
    region_table = tables[roller.die(len(tables)) - 1]
    entry = region_table.names[roller.die(len(region_table.names)) - 1]
    given_name = given.names[roller.die(len(given.names)) - 1]
    return Name(
        given_name=given_name,
        surname=entry.name,
        region=region_table.region,
        full=f"{given_name} {entry.name}",
    )
