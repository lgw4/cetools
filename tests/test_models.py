"""Tests for core models and serialization."""

from cetools import Character, RollResult


def test_character_serialization_roundtrip():
    c = Character(
        name="Test",
        strength=10,
        dexterity=9,
        endurance=8,
        intelligence=7,
        education=6,
        social_standing=5,
        psionic_strength=None,
        careers={"Navy": 1},
        skills={"Gunnery": 1},
    )

    data = c.to_dict()
    assert data["name"] == "Test"
    assert data["strength"] == 10

    # validate roundtrip via from_dict
    c2 = Character.from_dict(data)
    assert c2.strength == 10


def test_rollresult_serializable():
    r = RollResult(expression="2d6+1", breakdown=[3, 4], total=8)
    data = r.model_dump()
    assert data["expression"] == "2d6+1"
    assert data["total"] == 8


# This file contains GitHub Copilot generated content.
