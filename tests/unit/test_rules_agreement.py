"""FR-023, SC-015: validation performed on demand and validation performed on
load agree on every data set they are both given, valid and invalid alike.
"""

from pathlib import Path

import pytest

from cetools.errors import RulesDataError
from cetools.rules import load_rules, validate_rules

_DATA = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data"
NAVY = (_DATA / "careers" / "navy.toml").read_text(encoding="utf-8")
BACKGROUND_SKILLS = (_DATA / "chargen" / "background-skills.toml").read_text(encoding="utf-8")
MISHAPS = (_DATA / "chargen" / "mishaps.toml").read_text(encoding="utf-8")


def test_a_valid_data_set_reported_valid_always_loads():
    report = validate_rules()
    assert report.valid
    rules = load_rules()
    assert rules.provenance == report.provenance


def test_an_invalid_data_set_reported_invalid_never_loads(tmp_path):
    (tmp_path / "navy.toml").write_text(NAVY.replace('"Comms"', '"Coms"', 1), encoding="utf-8")
    report = validate_rules(tmp_path)
    assert not report.valid
    with pytest.raises(RulesDataError) as exc_info:
        load_rules(tmp_path)
    assert set(exc_info.value.problems) == set(report.problems)


def test_a_valid_override_reported_valid_always_loads(tmp_path):
    (tmp_path / "navy.toml").write_text(
        NAVY.replace("target = 5", "target = 9", 1), encoding="utf-8"
    )
    report = validate_rules(tmp_path)
    assert report.valid
    rules = load_rules(tmp_path)
    assert rules.careers["navy"].throws["survival"].target == 9


def test_every_background_skill_the_packaged_table_grants_resolves(tmp_path):
    # FR-040: background-skills.toml's skill grants are checked inline
    # against the skills registry, the same way a career table's are. A name
    # the registry does not hold fails the whole set rather than loading.
    text = BACKGROUND_SKILLS.replace(
        '"Gun Combat 0", "Gun Combat 0"', '"Gun Fight 0", "Gun Combat 0"', 1
    )
    assert text != BACKGROUND_SKILLS
    (tmp_path / "background-skills.toml").write_text(text, encoding="utf-8")
    report = validate_rules(tmp_path)
    assert not report.valid
    with pytest.raises(RulesDataError):
        load_rules(tmp_path)


def test_every_characteristic_class_the_packaged_mishap_table_names_resolves(tmp_path):
    # FR-040a: the same cross-file rule aging.toml exercises in
    # tests/integration/test_validation_categories.py, demonstrated here
    # against the packaged mishap table.
    text = MISHAPS.replace(
        'class = "physical", count = 1, amount = "-1d6"',
        'class = "cybernetic", count = 1, amount = "-1d6"',
        1,
    )
    assert text != MISHAPS
    (tmp_path / "mishaps.toml").write_text(text, encoding="utf-8")
    report = validate_rules(tmp_path)
    assert not report.valid
    with pytest.raises(RulesDataError):
        load_rules(tmp_path)


def test_the_packaged_name_tables_load_with_seven_distinct_surname_regions():
    rules = load_rules()
    assert rules.given_names.names
    assert len(rules.surnames) == 7
    assert len({table.region for table in rules.surnames.values()}) == 7


