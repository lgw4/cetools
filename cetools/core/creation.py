"""Character creation utilities for Cepheus Engine (basic generator).

This module implements a lightweight, seedable character generator used by
unit tests and the CLI. It provides simple templates, attribute rolling,
skill allocation, and equipment assignment sufficient to satisfy Step 2,
Phase 1, Item 1 of the implementation plan.

The implementation is intentionally small and conservative: it follows
Cepheus-style 2d6 attribute rolls and provides template-driven starting
skills and equipment so other systems in the repo can consume generated
Character objects.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from .models import Attributes, Character, CharacterClass, Equipment, ItemType, Skill

# Simple career templates. Each template contains a career, a list of base
# skills (name, level), and a list of equipment items (name, item_type, qty).
# This intentionally keeps things small and easy to extend later.
TEMPLATES: Dict[str, Dict] = {
    "traveller": {
        "career": CharacterClass.OTHER,
        "base_skills": [("Piloting", 0), ("Gunnery", 0), ("Mechanics", 0)],
        "equipment": [
            ("Pistol", ItemType.WEAPON, 1),
            ("Clothing", ItemType.EQUIPMENT, 1),
            ("Standard Ration", ItemType.CONSUMABLE, 5),
        ],
        "credit_range": (50, 200),
    },
    "soldier": {
        "career": CharacterClass.ARMY,
        "base_skills": [("Small Arms", 1), ("Tactics", 0), ("First Aid", 0)],
        "equipment": [
            ("Rifle", ItemType.WEAPON, 1),
            ("Helmet", ItemType.ARMOR, 1),
            ("Field Rations", ItemType.CONSUMABLE, 7),
        ],
        "credit_range": (20, 100),
    },
}


def _roll_2d6(rng: random.Random) -> int:
    """Roll 2d6 and return the sum."""
    return rng.randint(1, 6) + rng.randint(1, 6)


def generate_attributes(seed: Optional[int] = None) -> Attributes:
    """Generate a set of six Cepheus attributes using 2d6 rolls.

    Args:
        seed: Optional RNG seed for deterministic generation

    Returns:
        Attributes Pydantic model with normalized pseudo-hex values (via
        the Attributes validator).
    """
    rng = random.Random(seed)

    values = {
        "strength": _roll_2d6(rng),
        "dexterity": _roll_2d6(rng),
        "endurance": _roll_2d6(rng),
        "intelligence": _roll_2d6(rng),
        "education": _roll_2d6(rng),
        "social_standing": _roll_2d6(rng),
    }

    # The Attributes model will normalize values to pseudo-hex where
    # appropriate via its validators; we can pass ints here.
    return Attributes(**values)


def allocate_skills(
    template_name: str, terms_served: int = 0, extra_skills: Optional[List[Tuple[str, int]]] = None
) -> List[Skill]:
    """Create a skill list based on a template with optional extras.

    Args:
        template_name: Name of the template in TEMPLATES
        terms_served: Number of career terms (may be used to grant extra
            skill advances in future versions)
        extra_skills: Optional list of (name, level) to add or override

    Returns:
        List of Skill objects
    """
    tpl = TEMPLATES.get(template_name)
    if not tpl:
        raise KeyError(f"Unknown template: {template_name}")

    skills: Dict[str, Skill] = {}
    for name, level in tpl.get("base_skills", []):
        skills[name.lower()] = Skill(name=name, level=level)

    # Apply extra skills (override or add)
    if extra_skills:
        for name, level in extra_skills:
            skills[name.lower()] = Skill(name=name, level=level)

    # Future: allocate advances based on terms_served. For now, store
    # the provided base/extra skills.
    return list(skills.values())


def assign_equipment(template_name: str) -> List[Equipment]:
    """Assign equipment for the given template.

    This produces Equipment models with sensible defaults so they can be
    serialized by the rest of the system.
    """
    tpl = TEMPLATES.get(template_name)
    if not tpl:
        raise KeyError(f"Unknown template: {template_name}")

    equipment_list: List[Equipment] = []
    for name, item_type, qty in tpl.get("equipment", []):
        equipment_list.append(
            Equipment(name=name, item_type=item_type, quantity=qty, description=None)
        )

    return equipment_list


def create_character(
    template_name: str,
    name: Optional[str] = None,
    seed: Optional[int] = None,
    terms_served: int = 0,
    extra_skills: Optional[List[Tuple[str, int]]] = None,
) -> Character:
    """Create a Character from a small template.

    Args:
        template_name: Template name defined in TEMPLATES
        name: Optional character name
        seed: Optional RNG seed for deterministic generation
        terms_served: Number of terms (used for experience/advances in future)
        extra_skills: Optional list of (skill_name, level) to add/override

    Returns:
        A populated Character instance
    """
    tpl = TEMPLATES.get(template_name)
    if not tpl:
        raise KeyError(f"Unknown template: {template_name}")

    rng = random.Random(seed)

    attributes = generate_attributes(seed=seed)
    skills = allocate_skills(template_name, terms_served=terms_served, extra_skills=extra_skills)
    equipment = assign_equipment(template_name)

    # Determine starting credits
    cr_min, cr_max = tpl.get("credit_range", (0, 0))
    credits = rng.randint(cr_min, cr_max) if (cr_min <= cr_max) else 0

    character = Character(
        name=name or f"Unnamed {template_name.title()}",
        career=tpl.get("career"),
        terms_served=terms_served,
        attributes=attributes,
        skills=skills,
        equipment=equipment,
        credits=credits,
    )

    return character


# This file contains GitHub Copilot generated content.
