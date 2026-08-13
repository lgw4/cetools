import json
from functools import singledispatch

from cetools.dice import ThrowResult
from cetools.tasks import CheckResult


@singledispatch
def as_text(result) -> str:
    """Render a result (`ThrowResult` or `CheckResult`) as human-readable text.

    Follows the rendering rules pinned by the golden files in
    `tests/golden/`: labels padded to the longest present, values signed,
    a trailing newline, and no `Modifier:`/sum noise when there is no
    modifier to show.
    """
    raise TypeError(f"no as_text rendering registered for {type(result).__name__}")


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
    outer_width = max(len(label) for label in ("Dice:", "Total:", "Seed:")) + 1
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
    return "\n".join(lines) + "\n"


@singledispatch
def as_dict(result) -> dict:
    """Render a result (`ThrowResult` or `CheckResult`) as the committed JSON shape.

    `seed` is emitted as a decimal string, since 64-bit seeds exceed
    2^53 and would be silently corrupted by a JavaScript consumer; every
    other numeric field is a JSON number.
    """
    raise TypeError(f"no as_dict rendering registered for {type(result).__name__}")


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
    }


def as_json(result) -> str:
    """Render `as_dict(result)` as indented JSON with a trailing newline."""
    return json.dumps(as_dict(result), indent=2, ensure_ascii=False) + "\n"
