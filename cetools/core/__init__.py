"""Core functionality for Cepheus Engine tools."""

from .config import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_CONFIG,
    ensure_config_dir,
    get_config_value,
    load_config,
    save_config,
    set_config_value,
)
from .models import (
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
    SkillLevel,
)
from .serialization import (
    SerializationError,
    from_json,
    load_character,
    load_from_file,
    load_npc,
    load_party,
    save_character,
    save_npc,
    save_party,
    save_to_file,
    to_csv,
    to_json,
)
from .utils import dec_to_pseudo_hex, is_pseudo_hex, normalize_pseudo_hex, pseudo_hex_to_dec

__all__ = [
    # Configuration
    "CONFIG_DIR",
    "CONFIG_FILE",
    "DEFAULT_CONFIG",
    "ensure_config_dir",
    "get_config_value",
    "load_config",
    "save_config",
    "set_config_value",
    # Models
    "Attributes",
    "AttributeType",
    "Character",
    "CharacterClass",
    "Equipment",
    "ItemType",
    "NPC",
    "NPCType",
    "Party",
    "Skill",
    "SkillLevel",
    # Serialization
    "SerializationError",
    "from_json",
    "load_character",
    "load_from_file",
    "load_npc",
    "load_party",
    "save_character",
    "save_npc",
    "save_party",
    "save_to_file",
    "to_csv",
    "to_json",
    # Utils
    "dec_to_pseudo_hex",
    "is_pseudo_hex",
    "normalize_pseudo_hex",
    "pseudo_hex_to_dec",
]

# This file contains GitHub Copilot generated content.
