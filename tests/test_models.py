"""Tests for data models."""

from datetime import datetime

import pytest

from cetools.core.models import (
    NPC,
    Attributes,
    AttributeType,
    Character,
    CharacterClass,
    Equipment,
    ItemType,
    NPCType,
    Party,
    Skill,
)


class TestAttributes:
    """Test the Attributes model."""

    def test_create_attributes_with_integers(self):
        """Test creating attributes with integer values."""
        attrs = Attributes(
            strength=15,
            dexterity=12,
            endurance=10,
            intelligence=13,
            education=11,
            social_standing=8,
        )

        assert attrs.strength == "F"
        assert attrs.dexterity == "C"
        assert attrs.endurance == "A"
        assert attrs.intelligence == "D"
        assert attrs.education == "B"
        assert attrs.social_standing == "8"

    def test_create_attributes_with_pseudo_hex(self):
        """Test creating attributes with pseudo-hex strings."""
        attrs = Attributes(
            strength="F",
            dexterity="C",
            endurance="A",
            intelligence="D",
            education="B",
            social_standing="8",
        )

        assert attrs.strength == "F"
        assert attrs.dexterity == "C"
        assert attrs.endurance == "A"
        assert attrs.intelligence == "D"
        assert attrs.education == "B"
        assert attrs.social_standing == "8"

    def test_get_modifier(self):
        """Test the get_modifier method."""
        attrs = Attributes(
            strength=2,  # -2 modifier
            dexterity=5,  # -1 modifier
            endurance=8,  # 0 modifier
            intelligence=11,  # 1 modifier
            education=14,  # 2 modifier
            social_standing=16,  # 3 modifier
        )

        assert attrs.get_modifier(AttributeType.STRENGTH) == -2
        assert attrs.get_modifier(AttributeType.DEXTERITY) == -1
        assert attrs.get_modifier(AttributeType.ENDURANCE) == 0
        assert attrs.get_modifier(AttributeType.INTELLIGENCE) == 1
        assert attrs.get_modifier(AttributeType.EDUCATION) == 2
        assert attrs.get_modifier(AttributeType.SOCIAL_STANDING) == 3


class TestSkill:
    """Test the Skill model."""

    def test_create_basic_skill(self):
        """Test creating a basic skill."""
        skill = Skill(name="Gun Combat", level=2)

        assert skill.name == "Gun Combat"
        assert skill.level == 2
        assert skill.specialty is None
        assert skill.display_name == "Gun Combat"

    def test_create_skill_with_specialty(self):
        """Test creating a skill with specialty."""
        skill = Skill(name="Gun Combat", level=2, specialty="Slug Pistol")

        assert skill.name == "Gun Combat"
        assert skill.level == 2
        assert skill.specialty == "Slug Pistol"
        assert skill.display_name == "Gun Combat (Slug Pistol)"

    def test_skill_level_validation(self):
        """Test skill level validation."""
        # Valid levels
        Skill(name="Test", level=-3)
        Skill(name="Test", level=0)
        Skill(name="Test", level=5)

        # Invalid levels should raise validation error
        with pytest.raises(ValueError):
            Skill(name="Test", level=-4)

        with pytest.raises(ValueError):
            Skill(name="Test", level=6)


class TestEquipment:
    """Test the Equipment model."""

    def test_create_basic_equipment(self):
        """Test creating basic equipment."""
        equipment = Equipment(
            name="Autopistol",
            item_type=ItemType.WEAPON,
            description="A common sidearm",
            cost=200,
        )

        assert equipment.name == "Autopistol"
        assert equipment.item_type == ItemType.WEAPON
        assert equipment.description == "A common sidearm"
        assert equipment.cost == 200
        assert equipment.quantity == 1

    def test_create_weapon_equipment(self):
        """Test creating weapon equipment with weapon-specific attributes."""
        weapon = Equipment(
            name="Autopistol",
            item_type=ItemType.WEAPON,
            damage="3d6",
            range_short=10,
            range_medium=20,
            range_long=40,
        )

        assert weapon.damage == "3d6"
        assert weapon.range_short == 10
        assert weapon.range_medium == 20
        assert weapon.range_long == 40

    def test_create_armor_equipment(self):
        """Test creating armor equipment."""
        armor = Equipment(
            name="Cloth Armor",
            item_type=ItemType.ARMOR,
            protection=5,
            tech_level=7,
        )

        assert armor.protection == 5
        assert armor.tech_level == 7


