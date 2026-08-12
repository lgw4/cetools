from functools import singledispatch

from cetools.dice import ThrowResult


@singledispatch
def as_text(result) -> str:
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
