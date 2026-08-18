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


def _malformed(text: str, context: EntryContext, detail: str) -> NotationProblem:
    """A malformed entry, reported the way FR-009 asks for it: the entry as
    written, and the forms acceptable in the position it sits in.

    The forms come first because they are what FR-009 promises and FR-009a
    exists to supply; a context-free "one of the four notation forms" was not
    merely incomplete but false, since a gate admits exactly one form and a
    mustering-out benefits entry exactly two. `detail` says which rule the
    entry broke, which the admissible forms alone do not tell an author who
    wrote `Pilot -`.

    `text` is the entry as the author wrote it, not the stripped form: an
    author shown `Pilot -` for a cell holding `  Pilot -  ` is shown an entry
    that is not in their file.
    """
    return NotationProblem(found=text, expected=f"{_ADMISSIBLE_FORMS[context]}; {detail}")


def _parse_name(name: str) -> tuple[str, str | None] | str:
    """Split `name` into a base name and an optional parenthesized specialty,
    or return the detail of what is wrong with it.

    Returns a detail string rather than a `NotationProblem` because only the
    caller knows the context whose admissible forms belong in the report and
    the entry text as written; this sees the name alone.

    The whitespace the grammar puts before a specialty group is required, not
    decorative: `name := text [ WS "(" text ")" ]` with `WS` one or more
    spaces. Splitting on the parenthesis alone made `Blade(Cutlass)` and
    `Blade (Cutlass)` the same reference, which is the quiet widening FR-013
    forbids and which T087 already refused for a benefit item on exactly this
    reasoning — inserting or collapsing a space widens the notation the way
    case folding does. A benefit item carries its name as written, so
    `Weapon(Blade)` simply fails to match the registry; a skill reference is
    split into two fields, so nothing but this check keeps the space-free form
    from resolving. Rejecting it settles the two the same way.
    """
    name = name.strip()
    open_count = name.count("(")
    close_count = name.count(")")
    if open_count != close_count:
        return "a name with balanced parentheses"
    if open_count > 1:
        return "at most one specialty group"
    if open_count == 0:
        return name, None

    match = _SPECIALTY.match(name)
    if match is None:
        return "a name followed by (specialty)"
    base = match.group("base")
    if base and not base[-1].isspace():
        return "a space before the specialty group"
    base = base.strip()
    inner = match.group("inner").strip()
    if not inner:
        return "a non-empty specialty"
    return base, inner


def parse_entry(text: str, context: EntryContext) -> Entry | NotationProblem:
    """Parse one table cell's text into the entry it names, or a problem.

    Matches by anchoring on the trailing whitespace-delimited token, in the
    fixed order check, adjustment, grant, bare (contracts/notation.md,
    research R9). A token that contains a digit but matches none of the
    three suffixed forms is reported as malformed rather than folded into
    the name, distinguishing a mistaken suffix from a name that merely ends
    in ordinary text.

    The tail is looked for after a specialty's closing parenthesis, because
    the grammar reserves the suffix position to text outside the specialty
    group: without that, the `)` of `Blade (Mark 2)` was caught by the digit
    heuristic and the entry rejected, while the very same specialty in the
    grant form `Blade (Mark 2) 1` parsed. Only the suffixed forms take the
    name from before the tail; the bare form always takes the whole entry, so
    text beyond a specialty group still reaches `_parse_name` and is still
    reported rather than dropped.
    """
    stripped = text.strip()
    if not stripped:
        return _malformed(text, context, "a non-empty entry")

    after_specialty = stripped.rfind(")") + 1
    trailing = _TRAILING_TOKEN.search(stripped, after_specialty)
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
        return _malformed(text, context, "a number after the sign")
    elif trailing is not None and any(ch.isdigit() for ch in token):
        return _malformed(
            text, context, "a trailing number reads as a level, an amount, or a target"
        )
    else:
        kind, name_part = "bare", stripped

    if kind not in _ADMISSIBLE_KINDS[context]:
        return NotationProblem(found=text, expected=_ADMISSIBLE_FORMS[context])

    parsed_name = _parse_name(name_part)
    if isinstance(parsed_name, str):
        return _malformed(text, context, parsed_name)
    base, specialty = parsed_name
    if not base:
        return _malformed(text, context, "a non-empty name")

    if kind in ("check", "adjustment"):
        # A specialty belongs to a skill or a benefit item. Building the entry
        # from the base name alone would drop text the author wrote with no
        # effect and no diagnostic, and would evade FR-013's exact registry
        # match, since the name as written is `INT (Foo)` and the
        # characteristics registry holds only `INT`.
        if specialty is not None:
            return _malformed(text, context, "a characteristic carries no specialty")
        if kind == "check":
            return CharacteristicCheck(characteristic=base, target=target)
        return CharacteristicAdjustment(characteristic=base, amount=amount)
    if kind == "grant":
        return SkillGrant(skill=SkillReference(name=base, specialty=specialty), level=level)
    # kind == "bare". A benefit item has one field, so its name is carried as
    # written rather than reassembled from the split: rebuilding it as
    # `f"{base} ({specialty})"` made `Weapon(Blade)` and `Weapon  (Blade)`
    # resolve to the same registry entry, which is the quiet widening FR-013
    # forbids by requiring every name to be matched exactly. A skill keeps
    # base and specialty in separate fields, so nothing is reassembled there.
    if context is EntryContext.BENEFIT_TABLE:
        return BenefitItem(name=stripped)
    return SkillReference(name=base, specialty=specialty)
