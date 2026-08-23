import json
from functools import singledispatch

from cetools.character import (
    CareerService,
    Character,
    CharacterBatch,
    CharacterSkill,
    HistoryStep,
    StepEffect,
    StepThrow,
)
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
    """One pseudo-hex symbol per characteristic, read from
    `character.characteristic_symbols` (T159). `as_text` has no parameter to
    receive the rules that generated `character` (contracts/library-api.md
    pins its signature to `(result, *, full=False)`), so the symbols travel
    on the character itself rather than being recomputed here against
    whatever rules happen to be packaged — the seam a `--rules-data` override
    needs to reach this rendering at all.
    """
    return "".join(character.characteristic_symbols)


def _careers_line(character: Character) -> str:
    parts = []
    for service in character.careers:
        unit = "term" if service.terms == 1 else "terms"
        parts.append(f"{service.career} ({service.terms} {unit})")
    return ", ".join(parts)


def _skills_line(character: Character) -> str:
    # Sorted by the label alone (contracts/cli.md: "over the rendered
    # name-and-specialty"), not by the label-and-level string: the level
    # suffix must never perturb the order `as_dict`'s `skills` agrees with
    # (FR-046, T154).
    ordered = sorted(character.skills, key=lambda skill: _sort_key(_skill_label(skill)))
    return ", ".join(f"{_skill_label(skill)}-{skill.level}" for skill in ordered)


def _benefits_line(character: Character) -> str | None:
    if not character.benefits:
        return None
    counts: dict[str, int] = {}
    for name in character.benefits:
        counts[name] = counts.get(name, 0) + 1
    names = sorted(counts, key=_sort_key)
    return ", ".join(name if counts[name] == 1 else f"{name} (x{counts[name]})" for name in names)


def _universal_character_format(character: Character) -> str:
    """The Universal Character Format (contracts/cli.md): three fixed lines
    and a fourth omitted when the character holds no benefit items. Tab
    separated, exactly one tab between fields.
    """
    name_field = f"{character.title} {character.name}" if character.title else character.name
    line1 = f"{name_field}\t{_characteristic_profile(character)}\tAge {character.age}"
    line2 = f"{_careers_line(character)}\tCr{character.funds:,}"
    line3 = _skills_line(character)
    lines = [line1, line2, line3]
    benefits = _benefits_line(character)
    if benefits is not None:
        lines.append(benefits)
    return "\n".join(lines)


def _throw_text(throw: StepThrow) -> str:
    """One throw, composed from its own parts (FR-030a): the faces, each
    modifier itemized, the total when it differs from the raw sum, and the
    target and outcome for a throw that has one to beat. A table-reading
    throw (`target == 0`, `success == True`) omits that last part; the row
    it read is in the owning step's `selected`.
    """
    text = ", ".join(str(face) for face in throw.faces)
    raw_sum = sum(throw.faces)
    if len(throw.faces) > 1:
        text += f" (sum {raw_sum})"
    for modifier in throw.modifiers:
        sign = "+" if modifier.value >= 0 else "-"
        text += f" {modifier.label} {sign}{abs(modifier.value)}"
    if throw.total != raw_sum:
        text += f" = {throw.total}"
    if throw.target != 0 or not throw.success:
        text += f" vs {throw.target}  {'SUCCESS' if throw.success else 'FAILURE'}"
    return text


def _effect_text(effect: StepEffect) -> str:
    """One consequence, composed from its own `kind`, `subject`, and
    `amount` (FR-030a) rather than read from a stored prose field.
    """
    match effect.kind:
        case "characteristic" | "skill":
            return f"{effect.subject} {effect.amount}"
        case "characteristic-called-for":
            return f"{effect.subject} {effect.amount} (called for)"
        case "credits":
            return f"Cr{effect.amount:,}"
        case "debt":
            return f"Cr{effect.amount:,} debt"
        case "pension":
            return f"Cr{effect.amount:,} pension"
        case "benefit":
            return effect.subject if effect.amount == 0 else f"{effect.subject} {effect.amount}"
        case _:
            return effect.subject


def _step_message(step: HistoryStep) -> str:
    """A history line's message, composed from the step's throw, its
    `selected`, and its effects — never from a stored line of prose
    (FR-030a).
    """
    parts = []
    if step.throw is not None:
        parts.append(_throw_text(step.throw))
    if step.selected:
        parts.append(step.selected)
    if step.effects:
        parts.append(", ".join(_effect_text(effect) for effect in step.effects))
    return "  ".join(parts)


