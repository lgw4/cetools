"""Text composition for interactive ship-design prompts.

Three pure functions, consulting no rule: `key` is the stored spelling of a
typed answer, `split_values` splits an answer naming several values by greedy
longest-match, and `offer` composes the `question (values{note})` text every
closed-set prompt shares.

`spell` and `numbers` are re-exported from `cetools.engine.notation`, which is
where they now live: a refusal has to name the same set in the same notation as
the question above it, and refusals are raised in the engine.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from cetools.engine.notation import numbers, spell

__all__ = ["key", "numbers", "offer", "spell", "split_values"]


def key(answer: str) -> str:
    """The stored key for a typed answer: lowercase, and space or `-` to `_`.

    Surrounding whitespace is ignored and an internal whitespace run counts as
    one space, so `"  pop   up  "` and `"pop up"` are the same answer.
    """
    collapsed = "_".join(answer.strip().split())
    return collapsed.lower().replace("-", "_")


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
    (the phrasing for an empty narrowed set).
    """
    values = list(values)
    if not values and not note:
        return question
    if not values:
        return f"{question} ({note})"
    return f"{question} ({', '.join(values)}{note})"
