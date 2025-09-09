"""Data models for Cepheus Engine entities."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from ..core.utils import normalize_pseudo_hex


class AttributeType(str, Enum):
    """Standard Cepheus Engine attributes."""

    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    ENDURANCE = "endurance"
    INTELLIGENCE = "intelligence"
    EDUCATION = "education"
    SOCIAL_STANDING = "social_standing"


class SkillLevel(str, Enum):
    """Skill proficiency levels."""

    UNTRAINED = "untrained"
    LEVEL_0 = "level_0"
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"
    LEVEL_5 = "level_5"


class CharacterClass(str, Enum):
    """Character classes/careers."""

    ARMY = "army"
    MARINES = "marines"
    NAVY = "navy"
    SCOUTS = "scouts"
    MERCHANTS = "merchants"
    OTHER = "other"


class ItemType(str, Enum):
    """Types of equipment and items."""

    WEAPON = "weapon"
    ARMOR = "armor"
    EQUIPMENT = "equipment"
    CONSUMABLE = "consumable"
    VEHICLE = "vehicle"
    SHIP = "ship"


class NPCType(str, Enum):
    """Types of NPCs."""

    PATRON = "patron"
    ENEMY = "enemy"
    ALLY = "ally"
    CONTACT = "contact"
    NEUTRAL = "neutral"


class Attributes(BaseModel):
    """Character attributes using Cepheus Engine pseudo-hex notation."""

    strength: Union[str, int] = Field(..., description="Strength attribute in pseudo-hex")
    dexterity: Union[str, int] = Field(..., description="Dexterity attribute in pseudo-hex")
    endurance: Union[str, int] = Field(..., description="Endurance attribute in pseudo-hex")
    intelligence: Union[str, int] = Field(..., description="Intelligence attribute in pseudo-hex")
    education: Union[str, int] = Field(..., description="Education attribute in pseudo-hex")
    social_standing: Union[str, int] = Field(
        ..., description="Social Standing attribute in pseudo-hex"
    )

    @field_validator("*", mode="before")
    @classmethod
    def normalize_attributes(cls, value):
        """Normalize all attributes to pseudo-hex notation."""
        if isinstance(value, (int, str)):
            return normalize_pseudo_hex(value)
        return value

    def get_modifier(self, attribute: AttributeType) -> int:
        """Get the DM (Dice Modifier) for an attribute."""
        from ..core.utils import pseudo_hex_to_dec

        value = pseudo_hex_to_dec(getattr(self, attribute.value))
        if value <= 2:
            return -2
        elif value <= 5:
            return -1
        elif value <= 8:
            return 0
        elif value <= 11:
            return 1
        elif value <= 14:
            return 2
        else:
            return 3


class Skill(BaseModel):
    """A character skill with its level."""

    name: str = Field(..., description="Name of the skill")
    level: int = Field(default=0, ge=-3, le=5, description="Skill level (-3 to 5)")
    specialty: Optional[str] = Field(default=None, description="Skill specialty, if any")

    @property
    def display_name(self) -> str:
        """Display name including specialty if present."""
        if self.specialty:
            return f"{self.name} ({self.specialty})"
        return self.name


class Equipment(BaseModel):
    """A piece of equipment or gear."""

    name: str = Field(..., description="Name of the equipment")
    item_type: ItemType = Field(..., description="Type of item")
    description: Optional[str] = Field(default=None, description="Description of the item")
    weight: Optional[float] = Field(default=None, ge=0, description="Weight in kg")
    cost: Optional[int] = Field(default=None, ge=0, description="Cost in credits")
    tech_level: Optional[int] = Field(default=None, ge=0, le=15, description="Tech level (0-15)")
    quantity: int = Field(default=1, ge=1, description="Quantity owned")

    # Weapon-specific attributes
    damage: Optional[str] = Field(default=None, description="Damage dice notation")
    range_short: Optional[int] = Field(default=None, description="Short range in meters")
    range_medium: Optional[int] = Field(default=None, description="Medium range in meters")
    range_long: Optional[int] = Field(default=None, description="Long range in meters")

    # Armor-specific attributes
    protection: Optional[int] = Field(default=None, ge=0, description="Armor protection value")


class Character(BaseModel):
    """A player character or detailed NPC."""

    # Basic information
    name: str = Field(..., description="Character name")
    age: Optional[int] = Field(default=None, ge=18, description="Character age")
    homeworld: Optional[str] = Field(default=None, description="Character's homeworld")
    career: Optional[CharacterClass] = Field(default=None, description="Character's career")
    terms_served: int = Field(default=0, ge=0, description="Number of terms served in career")

    # Core stats
    attributes: Attributes = Field(..., description="Character attributes")
    skills: List[Skill] = Field(default_factory=list, description="Character skills")
    equipment: List[Equipment] = Field(default_factory=list, description="Character equipment")

    # Game mechanics
    credits: int = Field(default=0, ge=0, description="Character's money in credits")
    benefits: List[str] = Field(default_factory=list, description="Mustering out benefits")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    notes: Optional[str] = Field(default=None, description="Additional character notes")

    def get_skill_level(self, skill_name: str, specialty: Optional[str] = None) -> int:
        """Get the level of a specific skill."""
        for skill in self.skills:
            if skill.name.lower() == skill_name.lower():
                if specialty is None or (
                    skill.specialty and skill.specialty.lower() == specialty.lower()
                ):
                    return skill.level
        return -3  # Untrained

    def add_skill(self, name: str, level: int, specialty: Optional[str] = None) -> None:
        """Add or update a skill."""
        # Check if skill already exists
        for skill in self.skills:
            if skill.name.lower() == name.lower() and skill.specialty == specialty:
                skill.level = max(skill.level, level)  # Take the higher level
                return

        # Add new skill
        self.skills.append(Skill(name=name, level=level, specialty=specialty))

    def add_equipment(self, equipment: Equipment) -> None:
        """Add equipment to the character."""
        # Check if identical equipment already exists
        for existing in self.equipment:
            if (
                existing.name == equipment.name
                and existing.item_type == equipment.item_type
                and existing.description == equipment.description
            ):
                existing.quantity += equipment.quantity
                return

        # Add new equipment
        self.equipment.append(equipment)


class NPC(BaseModel):
    """A non-player character with simplified stats."""

    # Basic information
    name: str = Field(..., description="NPC name")
    npc_type: NPCType = Field(default=NPCType.NEUTRAL, description="Type of NPC")
    description: Optional[str] = Field(default=None, description="Physical description")

    # Core stats (may be simplified for minor NPCs)
    attributes: Optional[Attributes] = Field(default=None, description="NPC attributes")
    notable_skills: List[Skill] = Field(default_factory=list, description="Notable skills only")
    equipment: List[Equipment] = Field(default_factory=list, description="NPC equipment")

    # NPC-specific attributes
    motivation: Optional[str] = Field(default=None, description="NPC's primary motivation")
    personality: Optional[str] = Field(default=None, description="Personality traits")
    reaction_modifier: int = Field(default=0, ge=-6, le=6, description="Reaction roll modifier")

    # Patron-specific
    patron_type: Optional[str] = Field(default=None, description="Type of patron if applicable")
    mission_types: List[str] = Field(default_factory=list, description="Types of missions offered")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    notes: Optional[str] = Field(default=None, description="Additional NPC notes")

    def get_skill_level(self, skill_name: str) -> int:
        """Get the level of a notable skill."""
        for skill in self.notable_skills:
            if skill.name.lower() == skill_name.lower():
                return skill.level
        return -3  # Assume untrained for unlisted skills


class Party(BaseModel):
    """A group of characters for encounter balancing."""

    name: str = Field(..., description="Party name")
    characters: List[Character] = Field(..., description="Characters in the party")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    @property
    def average_level(self) -> float:
        """Calculate the average experience level of the party."""
        if not self.characters:
            return 0.0

        total_terms = sum(char.terms_served for char in self.characters)
        return total_terms / len(self.characters)

    @property
    def party_size(self) -> int:
        """Get the number of characters in the party."""
        return len(self.characters)


# This file contains GitHub Copilot generated content.