def _history_lines(history: tuple[HistoryStep, ...]) -> list[str]:
    """The `History:` block (FR-049): kind, career, and term columns padded
    to the longest value present, matching the padding rule the `Modifiers`
    block already uses, followed by the composed message.
    """
    kind_width = max(len(step.kind) for step in history)
    career_width = max(len(step.career) for step in history)
    term_texts = [f"t{step.term}" if step.term else "" for step in history]
    term_width = max(len(text) for text in term_texts)

    lines = ["  History:"]
    for step, term_text in zip(history, term_texts):
        line = (
            f"    {step.kind.ljust(kind_width)}  "
            f"{step.career.ljust(career_width)}  "
            f"{term_text.ljust(term_width)}  {_step_message(step)}"
        )
        lines.append(line.rstrip())
    return lines


def _debt_pension_lines(character: Character) -> list[str]:
    """`Debt:` and `Pension:` (FR-049), reading `none` rather than a zero
    amount so a reader never has to tell a zero from an absence.
    """
    width = max(len("Debt:"), len("Pension:")) + 1
    debt_text = "none" if character.debt == 0 else f"Cr{character.debt:,}"
    pension_text = "none" if character.pension == 0 else f"Cr{character.pension:,}"
    return [
        f"  {'Debt:'.ljust(width)}{debt_text}",
        f"  {'Pension:'.ljust(width)}{pension_text}",
    ]


@as_text.register
def _(character: Character, *, full: bool = False) -> str:
    """The Universal Character Format, or, with `full=True`, that format
    plus a blank line, the debt, the pension, and the generation history
    (contracts/cli.md).

    Carries **no** trailing newline of its own — unlike every other `as_text`
    registration — because a batch joins sheets on a blank line with nothing
    before or after (FR-048a), and the CLI is what appends the one final
    newline a redirected sheet ends with (contracts/cli.md T106: the command's
    stdout is `as_text(character)` plus that one trailing newline).
    """
    base = _universal_character_format(character)
    if not full:
        return base
    lines = [base, "", *_debt_pension_lines(character), "", *_history_lines(character.history)]
    return "\n".join(lines)


@as_text.register
def _(batch: CharacterBatch, *, full: bool = False) -> str:
    """Sheets separated by exactly one blank line and nothing else (FR-048a):
    a batch of one is byte-identical to the single character of that seed.
    """
    return "\n\n".join(as_text(character, full=full) for character in batch.characters)


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


def _skill_dict(skill: CharacterSkill) -> dict:
    return {"name": skill.name, "specialty": skill.specialty, "level": skill.level}


def _career_service_dict(service: CareerService) -> dict:
    return {
        "career": service.career,
        "terms": service.terms,
        "ladder": service.ladder,
        "rank": service.rank,
        "title": service.title,
        "commissioned": service.commissioned,
        "entered_by": service.entered_by,
        "ended": service.ended,
        "benefit_rolls": service.benefit_rolls,
    }


def _step_throw_dict(throw: StepThrow | None) -> dict | None:
    if throw is None:
        return None
    return {
        "faces": list(throw.faces),
        "modifiers": [{"label": m.label, "value": m.value} for m in throw.modifiers],
        "total": throw.total,
        "target": throw.target,
        "success": throw.success,
    }


def _step_effect_dict(effect: StepEffect) -> dict:
    return {"kind": effect.kind, "subject": effect.subject, "amount": effect.amount}


def _history_step_dict(step: HistoryStep) -> dict:
    return {
        "kind": step.kind,
        "career": step.career,
        "term": step.term,
        "throw": _step_throw_dict(step.throw),
        "selected": step.selected,
        "effects": [_step_effect_dict(effect) for effect in step.effects],
    }


@as_dict.register
def _(character: Character) -> dict:
    # `skills` sorts by the same key the sheet sorts by, so the two agree
    # (contracts/json-output.md), even though `Character.skills` itself is
    # held in acquisition order (data-model.md).
    sorted_skills = sorted(character.skills, key=lambda skill: _sort_key(_skill_label(skill)))
    return {
        "seed": str(character.seed),
        "name": character.name,
        "given_name": character.given_name,
        "surname": character.surname,
        "surname_region": character.surname_region,
        "title": character.title,
        "characteristics": dict(character.characteristics),
        "skills": [_skill_dict(skill) for skill in sorted_skills],
        "careers": [_career_service_dict(service) for service in character.careers],
        "age": character.age,
        "funds": character.funds,
        "debt": character.debt,
        "pension": character.pension,
        "benefits": list(character.benefits),
        "history": [_history_step_dict(step) for step in character.history],
    }


@as_dict.register
def _(batch: CharacterBatch) -> dict:
    return {
        "kind": "npc",
        "seed": str(batch.seed),
        "provenance": _provenance_dict(batch.provenance),
        "characters": [as_dict(character) for character in batch.characters],
    }


def as_json(result) -> str:
    """Render `as_dict(result)` as indented JSON with a trailing newline."""
    return json.dumps(as_dict(result), indent=2, ensure_ascii=False) + "\n"