class TestCharacter:
    """Test the Character model."""

    def test_create_basic_character(self):
        """Test creating a basic character."""
        attrs = Attributes(
            strength=10,
            dexterity=12,
            endurance=11,
            intelligence=13,
            education=9,
            social_standing=8,
        )

        character = Character(
            name="John Doe",
            age=30,
            attributes=attrs,
            career=CharacterClass.ARMY,
            terms_served=2,
        )

        assert character.name == "John Doe"
        assert character.age == 30
        assert character.career == CharacterClass.ARMY
        assert character.terms_served == 2
        assert character.credits == 0
        assert len(character.skills) == 0
        assert len(character.equipment) == 0

    def test_add_skill(self):
        """Test adding skills to a character."""
        attrs = Attributes(
            strength=10,
            dexterity=10,
            endurance=10,
            intelligence=10,
            education=10,
            social_standing=10,
        )
        character = Character(name="Test", attributes=attrs)

        # Add new skill
        character.add_skill("Gun Combat", 2, "Rifle")
        assert len(character.skills) == 1
        assert character.get_skill_level("Gun Combat", "Rifle") == 2

        # Add skill without specialty
        character.add_skill("Athletics", 1)
        assert len(character.skills) == 2
        assert character.get_skill_level("Athletics") == 1

        # Update existing skill (should take higher level)
        character.add_skill("Gun Combat", 1, "Rifle")
        assert len(character.skills) == 2  # Should not add duplicate
        assert character.get_skill_level("Gun Combat", "Rifle") == 2  # Should keep higher level

    def test_get_skill_level(self):
        """Test getting skill levels."""
        attrs = Attributes(
            strength=10,
            dexterity=10,
            endurance=10,
            intelligence=10,
            education=10,
            social_standing=10,
        )
        character = Character(name="Test", attributes=attrs)

        # Test untrained skill
        assert character.get_skill_level("Pilot") == -3

        # Add a skill and test
        character.add_skill("Gun Combat", 2)
        assert character.get_skill_level("Gun Combat") == 2

    def test_add_equipment(self):
        """Test adding equipment to a character."""
        attrs = Attributes(
            strength=10,
            dexterity=10,
            endurance=10,
            intelligence=10,
            education=10,
            social_standing=10,
        )
        character = Character(name="Test", attributes=attrs)

        # Add new equipment
        pistol = Equipment(name="Autopistol", item_type=ItemType.WEAPON)
        character.add_equipment(pistol)
        assert len(character.equipment) == 1
        assert character.equipment[0].quantity == 1

        # Add identical equipment (should increase quantity)
        pistol2 = Equipment(name="Autopistol", item_type=ItemType.WEAPON)
        character.add_equipment(pistol2)
        assert len(character.equipment) == 1  # Should not add duplicate
        assert character.equipment[0].quantity == 2  # Should increase quantity


class TestNPC:
    """Test the NPC model."""

    def test_create_simple_npc(self):
        """Test creating a simple NPC without full attributes."""
        npc = NPC(
            name="Shopkeeper Bob",
            npc_type=NPCType.NEUTRAL,
            description="A friendly merchant",
        )

        assert npc.name == "Shopkeeper Bob"
        assert npc.npc_type == NPCType.NEUTRAL
        assert npc.description == "A friendly merchant"
        assert npc.attributes is None

    def test_create_detailed_npc(self):
        """Test creating a detailed NPC with attributes."""
        attrs = Attributes(
            strength=8,
            dexterity=10,
            endurance=9,
            intelligence=12,
            education=11,
            social_standing=10,
        )

        npc = NPC(
            name="Captain Reynolds",
            npc_type=NPCType.PATRON,
            attributes=attrs,
            motivation="Protect the innocent",
            patron_type="Military",
        )

        assert npc.name == "Captain Reynolds"
        assert npc.npc_type == NPCType.PATRON
        assert npc.attributes is not None
        assert npc.motivation == "Protect the innocent"
        assert npc.patron_type == "Military"

    def test_npc_get_skill_level(self):
        """Test getting skill levels for NPCs."""
        npc = NPC(name="Test NPC")

        # Test untrained skill
        assert npc.get_skill_level("Pilot") == -3

        # Add a notable skill
        npc.notable_skills.append(Skill(name="Leadership", level=3))
        assert npc.get_skill_level("Leadership") == 3


class TestParty:
    """Test the Party model."""

    def test_create_party(self):
        """Test creating a party."""
        attrs1 = Attributes(
            strength=10,
            dexterity=10,
            endurance=10,
            intelligence=10,
            education=10,
            social_standing=10,
        )
        attrs2 = Attributes(
            strength=12, dexterity=8, endurance=11, intelligence=9, education=12, social_standing=7
        )

        char1 = Character(name="Alice", attributes=attrs1, terms_served=2)
        char2 = Character(name="Bob", attributes=attrs2, terms_served=1)

        party = Party(name="The Adventurers", characters=[char1, char2])

        assert party.name == "The Adventurers"
        assert party.party_size == 2
        assert party.average_level == 1.5  # (2 + 1) / 2

    def test_empty_party(self):
        """Test party with no characters."""
        party = Party(name="Empty Party", characters=[])

        assert party.party_size == 0
        assert party.average_level == 0.0


# This file contains GitHub Copilot generated content.
