"""Text composition for interactive ship-design prompts.

Five pure functions, consulting no rule: `spell`/`key` are the display/stored
spelling round trip (FR-014, FR-015), `numbers` collapses an ascending run of
integers for display (FR-005), `split_values` splits an answer naming several
values by greedy longest-match (FR-015, FR-018), and `offer` composes the
`question (values{note})` text every closed-set prompt shares.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence


def spell(value: str | int) -> str:
    """The displayed spelling of a stored key: each `_` becomes a space."""
    return str(value).replace("_", " ")


def key(answer: str) -> str:
    """The stored key for a typed answer: lowercase, and space or `-` to `_`.

    Surrounding whitespace is ignored and an internal whitespace run counts as
    one space, so `"  pop   up  "` and `"pop up"` are the same answer.
    """
    collapsed = "_".join(answer.strip().split())
    return collapsed.lower().replace("-", "_")


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


def split_values(answer: str, known: Iterable[str]) -> list[str]:
    """Split `answer` into stored keys by greedy longest-match.

    Words are separated by whitespace or commas; a value may itself contain a
    space (`self sealing`), so the answer is matched against `known` before it
    is split rather than split first and matched word by word. The span limit
    is derived from `known` rather than hard-coded. Raises `ValueError` naming
    a word run that matches nothing.
    """
    known = tuple(known)
    known_set = set(known)
    max_span = max((k.count("_") + 1 for k in known), default=1)
    raw_words = [word for word in re.split(r"[,\s]+", answer.strip()) if word]
    words = [key(word) for word in raw_words]

    result: list[str] = []
    i = 0
    n = len(words)
    while i < n:
        span = min(max_span, n - i)
        while span >= 1:
            candidate = "_".join(words[i : i + span])
            if candidate in known_set:
                result.append(candidate)
                i += span
                break
            span -= 1
        else:
            raise ValueError(f"{raw_words[i]!r} is not a known value")
    return result


def offer(question: str, values: Iterable[str], *, note: str = "") -> str:
    """Compose `"{question} ({values}{note})"`.

    Returns `question` unchanged when `values` is empty and no `note` is
    given, and emits `note` alone, still parenthesised, when `values` is empty
    (FR-012's phrasing for an empty narrowed set).
    """
    values = list(values)
    if not values and not note:
        return question
    if not values:
        return f"{question} ({note})"
    return f"{question} ({', '.join(values)}{note})"