# research.md R4: the 68 skills the source's skill chapter defines, plus
# `Perception` and `Prospecting`, which career tables grant and the chapter
# never defines.
_R4_CASCADES = {
    "Gun Combat": (
        "Archery",
        "Energy Pistol",
        "Energy Rifle",
        "Shotgun",
        "Slug Pistol",
        "Slug Rifle",
    ),
    "Gunnery": ("Bay Weapons", "Heavy Weapons", "Screens", "Spinal Mounts", "Turret Weapons"),
    "Melee Combat": (
        "Natural Weapons",
        "Bludgeoning Weapons",
        "Piercing Weapons",
        "Slashing Weapons",
    ),
    "Sciences": ("Life Sciences", "Physical Sciences", "Social Sciences", "Space Sciences"),
    "Animals": ("Farming", "Riding", "Survival", "Veterinary Medicine"),
    "Vehicle": ("Aircraft", "Mole", "Tracked Vehicle", "Watercraft", "Wheeled Vehicle"),
    "Aircraft": ("Grav Vehicle", "Rotor Aircraft", "Winged Aircraft"),
    "Watercraft": ("Motorboats", "Ocean Ships", "Sailing Ships", "Submarine"),
}
_R4_NON_CASCADES = {
    "Admin",
    "Advocate",
    "Athletics",
    "Battle Dress",
    "Bribery",
    "Broker",
    "Carousing",
    "Comms",
    "Computer",
    "Demolitions",
    "Electronics",
    "Engineering",
    "Gambling",
    "Gravitics",
    "Jack-of-All-Trades",
    "Leadership",
    "Liaison",
    "Linguistics",
    "Mechanics",
    "Medicine",
    "Navigation",
    "Piloting",
    "Recon",
    "Steward",
    "Streetwise",
    "Survival",
    "Tactics",
    "Zero-G",
    # The 32 specialty names above that are not themselves cascades (`Aircraft`
    # and `Watercraft` are excluded here — they are cascades in their own
    # right and already appear as keys of `_R4_CASCADES`).
    "Archery",
    "Energy Pistol",
    "Energy Rifle",
    "Shotgun",
    "Slug Pistol",
    "Slug Rifle",
    "Bay Weapons",
    "Heavy Weapons",
    "Screens",
    "Spinal Mounts",
    "Turret Weapons",
    "Natural Weapons",
    "Bludgeoning Weapons",
    "Piercing Weapons",
    "Slashing Weapons",
    "Life Sciences",
    "Physical Sciences",
    "Social Sciences",
    "Space Sciences",
    "Farming",
    "Riding",
    "Veterinary Medicine",
    "Mole",
    "Tracked Vehicle",
    "Wheeled Vehicle",
    "Grav Vehicle",
    "Rotor Aircraft",
    "Winged Aircraft",
    "Motorboats",
    "Ocean Ships",
    "Sailing Ships",
    "Submarine",
    "Perception",
    "Prospecting",
}


def test_the_packaged_skill_vocabulary_is_exactly_r4():
    skills = load_rules().skills.skills
    assert set(skills) == set(_R4_CASCADES) | _R4_NON_CASCADES
    assert len(skills) == 70
    for name, specialties in _R4_CASCADES.items():
        assert set(skills[name]) == set(specialties)
    for name in _R4_NON_CASCADES:
        assert skills[name] == ()


# research.md R5: exactly the eight items the twenty-four material tables
# award.
_R5_BENEFITS = {
    "Low Passage",
    "Mid Passage",
    "High Passage",
    "Weapon",
    "Explorers' Society",
    "Ship Share",
    "Courier Vessel",
    "Research Vessel",
}


def test_the_packaged_benefit_vocabulary_is_exactly_r5():
    items = load_rules().benefits.items
    assert set(items) == _R5_BENEFITS
    assert len(items) == 8


# research.md R8: the source's three background-skills lists, read from
# character-creation.html, in printed order with repeats intact — a set
# comparison would record a match where rows went missing, since the
# repeats are what carries the draw's weighting (FR-014a).
_R8_LAW_LEVEL = ("Gun Combat", "Gun Combat", "Gun Combat", "Melee Combat")
_R8_TRADE_CODE = (
    "Animals",
    "Zero-G",
    "Survival",
    "Watercraft",
    "Animals",
    "Computer",
    "Streetwise",
    "Zero-G",
    "Broker",
    "Survival",
    "Animals",
    "Carousing",
    "Watercraft",
    "Zero-G",
)
_R8_EDUCATION = (
    "Admin",
    "Advocate",
    "Animals",
    "Carousing",
    "Comms",
    "Computer",
    "Electronics",
    "Engineering",
    "Life Sciences",
    "Linguistics",
    "Mechanics",
    "Medicine",
    "Physical Sciences",
    "Social Sciences",
    "Space Sciences",
)


def test_the_packaged_background_skills_table_is_exactly_r8_in_printed_order():
    background_skills = load_rules().background_skills
    for attr, expected in (
        ("law_level", _R8_LAW_LEVEL),
        ("trade_code", _R8_TRADE_CODE),
        ("education", _R8_EDUCATION),
    ):
        rows = getattr(background_skills, attr)
        assert len(rows) == len(expected), attr
        names = tuple(row.skill.name for row in rows)
        assert names == expected, attr
        assert all(row.skill.specialty is None and row.level == 0 for row in rows), attr
