"""Tests for the character creation utilities."""

from cetools.core.creation import allocate_skills, create_character, generate_attributes
from cetools.core.models import Attributes, Character, Skill


def test_generate_attributes_deterministic():
    attrs1 = generate_attributes(seed=42)
    attrs2 = generate_attributes(seed=42)

    # Attributes should be identical for same seed
    assert attrs1.strength == attrs2.strength
    assert attrs1.dexterity == attrs2.dexterity
    assert isinstance(attrs1, Attributes)


def test_create_character_template_traveller():
    char = create_character("traveller", name="Test", seed=123)
    assert isinstance(char, Character)
    assert char.name == "Test"
    # Traveller template should include Piloting skill
    skill_names = [s.name for s in char.skills]
    assert any("Piloting" == n for n in skill_names)
    # Equipment should not be empty
    assert len(char.equipment) >= 1


def test_allocate_skills_override():
    skills = allocate_skills("soldier", extra_skills=[("Tactics", 2), ("Stealth", 1)])
    assert any(s.name == "Tactics" and s.level == 2 for s in skills)
    assert any(s.name == "Stealth" and s.level == 1 for s in skills)
