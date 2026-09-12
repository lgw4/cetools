"""The three shipped registries that give names meaning: characteristics,
skills, and benefit items (contracts/data-files.md).

Each `parse_*` function turns one file's already-parsed TOML dict into a
registry, collecting every problem rather than raising on the first
(research R7). The header keys `schema` and `schema-version` are accepted
here as known keys but not interpreted; the kind-and-version check itself is
`rules.py`'s job (T023), which runs before these functions are reached.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, auto
from types import MappingProxyType

from cetools.errors import RulesDataError, TaskError, type_name
from cetools.notation import SkillReference
from cetools.schema import HEADER_KEYS, ParseContext

_BAND_RANGE = re.compile(r"^(\d+)-(\d+)$")
_BAND_UNBOUNDED = re.compile(r"^(\d+)\+$")


@dataclass(frozen=True, slots=True)
class Band:
    """One row of the characteristic modifier table.

    `maximum` is `None` for the sole unbounded top band, which sorts last.
    """

    minimum: int
    maximum: int | None
    dm: int


@dataclass(frozen=True, slots=True)
class CharacteristicRegistry:
    """Code (`"INT"`) to label (`"Intellect"`), in the file's order, plus
    every other fact about a characteristic FR-039 puts in data rather than
    in engine code: which class it belongs to, the modifier bands every
    score is looked up against, and the pseudo-hex symbols the profile
    renders in.
    """

    names: Mapping[str, str]
    classes: Mapping[str, str] = MappingProxyType({})
    bands: tuple[Band, ...] = ()
    pseudo_hex_minimum: int = 0
    pseudo_hex: tuple[str, ...] = ()

    def __contains__(self, code: object) -> bool:
        return code in self.names

    def characteristic_dm(self, score: int) -> int:
        if score < 0:
            raise TaskError(f"characteristic must be non-negative, got {score}")
        for band in self.bands:
            if band.minimum <= score and (band.maximum is None or score <= band.maximum):
                return band.dm
        raise RulesDataError(f"no characteristic band covers score {score}")

    def symbol(self, score: int) -> str:
        """The pseudo-hex symbol for `score` (research R13).

        Raises `RulesDataError` naming the score and the declared range when
        `score` falls outside `pseudo_hex_minimum` through
        `pseudo_hex_minimum + len(pseudo_hex) - 1`. Unreachable from the
        shipped data, whose declared range covers every score a reduction can
        floor at or a throw can produce; reachable only from an override that
        declares a shorter table.
        """
        index = score - self.pseudo_hex_minimum
        if index < 0 or index >= len(self.pseudo_hex):
            top = self.pseudo_hex_minimum + len(self.pseudo_hex) - 1
            raise RulesDataError(
                f"characteristic score {score} is outside the declared pseudo-hex range "
                f"{self.pseudo_hex_minimum}-{top}"
            )
        return self.pseudo_hex[index]

    def floor(self) -> int:
        """The value a characteristic reduction clamps at: the bottom of the
        declared pseudo-hex range, so the rules cannot produce a score the
        symbols do not cover (research R13).
        """
        return self.pseudo_hex_minimum


class SkillResolution(Enum):
    """The four distinguishable outcomes of resolving a `SkillReference`
    against a `SkillRegistry` (FR-007, contracts/notation.md).
    """

    VALID = auto()
    UNRECOGNIZED_SKILL = auto()
    SPECIALTY_NOT_ALLOWED = auto()
    UNRECOGNIZED_SPECIALTY = auto()


@dataclass(frozen=True, slots=True)
class SkillRegistry:
    """Skill name to its permitted specialties; an empty tuple means none."""

    skills: Mapping[str, tuple[str, ...]]

    def resolve(self, reference: SkillReference) -> SkillResolution:
        specialties = self.skills.get(reference.name)
        if specialties is None:
            return SkillResolution.UNRECOGNIZED_SKILL
        if reference.specialty is None:
            return SkillResolution.VALID
        if not specialties:
            return SkillResolution.SPECIALTY_NOT_ALLOWED
        if reference.specialty not in specialties:
            return SkillResolution.UNRECOGNIZED_SPECIALTY
        return SkillResolution.VALID


@dataclass(frozen=True, slots=True)
class BenefitRegistry:
    """Benefit item names, in file order."""

    items: tuple[str, ...]

    def __contains__(self, name: object) -> bool:
        return name in self.items


def _parse_bands(data: object, ctx: ParseContext) -> tuple[Band, ...] | None:
    """Parse a `key -> modifier` table (`"N-M"` or `"N+"`) into bands sorted
    by `minimum`, exactly one unbounded (003-npc-generator contracts/data-files.md).

    Moved here, verbatim in shape, from the reader that used to parse
    `tasks.toml`'s `[characteristic-dms]`; the characteristics registry is
    where the bands live now (FR-039).
    """
    if not isinstance(data, dict) or not data:
        ctx.report(
            found=(
                "missing"
                if data is None
                else ("an empty table" if data == {} else type_name(data))
            ),
            expected=f"a [{ctx.location}] table with at least one entry",
        )
        return None

    bands: list[Band] = []
    unbounded_count = 0
    ok = True
    for key in data:
        value = ctx.require_int(data, key)
        if value is None:
            ok = False
            continue
        range_match = _BAND_RANGE.match(key)
        unbounded_match = _BAND_UNBOUNDED.match(key)
        if range_match:
            minimum, maximum = int(range_match.group(1)), int(range_match.group(2))
        elif unbounded_match:
            minimum, maximum = int(unbounded_match.group(1)), None
            unbounded_count += 1
        else:
            ctx.at(key).report(found=repr(key), expected="a key of the form N-M or N+")
            ok = False
            continue
        bands.append(Band(minimum=minimum, maximum=maximum, dm=value))

    if ok and unbounded_count != 1:
        ctx.report(
            found=f"{unbounded_count} unbounded bands",
            expected="exactly one unbounded band",
        )

    if ctx.failed:
        return None
    bands.sort(key=lambda band: band.minimum)
    return tuple(bands)


_CHARACTERISTIC_ENTRY_KEYS = frozenset({"label", "class"})


def _parse_characteristic_entry(entry: object, ctx: ParseContext) -> tuple[str | None, str | None]:
    entry_table = ctx.require_dict(entry, expected="a table with label and class")
    if entry_table is None:
        return None, None

    ctx.unrecognized_keys(entry_table, _CHARACTERISTIC_ENTRY_KEYS)

    label = ctx.require_string(entry_table, "label")
    characteristic_class = ctx.require_string(entry_table, "class")
    return label, characteristic_class


def _parse_pseudo_hex(data: object, ctx: ParseContext) -> tuple[int, tuple[str, ...]] | None:
    # `ctx` is the file-level carrier here, not one derived for "pseudo-hex":
    # the unrecognized-key check below must keep reporting a stray key at its
    # bare name rather than prefixed with "pseudo-hex.", which is what the
    # tree does before this migration. Converting it on the fragment carrier
    # its surroundings suggest would move a reported location, which FR-014
    # forbids. See inventory.md I-1.
    pseudo_hex_ctx = ctx.at("pseudo-hex")
    table = pseudo_hex_ctx.require_dict(data, expected="a [pseudo-hex] table")
    if table is None:
        return None

    ctx.unrecognized_keys(table, {"minimum", "symbols"})

    minimum = pseudo_hex_ctx.require_int(table, "minimum")

    symbols_raw = pseudo_hex_ctx.require_list(
        table, "symbols", expected="a non-empty array of strings"
    )
    symbols: tuple[str, ...] | None = None
    if symbols_raw is not None:
        parsed_symbols = []
        ok = True
        for index, symbol in enumerate(symbols_raw):
            if not isinstance(symbol, str) or not symbol:
                pseudo_hex_ctx.at("symbols", index).report(
                    found=(
                        type_name(symbol) if not isinstance(symbol, str) else "an empty string"
                    ),
                    expected="a non-empty string",
                )
                ok = False
                continue
            parsed_symbols.append(symbol)
        if ok:
            symbols = tuple(parsed_symbols)

    if minimum is None or symbols is None:
        return None
    return (minimum, symbols)


def parse_characteristics(
    data: Mapping[str, object], ctx: ParseContext
) -> CharacteristicRegistry | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"characteristics", "modifier-dms", "pseudo-hex"})

    characteristics_ctx = ctx.at("characteristics")
    table = data.get("characteristics")
    names: dict[str, str] = {}
    classes: dict[str, str] = {}
    if not isinstance(table, dict):
        characteristics_ctx.report(
            found="missing" if table is None else type_name(table),
            expected="a [characteristics] table with at least one entry",
        )
    elif not table:
        characteristics_ctx.report(found="an empty table", expected="at least one entry")
    else:
        for code, entry in table.items():
            label, characteristic_class = _parse_characteristic_entry(
                entry, characteristics_ctx.at(code)
            )
            if label is not None and characteristic_class is not None:
                names[code] = label
                classes[code] = characteristic_class

    bands = _parse_bands(data.get("modifier-dms"), ctx.at("modifier-dms"))

    pseudo_hex = _parse_pseudo_hex(data.get("pseudo-hex"), ctx)

    if ctx.failed:
        return None
    pseudo_hex_minimum, pseudo_hex_symbols = pseudo_hex
    return CharacteristicRegistry(
        names=MappingProxyType(names),
        classes=MappingProxyType(classes),
        bands=bands,
        pseudo_hex_minimum=pseudo_hex_minimum,
        pseudo_hex=pseudo_hex_symbols,
    )


def _acyclic_problems(skills: Mapping[str, tuple[str, ...]], ctx: ParseContext) -> None:
    """The specialty graph must be acyclic (FR-012a): generation-time
    resolution (`_resolve_specialty`, `src/cetools/generator.py`) follows a
    specialty into another entry and continues until it finds one with none,
    and a cycle would make that loop never terminate.

    A specialty that names no entry in `skills` is terminal and outside this
    graph (D5): every specialty in the packaged registry happens to also be
    an entry, but nothing requires it.
    """
    state: dict[str, int] = {}  # 1: on the current path, 2: fully explored

    def visit(name: str, path: list[str]) -> None:
        state[name] = 1
        for specialty in skills.get(name, ()):
            if specialty not in skills:
                continue
            if state.get(specialty) == 1:
                cycle = path[path.index(specialty) :] + [specialty]
                ctx.at("skills", name).report(
                    found=specialty,
                    expected=f"an acyclic specialty graph: {' -> '.join(cycle)} is a cycle",
                )
            elif specialty not in state:
                visit(specialty, path + [specialty])
        state[name] = 2

    for name in sorted(skills):
        if name not in state:
            visit(name, [name])


def parse_skills(data: Mapping[str, object], ctx: ParseContext) -> SkillRegistry | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"skills"})

    skills_ctx = ctx.at("skills")
    table = data.get("skills")
    if not isinstance(table, dict):
        skills_ctx.report(
            found="missing" if table is None else type_name(table),
            expected="a [skills] table with at least one entry",
        )
        return None

    if not table:
        skills_ctx.report(found="an empty table", expected="at least one entry")
        return None

    skills: dict[str, tuple[str, ...]] = {}
    for name, specialties in table.items():
        # A key carrying a specialty group can never be referenced: every
        # career entry is split into a base name and a specialty before it is
        # resolved, so `"Gun Combat (Slug Rifle)" = []` is an entry nothing
        # can reach, and a career writing that very text resolves
        # `UNRECOGNIZED_SKILL` against the base name instead. Specialties are
        # declared in the array (FR-011); a name that also spells one is a
        # mistake the author needs told about rather than a dead entry
        # (FR-006, FR-013, contracts/notation.md).
        if "(" in name or ")" in name:
            skills_ctx.at(name).report(
                found=name,
                expected=(
                    "a skill name with no parentheses: a specialty is declared in this "
                    "skill's array, never spelled into its name"
                ),
            )
            continue
        # `skills.py:429`: an empty array validates clean today (a
        # non-cascade skill), unlike every other array field in this
        # schema; the disagreement is inventory.md I-4.
        raw_specialties = skills_ctx.require_list(
            table, name, expected="an array of strings", allow_empty=True
        )
        if raw_specialties is None:
            continue
        # Every offending element, not the first: reporting one made this the
        # one field in the feature where fixing the reported mistake revealed
        # the next on the following run, which FR-021's collect-everything and
        # SC-003's "the number of runs needed to find every problem in a file
        # is always one" forbid. Both sibling parsers below already loop.
        bad = False
        for index, specialty in enumerate(raw_specialties):
            if not isinstance(specialty, str):
                skills_ctx.at(name, index).report(found=type_name(specialty), expected="a string")
                bad = True
        if bad:
            continue
        skills[name] = tuple(raw_specialties)

    if ctx.failed:
        return None

    _acyclic_problems(skills, ctx)
    if ctx.failed:
        return None
    return SkillRegistry(skills=MappingProxyType(skills))


def parse_benefits(data: Mapping[str, object], ctx: ParseContext) -> BenefitRegistry | None:
    ctx.unrecognized_keys(data, HEADER_KEYS | {"benefits"})

    items = ctx.require_list(
        data,
        "benefits",
        expected="an array of strings with at least one entry",
        expected_empty="at least one entry",
    )
    if items is None:
        return None

    names: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str):
            ctx.at("benefits", index).report(found=type_name(item), expected="a string")
            continue
        names.append(item)

    if ctx.failed:
        return None
    return BenefitRegistry(items=tuple(names))
