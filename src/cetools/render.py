import json
from functools import singledispatch

from cetools.dice import ThrowResult
from cetools.errors import CetoolsError, ValidationProblem
from cetools.provenance import Provenance
from cetools.rules import ValidationReport
from cetools.tasks import CheckResult

_RULES_LABEL_WIDTH = len("Rules:") + 1


def _provenance_lines(provenance: Provenance, label_width: int = _RULES_LABEL_WIDTH) -> list[str]:
    """The shared `Rules:` block, appended after a result's `Seed:` line and
    after a `validate` report's summary (contracts/cli.md).

    `label_width` lets a caller line the `Rules:` label up with sibling
    summary labels of different lengths (`Files:`, `Problems:`); it defaults
    to `Rules:`'s own width, which is what `CheckResult` needs since `Rules:`
    is its widest label. The file column is padded to the longest basename
    present and the disposition column to the longest disposition present
    (`"ignored"` counts as one), matching the padding rule the `Modifiers`
    block already uses. Files that took effect are listed first, already
    sorted by name, then ignored files, already sorted by name. An ignored
    file's line ends at the disposition: it carries no fingerprint to pad
    toward.
    """
    source = "packaged" if provenance.is_packaged else "overridden"
    lines = [f"  {'Rules:'.ljust(label_width)}{source} (cetools {provenance.version})"]

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
            f"    {fp.file.ljust(basename_width)}   "
            f"{fp.disposition.value.ljust(disposition_width)}  {fp.fingerprint}"
        )
    for name in provenance.ignored:
        lines.append(f"    {name.ljust(basename_width)}   ignored")
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
    """
    location = f":{problem.location}" if problem.location else ""
    return f"{problem.file}{location}: found {problem.found}; expected {problem.expected}"


@singledispatch
def as_text(result) -> str:
    """Render a result (`ThrowResult` or `CheckResult`) as human-readable text.

    Follows the rendering rules pinned by the golden files in
    `tests/golden/`: labels padded to the longest present, values signed,
    a trailing newline, and no `Modifier:`/sum noise when there is no
    modifier to show.

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


@as_text.register
def _(result: ThrowResult) -> str:
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
def _(result: CheckResult) -> str:
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
def _(result: ValidationReport) -> str:
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
