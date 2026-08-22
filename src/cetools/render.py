import json
from functools import singledispatch

from cetools.character import Character, CharacterBatch
from cetools.dice import ThrowResult
from cetools.errors import CetoolsError, ValidationProblem
from cetools.provenance import Provenance
from cetools.rules import ValidationReport
from cetools.tasks import CheckResult

_RULES_LABEL_WIDTH = len("Rules:") + 1


def _provenance_lines(
    provenance: Provenance, label_width: int = _RULES_LABEL_WIDTH, indent: int = 2
) -> list[str]:
    """The shared `Rules:` block, appended after a result's `Seed:` line and
    after a `validate` report's summary (contracts/cli.md).

    `label_width` lets a caller line the `Rules:` label up with sibling
    summary labels of different lengths (`Files:`, `Problems:`); it defaults
    to `Rules:`'s own width, which is what `CheckResult` needs since `Rules:`
    is its widest label. `indent` is the left margin of the `Rules:` line
    itself, in spaces; the per-file lines beneath it are always two spaces
    further in, which is what keeps them visually nested under it whatever
    `indent` is. It defaults to the two spaces every existing caller relies
    on, and the npc command writes the block to stderr with no surrounding
    result, so it passes `indent=0`. The file column is padded to the longest
    name present across both lists — a composition key for a file that took
    effect, a path within the override for an ignored one — and the
    disposition column to the longest disposition present (`"ignored"` counts
    as one), matching the padding rule the `Modifiers` block already uses.
    Files that took effect are listed first, already sorted by name, then
    ignored files, already sorted by name. An ignored file's line ends at the
    disposition: it carries no fingerprint to pad toward.
    """
    outer = " " * indent
    inner = " " * (indent + 2)
    source = "packaged" if provenance.is_packaged else "overridden"
    lines = [f"{outer}{'Rules:'.ljust(label_width)}{source} (cetools {provenance.version})"]

    names = [fp.file for fp in provenance.files] + list(provenance.ignored)
    if not names:
        return lines

    basename_width = max(len(name) for name in names)
    dispositions = [fp.disposition.value for fp in provenance.files]
    if provenance.ignored:
        dispositions.append("ignored")
    disposition_width = max(len(d) for d in dispositions)

    for fp in provenance.files:
        lines.append(
            f"{inner}{fp.file.ljust(basename_width)}   "
            f"{fp.disposition.value.ljust(disposition_width)}  {fp.fingerprint}"
        )
    for name in provenance.ignored:
        lines.append(f"{inner}{name.ljust(basename_width)}   ignored")
    return lines


def _provenance_dict(provenance: Provenance) -> dict:
    return {
        "source": "packaged" if provenance.is_packaged else "overridden",
        "version": provenance.version,
        "files": [
            {"file": fp.file, "disposition": fp.disposition.value, "fingerprint": fp.fingerprint}
            for fp in provenance.files
        ],
        "ignored": list(provenance.ignored),
    }


def _problem_line(problem: ValidationProblem) -> str:
    """One `validate` report line: `FILE:LOCATION: found F; expected E`,
    dropping `:LOCATION` for a problem about the file as a whole
    (contracts/cli.md). Also what `cli.py` prints to stderr when a `check`
    load fails, so the two surfaces never disagree on the form.

    Package-internal, and named as such in this feature's
    `contracts/library-api.md` because it crosses a module boundary: a seam no
    contract records is one a later change can break without noticing.
    """
    location = f":{problem.location}" if problem.location else ""
    return f"{problem.file}{location}: found {problem.found}; expected {problem.expected}"


@singledispatch
def as_text(result, *, full: bool = False) -> str:
    """Render a result (`ThrowResult` or `CheckResult`) as human-readable text.

    Follows the rendering rules pinned by the golden files in
    `tests/golden/`: labels padded to the longest present, values signed,
    a trailing newline, and no `Modifier:`/sum noise when there is no
    modifier to show.

    `full=True` asks for a fuller rendering. Every registration below has no
    fuller form and raises `CetoolsError` when it is passed, on the same
    reasoning this fallback already applies one level up: a rendering that
    silently gave less than was asked for is worse than one that says it
    cannot (003-npc-generator plan.md).

    An unregistered type raises `CetoolsError`. Unlike an empty modifier
    list, which renders because it is a check with nothing applied rather
    than a condition the library detects, this fallback exists precisely to
    detect the miss, and 001-dice-task-engine FR-029 admits no exception. The
    base class is raised rather than a fourth leaf: no existing leaf describes a
    dispatch miss, and a new public error type for a path no supported caller
    reaches is the speculative surface Principle VI rejects. What that
    requirement buys a caller — one `except CetoolsError` catches everything —
    holds either way.
    """
    raise CetoolsError(f"no as_text rendering registered for {type(result).__name__}")


