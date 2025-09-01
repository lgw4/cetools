"""Character generator for cetools.

This file contains GitHub Copilot generated content.
"""

from __future__ import annotations

from typing import Optional

from .dice import roll
from .exceptions import InvalidInputError
from .models import Character as CharacterModel


def _roll_stat(seed: Optional[int], expr: str) -> int:
    r = roll(expr, seed=seed)
    return r.total


def generate(seed: Optional[int] = None, template: dict | None = None) -> CharacterModel:
    """Generate a simple character.

    Attributes are generated using standard 3d6 rolls for STR/DEX/END/INT and
    2d6+6 for EDU/SOC as a small example. `template` may override any fields.
    The `seed` parameter is forwarded to the dice RNG for determinism.
    """
    if template is None:
        template = {}

    # base attributes
    strength = template.get("strength") or _roll_stat(seed, "3d6")
    dexterity = template.get("dexterity") or _roll_stat(
        seed + 1 if seed is not None else None, "3d6"
    )
    endurance = template.get("endurance") or _roll_stat(
        seed + 2 if seed is not None else None, "3d6"
    )
    intelligence = template.get("intelligence") or _roll_stat(
        seed + 3 if seed is not None else None, "3d6"
    )
    education = template.get("education") or _roll_stat(
        seed + 4 if seed is not None else None, "2d6+6"
    )
    social_standing = template.get("social_standing") or _roll_stat(
        seed + 5 if seed is not None else None, "2d6+6"
    )

    psionic_strength = template.get("psionic_strength")

    careers = template.get("careers", {})
    skills = template.get("skills", {})

    name = template.get("name")

    try:
        character = CharacterModel(
            name=name,
            strength=int(strength),
            dexterity=int(dexterity),
            endurance=int(endurance),
            intelligence=int(intelligence),
            education=int(education),
            social_standing=int(social_standing),
            psionic_strength=psionic_strength,
            careers=careers,
            skills=skills,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise InvalidInputError(f"Invalid character data: {exc}")

    return character


# This file contains GitHub Copilot generated content.
