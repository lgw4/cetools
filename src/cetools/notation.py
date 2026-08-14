"""The compact table notation: one entry that mixes kinds of thing in one cell.

`parse_entry` does no registry lookup (see `registries.py` and `careers.py`
for that); it only decides which of the four grammar forms an entry text is,
and whether that form is admissible in the caller's `EntryContext`. See
contracts/notation.md for the grammar and the malformed-entry table this
module's behavior is pinned to.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto


class EntryContext(Enum):
    """Which forms an entry position admits, and which registry validates a
    name at that position (contracts/notation.md).
    """

    SKILL_TABLE = auto()
    BENEFIT_TABLE = auto()
    GATE = auto()


@dataclass(frozen=True, slots=True)
class SkillReference:
    """A skill name with an optional specialty.

    `specialty is None` for a skill that has specialties means a choice is
    owed, and stays distinguishable from a specialty that was given
    (FR-008); this type carries no knowledge of which skills owe one.
    """

    name: str
    specialty: str | None = None


@dataclass(frozen=True, slots=True)
class CharacteristicCheck:
    """A table gate: `INT 4+` means the throw must equal or exceed 4."""

    characteristic: str
    target: int


@dataclass(frozen=True, slots=True)
class CharacteristicAdjustment:
    """A signed change to a characteristic: `STR +1` or `SOC -1`."""

    characteristic: str
    amount: int


@dataclass(frozen=True, slots=True)
class SkillGrant:
    """A skill granted at an explicit level: `Pilot 2` or `Blade (Cutlass) 1`."""

    skill: SkillReference
    level: int


@dataclass(frozen=True, slots=True)
class BenefitItem:
    """The bare form in a benefits table: a mustering-out benefit's name."""

    name: str


type Entry = (
    SkillReference | CharacteristicCheck | CharacteristicAdjustment | SkillGrant | BenefitItem
)


@dataclass(frozen=True, slots=True)
class NotationProblem:
    """An entry's text does not parse, or parses to a form its context does
    not admit. Carries no file or location; the caller (which knows the
    field it read the text from) fills those into a `ValidationProblem`.
    """

    found: str
    expected: str


_ADMISSIBLE_KINDS: dict[EntryContext, frozenset[str]] = {
    EntryContext.SKILL_TABLE: frozenset({"adjustment", "grant", "bare"}),
    EntryContext.BENEFIT_TABLE: frozenset({"adjustment", "bare"}),
    EntryContext.GATE: frozenset({"check"}),
}

_ADMISSIBLE_FORMS: dict[EntryContext, str] = {
    EntryContext.SKILL_TABLE: (
        "a characteristic adjustment, a skill grant, or a bare skill reference"
    ),
    EntryContext.BENEFIT_TABLE: "a characteristic adjustment or a bare benefit item",
    EntryContext.GATE: "a characteristic check",
}

_TRAILING_TOKEN = re.compile(r"\s+(\S+)$")
_CHECK_TOKEN = re.compile(r"^(\d+)\+$")
_ADJUSTMENT_TOKEN = re.compile(r"^([+-])(\d+)$")
_GRANT_TOKEN = re.compile(r"^(\d+)$")
_BARE_SIGN_TOKEN = re.compile(r"^[+-]$")
_SPECIALTY = re.compile(r"^(?P<base>[^()]*)\((?P<inner>[^()]*)\)$")


def _parse_name(text: str) -> tuple[str, str | None] | NotationProblem:
    """Split `text` into a base name and an optional parenthesized specialty."""
    text = text.strip()
    open_count = text.count("(")
    close_count = text.count(")")
    if open_count != close_count:
        return NotationProblem(found=text, expected="a name with balanced parentheses")
    if open_count > 1:
        return NotationProblem(found=text, expected="at most one specialty group")
    if open_count == 0:
        return text, None

    match = _SPECIALTY.match(text)
    if match is None:
        return NotationProblem(found=text, expected="a name followed by (specialty)")
    base = match.group("base").strip()
    inner = match.group("inner").strip()
    if not inner:
        return NotationProblem(found=text, expected="a non-empty specialty")
    return base, inner


def parse_entry(text: str, context: EntryContext) -> Entry | NotationProblem:
    """Parse one table cell's text into the entry it names, or a problem.

    Matches by anchoring on the trailing whitespace-delimited token, in the
    fixed order check, adjustment, grant, bare (contracts/notation.md,
    research R9). A token that contains a digit but matches none of the
    three suffixed forms is reported as malformed rather than folded into
    the name, distinguishing a mistaken suffix from a name that merely ends
    in ordinary text.
    """
    stripped = text.strip()
    if not stripped:
        return NotationProblem(found=text, expected="a non-empty entry")

    trailing = _TRAILING_TOKEN.search(stripped)
    name_part = stripped[: trailing.start()] if trailing else ""
    token = trailing.group(1) if trailing else stripped

    kind: str
    target = amount = level = None
    if (m := _CHECK_TOKEN.match(token)) is not None:
        kind, target = "check", int(m.group(1))
    elif (m := _ADJUSTMENT_TOKEN.match(token)) is not None:
        kind, amount = "adjustment", int(m.group(1) + m.group(2))
    elif (m := _GRANT_TOKEN.match(token)) is not None:
        kind, level = "grant", int(m.group(1))
    elif trailing is not None and _BARE_SIGN_TOKEN.match(token):
        return NotationProblem(found=stripped, expected="a number after the sign")
    elif trailing is not None and any(ch.isdigit() for ch in token):
        return NotationProblem(found=stripped, expected="one of the four notation forms")
    else:
        kind, name_part = "bare", stripped

    if kind not in _ADMISSIBLE_KINDS[context]:
        return NotationProblem(found=stripped, expected=_ADMISSIBLE_FORMS[context])

    parsed_name = _parse_name(name_part)
    if isinstance(parsed_name, NotationProblem):
        return parsed_name
    base, specialty = parsed_name
    if not base:
        return NotationProblem(found=stripped, expected="a non-empty name")

    if kind == "check":
        return CharacteristicCheck(characteristic=base, target=target)
    if kind == "adjustment":
        return CharacteristicAdjustment(characteristic=base, amount=amount)
    if kind == "grant":
        return SkillGrant(skill=SkillReference(name=base, specialty=specialty), level=level)
    # kind == "bare"
    if context is EntryContext.BENEFIT_TABLE:
        return BenefitItem(name=f"{base} ({specialty})" if specialty else base)
    return SkillReference(name=base, specialty=specialty)
