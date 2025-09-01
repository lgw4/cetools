"""Pydantic models for cetools.

This file contains GitHub Copilot generated content.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class RollResult(BaseModel):
    expression: str
    breakdown: List[int]
    total: int

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict using Pydantic v2 model_dump."""
        return self.model_dump()


class Character(BaseModel):
    name: Optional[str]
    strength: int
    dexterity: int
    endurance: int
    intelligence: int
    education: int
    social_standing: int
    psionic_strength: Optional[int] = None
    careers: Dict[str, int] = {}
    skills: Dict[str, int] = {}

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict using Pydantic v2 model_dump."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """Create/validate a Character from a mapping using model_validate.

        This returns a `Character` instance or raises a `pydantic.ValidationError`.
        """
        return cls.model_validate(data)


class NPC(Character):
    npc_id: Optional[str] = None


# This file contains GitHub Copilot generated content.
