"""How a set of acceptable values is written for a human.

Two pure functions, consulting no rule: `spell` is the displayed spelling of a
stored key, and `numbers` collapses an ascending run of integers.

Lives in the engine rather than beside the prompts that grew it because a
refusal has to name the same set the question named, in the same notation, and
the question and the refusal are raised in different layers. Rendering a hull
size as `[100, 200, ... 5000]` in one and `100-1000 by 100` in the other is two
spellings of one set, and the only way the wizard could avoid printing the first
was to stop calling the engine's validators and retype the rules behind them.
Sharing the notation is what lets one rule serve both.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def spell(value: str | int) -> str:
    """The displayed spelling of a stored key: each `_` becomes a space."""
    return str(value).replace("_", " ")


def numbers(values: Sequence[int]) -> list[str]:
    """Collapse `values` (ascending) into runs for display.

    A run of three or more evenly spaced values collapses to `"first-last"`,
    or `"first-last by step"` when the step is not 1. A run of exactly two
    collapses only when its step is 1; otherwise both are enumerated. A value
    in no run is enumerated in its place.
    """
    values = list(values)
    segments: list[str] = []
    i = 0
    n = len(values)
    while i < n:
        j = i
        step: int | None = None
        while j + 1 < n:
            candidate_step = values[j + 1] - values[j]
            if step is None:
                step = candidate_step
            elif candidate_step != step:
                break
            j += 1
        run_length = j - i + 1
        if run_length >= 3 or (run_length == 2 and step == 1):
            segment = f"{values[i]}-{values[j]}"
            if step != 1:
                segment += f" by {step}"
            segments.append(segment)
            i = j + 1
        else:
            segments.append(str(values[i]))
            i += 1
    return segments


def spelled_values(values: Iterable[str | int]) -> str:
    """A set of named values as a refusal writes it: displayed spelling, table
    order, comma-separated. Table order rather than sorted, because that is the
    order the question offered them in."""
    return ", ".join(spell(value) for value in values)


def numeric_values(values: Sequence[int]) -> str:
    """A set of numeric values as a refusal writes it: collapsed into runs,
    comma-separated."""
    return ", ".join(numbers(values))
