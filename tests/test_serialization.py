"""Tests for serialization functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from cetools.core.models import Attributes, Character, CharacterClass, Equipment, ItemType
from cetools.core.serialization import (
    SerializationError,
    from_json,
    load_character,
    save_character,
    to_csv,
    to_json,
)


class TestSerialization:
    """Test serialization and deserialization functionality."""

    def setup_method(self):
        """Set up test data."""
        self.attrs = Attributes(
            strength=10,
            dexterity=12,
            endurance=11,
            intelligence=13,
            education=9,
            social_standing=8,
        )

        self.character = Character(
            name="Test Character",
            age=30,
            attributes=self.attrs,
            career=CharacterClass.ARMY,
            terms_served=2,
            credits=5000,
            homeworld="Terra",
            notes="Test character for unit tests",
        )

    def test_to_json(self):
        """Test JSON serialization."""
        json_str = to_json(self.character)

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["name"] == "Test Character"
        assert data["age"] == 30
        assert data["career"] == "army"

    def test_from_json(self):
        """Test JSON deserialization."""
        json_str = to_json(self.character)
        restored_character = from_json(json_str, Character)

        assert restored_character.name == self.character.name
        assert restored_character.age == self.character.age
        assert restored_character.career == self.character.career
        assert restored_character.attributes.strength == self.character.attributes.strength

    def test_to_csv(self):
        """Test CSV serialization."""
        characters = [self.character]
        csv_str = to_csv(characters)

        # Check that it contains the expected header and data
        lines = csv_str.strip().split("\n")
        assert len(lines) >= 2  # Header + data
        assert "name" in lines[0]
        assert "Test Character" in lines[1]

    def test_save_and_load_character_json(self):
        """Test saving and loading character to/from JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "character.json"

            # Save character
            save_character(self.character, file_path)
            assert file_path.exists()

            # Load character
            loaded_character = load_character(file_path)
            assert loaded_character.name == self.character.name
            assert loaded_character.attributes.strength == self.character.attributes.strength

    def test_serialization_error_handling(self):
        """Test error handling in serialization."""
        # Test loading from non-existent file
        with pytest.raises(FileNotFoundError):
            load_character("non_existent_file.json")

        # Test invalid JSON
        with pytest.raises(SerializationError):
            from_json("invalid json", Character)


# This file contains GitHub Copilot generated content.