def _reject_full(result, full: bool) -> None:
    if full:
        raise CetoolsError(f"{type(result).__name__} has no fuller as_text rendering")


@as_text.register
def _(result: ThrowResult, *, full: bool = False) -> str:
    _reject_full(result, full)
    labels = ["Dice:"]
    if result.modifier != 0:
        labels.append("Modifier:")
    labels.append("Seed:")
    width = max(len(label) for label in labels) + 1

    dice_value = ", ".join(str(face) for face in result.faces)
    if result.modifier != 0:
        dice_value += f" (sum {sum(result.faces)})"

    lines = [f"{result.notation} = {result.total}"]
    lines.append(f"  {'Dice:'.ljust(width)}{dice_value}")
    if result.modifier != 0:
        sign = "+" if result.modifier > 0 else ""
        lines.append(f"  {'Modifier:'.ljust(width)}{sign}{result.modifier}")
    lines.append(f"  {'Seed:'.ljust(width)}{result.seed}")
    return "\n".join(lines) + "\n"


@as_text.register
def _(result: CheckResult, *, full: bool = False) -> str:
    _reject_full(result, full)
    outer_width = max(len(label) for label in ("Dice:", "Total:", "Seed:", "Rules:")) + 1
    # `check` always applies at least a difficulty and a skill-or-unskilled row,
    # so the CLI never sees an empty list. `CheckResult` is public, though, and a
    # heading with no rows under it is a check with nothing applied rather than a
    # malformed one, so it renders rather than raising.
    mod_width = max((len(modifier.label) for modifier in result.modifiers), default=0)

    dice_value = ", ".join(str(face) for face in result.faces) + f" (sum {result.dice_total})"

    lines = [f"Check: {'SUCCESS' if result.success else 'FAILURE'}"]
    lines.append(f"  {'Dice:'.ljust(outer_width)}{dice_value}")
    lines.append("  Modifiers:")
    for modifier in result.modifiers:
        sign = "+" if modifier.value >= 0 else "-"
        lines.append(f"    {modifier.label.ljust(mod_width)} {sign}{abs(modifier.value)}")
    lines.append(f"  {'Total:'.ljust(outer_width)}{result.total} vs target {result.target}")
    lines.append(f"  {'Seed:'.ljust(outer_width)}{result.seed}")
    lines.extend(_provenance_lines(result.provenance))
    return "\n".join(lines) + "\n"


@as_text.register
def _(result: ValidationReport, *, full: bool = False) -> str:
    _reject_full(result, full)
    problem_lines = [_problem_line(p) for p in result.problems]

    if result.problems:
        labels = ("Files:", "Problems:", "Rules:")
        width = max(len(label) for label in labels) + 1
        lines = [*problem_lines, "", "Rules data is invalid."]
        lines.append(f"  {'Files:'.ljust(width)}{result.file_count}")
        lines.append(f"  {'Problems:'.ljust(width)}{len(result.problems)}")
    else:
        labels = ("Files:", "Rules:")
        width = max(len(label) for label in labels) + 1
        lines = ["Rules data is valid.", f"  {'Files:'.ljust(width)}{result.file_count}"]

    lines.extend(_provenance_lines(result.provenance, label_width=width))
    return "\n".join(lines) + "\n"


def _skill_label(skill) -> str:
    if skill.specialty is None:
        return skill.name
    return f"{skill.name} ({skill.specialty})"


def _sort_key(text: str) -> tuple[str, str]:
    """`(casefold, codepoint)`, alphabetical and locale-independent (FR-046,
    SC-012, research R8). Never `locale.strxfrm`.
    """
    return text.casefold(), text


def _characteristic_profile(character: Character) -> str:
    """One pseudo-hex symbol per characteristic, in `character.characteristics`'
    own order, which is already the characteristics registry's file order
    (data-model.md) — the generator built that mapping by iterating the
    registry, so no separate registry lookup is needed for order.

    The *symbols themselves* do need the registry, which `as_text` has no
    parameter to receive (contracts/library-api.md pins its signature to
    `(result, *, full=False)`). This loads the packaged rules for that lookup
    alone, the same fallback `tasks.check` uses for its own `rules=None`. A
    character generated under an overridden pseudo-hex table renders against
    the *packaged* one here, which is a known gap `--rules-data` characters
    may hit; there is no override-carrying seam in this contract to close it
    through.
    """
    from cetools.rules import load_rules

    registry = load_rules().characteristics
    return "".join(registry.symbol(score) for score in character.characteristics.values())


