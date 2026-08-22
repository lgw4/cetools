"""The two name table kinds and the name roll (contracts/data-files.md).

`GivenNameTable` and `SurnameTable` own their own schemas, exactly as the
registries do; the roll is here beside the tables it weights, because
`roll_name` is what FR-043f's uniform-over-tables-in-force rule constrains.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from cetools.dice import Roller
from cetools.errors import ValidationProblem, type_name

_HEADER_KEYS = frozenset({"schema", "schema-version"})


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
        found = type_name(value) if not isinstance(value, str) else "an empty string"
        problems.append(
            ValidationProblem(
                file=file, location=location, found=found, expected="a non-empty string"
            )
        )
        return None
    return value


def _require_name_array(
    raw: object, file: str, location: str
) -> tuple[tuple[str, ...] | None, list[ValidationProblem]]:
    if not isinstance(raw, list) or not raw:
        found = type_name(raw) if not isinstance(raw, list) else "an empty array"
        return None, [
            ValidationProblem(
                file=file, location=location, found=found, expected="at least one entry"
            )
        ]
    problems: list[ValidationProblem] = []
    names: list[str] = []
    ok = True
    for index, item in enumerate(raw):
        if not isinstance(item, str) or not item:
            found = type_name(item) if not isinstance(item, str) else "an empty string"
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}[{index}]",
                    found=found,
                    expected="a non-empty string",
                )
            )
            ok = False
            continue
        names.append(item)
    if not ok:
        return None, problems
    return tuple(names), problems


@dataclass(frozen=True, slots=True)
class GivenNameTable:
    """No `gender` field exists anywhere in this schema (FR-043b): the key
    set is closed to `source` and `names`.
    """

    source: str
    names: tuple[str, ...]


def parse_given_names(
    data: Mapping[str, object], file: str
) -> tuple[GivenNameTable | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(_unrecognized_key_problems(data, _HEADER_KEYS | {"source", "names"}, file))

    source = _require_string(data, "source", file, "source", problems)

    names: tuple[str, ...] | None = None
    if "names" not in data:
        problems.append(
            ValidationProblem(file=file, location="names", found="missing", expected="an array")
        )
    else:
        names, sub_problems = _require_name_array(data["names"], file, "names")
        problems.extend(sub_problems)

    if problems or source is None or names is None:
        return None, tuple(problems)
    return GivenNameTable(source=source, names=names), ()


@dataclass(frozen=True, slots=True)
class SurnameEntry:
    """`people` is required of the shipped indigenous-peoples table by a
    test (FR-043d, SC-015b) and optional here, because an override adding a
    region carries no such obligation.
    """

    name: str
    people: str = ""


def _parse_surname_entry(
    value: object, file: str, location: str
) -> tuple[SurnameEntry | None, list[ValidationProblem]]:
    problems: list[ValidationProblem] = []
    if not isinstance(value, dict):
        problems.append(
            ValidationProblem(
                file=file, location=location, found=type_name(value), expected="a table"
            )
        )
        return None, problems

    problems.extend(_unrecognized_key_problems(value, {"name", "people"}, file, f"{location}."))

    name = _require_string(value, "name", file, f"{location}.name", problems)

    people = ""
    if "people" in value:
        raw_people = value["people"]
        if not isinstance(raw_people, str):
            problems.append(
                ValidationProblem(
                    file=file,
                    location=f"{location}.people",
                    found=type_name(raw_people),
                    expected="a string",
                )
            )
        else:
            people = raw_people

    if name is None or problems:
        return None, problems
    return SurnameEntry(name=name, people=people), problems


@dataclass(frozen=True, slots=True)
class SurnameTable:
    """`region` is distinct across the tables in force, checked as a
    cross-file rule. No `gender` field exists anywhere in this schema
    (FR-043b): the key set is closed to `region`, `source`, and `names`.
    """

    region: str
    source: str
    names: tuple[SurnameEntry, ...]


def parse_surnames(
    data: Mapping[str, object], file: str
) -> tuple[SurnameTable | None, tuple[ValidationProblem, ...]]:
    problems: list[ValidationProblem] = []
    problems.extend(
        _unrecognized_key_problems(data, _HEADER_KEYS | {"region", "source", "names"}, file)
    )

    region = _require_string(data, "region", file, "region", problems)
    source = _require_string(data, "source", file, "source", problems)

    names: tuple[SurnameEntry, ...] | None = None
    if "names" not in data:
        problems.append(
            ValidationProblem(file=file, location="names", found="missing", expected="an array")
        )
    else:
        raw = data["names"]
        if not isinstance(raw, list) or not raw:
            found = type_name(raw) if not isinstance(raw, list) else "an empty array"
            problems.append(
                ValidationProblem(
                    file=file, location="names", found=found, expected="at least one entry"
                )
            )
        else:
            parsed: list[SurnameEntry] = []
            ok = True
            for index, item in enumerate(raw):
                entry, sub_problems = _parse_surname_entry(item, file, f"names[{index}]")
                problems.extend(sub_problems)
                if entry is None:
                    ok = False
                else:
                    parsed.append(entry)
            if ok:
                names = tuple(parsed)

    if problems or region is None or source is None or names is None:
        return None, tuple(problems)
    return SurnameTable(region=region, source=source, names=names), ()


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