def _careers_line(character: Character) -> str:
    parts = []
    for service in character.careers:
        unit = "term" if service.terms == 1 else "terms"
        parts.append(f"{service.career} ({service.terms} {unit})")
    return ", ".join(parts)


def _skills_line(character: Character) -> str:
    rendered = [f"{_skill_label(skill)}-{skill.level}" for skill in character.skills]
    rendered.sort(key=_sort_key)
    return ", ".join(rendered)


def _benefits_line(character: Character) -> str | None:
    if not character.benefits:
        return None
    counts: dict[str, int] = {}
    for name in character.benefits:
        counts[name] = counts.get(name, 0) + 1
    names = sorted(counts, key=_sort_key)
    return ", ".join(name if counts[name] == 1 else f"{name} (x{counts[name]})" for name in names)


@as_text.register
def _(character: Character, *, full: bool = False) -> str:
    """The Universal Character Format (contracts/cli.md): three fixed lines
    and a fourth omitted when the character holds no benefit items. Tab
    separated, exactly one tab between fields.

    Carries **no** trailing newline of its own — unlike every other `as_text`
    registration — because a batch joins sheets on a blank line with nothing
    before or after (FR-048a), and the CLI is what appends the one final
    newline a redirected sheet ends with (contracts/cli.md T106: the command's
    stdout is `as_text(character)` plus that one trailing newline).
    """
    _reject_full(character, full)
    name_field = f"{character.title} {character.name}" if character.title else character.name
    line1 = f"{name_field}\t{_characteristic_profile(character)}\tAge {character.age}"
    line2 = f"{_careers_line(character)}\tCr{character.funds:,}"
    line3 = _skills_line(character)
    lines = [line1, line2, line3]
    benefits = _benefits_line(character)
    if benefits is not None:
        lines.append(benefits)
    return "\n".join(lines)


@as_text.register
def _(batch: CharacterBatch, *, full: bool = False) -> str:
    """Sheets separated by exactly one blank line and nothing else (FR-048a):
    a batch of one is byte-identical to the single character of that seed.
    """
    _reject_full(batch, full)
    return "\n\n".join(as_text(character) for character in batch.characters)


@singledispatch
def as_dict(result) -> dict:
    """Render a result (`ThrowResult` or `CheckResult`) as the committed JSON shape.

    `seed` is emitted as a decimal string, since 64-bit seeds exceed
    2^53 and would be silently corrupted by a JavaScript consumer; every
    other numeric field is a JSON number.

    An unregistered type raises `CetoolsError`, for the reasons recorded on
    `as_text`. `as_json` reaches this fallback rather than carrying its own,
    since it renders through `as_dict`.
    """
    raise CetoolsError(f"no as_dict rendering registered for {type(result).__name__}")


@as_dict.register
def _(result: ThrowResult) -> dict:
    return {
        "kind": "roll",
        "notation": result.notation,
        "faces": list(result.faces),
        "modifier": result.modifier,
        "total": result.total,
        "seed": str(result.seed),
    }


@as_dict.register
def _(result: CheckResult) -> dict:
    return {
        "kind": "check",
        "faces": list(result.faces),
        "dice_total": result.dice_total,
        "modifiers": [
            {"label": modifier.label, "value": modifier.value} for modifier in result.modifiers
        ],
        "total": result.total,
        "target": result.target,
        "success": result.success,
        "seed": str(result.seed),
        "provenance": _provenance_dict(result.provenance),
    }


@as_dict.register
def _(result: ValidationReport) -> dict:
    return {
        "kind": "validation",
        "valid": result.valid,
        "file_count": result.file_count,
        "provenance": _provenance_dict(result.provenance),
        "problems": [
            {
                "file": p.file,
                "location": p.location,
                "found": p.found,
                "expected": p.expected,
            }
            for p in result.problems
        ],
    }


def as_json(result) -> str:
    """Render `as_dict(result)` as indented JSON with a trailing newline."""
    return json.dumps(as_dict(result), indent=2, ensure_ascii=False) + "\n"
