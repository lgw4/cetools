"""SC-011: a behavior change with no code edit, demonstrated for a career
throw, a skill table entry, a rank bonus, and a registry entry. The registry
case is the sharpest: removing a skill name from the registry must make
every career reference to it fail, which is what proves the registry is
what gives names meaning (FR-013).
"""

from pathlib import Path

from cetools.rules import load_rules, validate_rules

_DATA = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data"
NAVY = (_DATA / "careers" / "navy.toml").read_text(encoding="utf-8")
SKILLS = (_DATA / "registries" / "skills.toml").read_text(encoding="utf-8")
CHARACTERISTICS = (_DATA / "registries" / "characteristics.toml").read_text(encoding="utf-8")


_PROMOTION_BLOCK = '[throws.promotion]\ncharacteristic = "EDU"\ntarget = 6\n'
_TACTICS_ENTRY = '"Tactics" = []\n'


def test_a_career_throw_takes_effect_with_no_code_edit(tmp_path):
    assert _PROMOTION_BLOCK in NAVY
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.replace(_PROMOTION_BLOCK, _PROMOTION_BLOCK.replace("target = 6", "target = 11"), 1),
        encoding="utf-8",
    )
    rules = load_rules(override)
    assert rules.careers["navy"].throws["promotion"].target == 11


def test_a_skill_table_entry_takes_effect_with_no_code_edit(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace('"Comms"', '"Advocate"', 1), encoding="utf-8")
    rules = load_rules(override)
    entries = rules.careers["navy"].tables["service"].entries
    assert entries[0].name == "Advocate"


def test_a_rank_bonus_takes_effect_with_no_code_edit(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.replace('bonus = "Zero-G 1"', 'bonus = "Zero-G 3"', 1), encoding="utf-8"
    )
    rules = load_rules(override)
    (enlisted,) = (ladder for ladder in rules.careers["navy"].ladders if ladder.name == "enlisted")
    (starman,) = (rank for rank in enlisted.ranks if rank.title == "Starman")
    assert starman.bonus.level == 3


def test_removing_a_registry_entry_breaks_every_career_reference_to_it(tmp_path):
    assert _TACTICS_ENTRY in SKILLS
    override = tmp_path / "skills.toml"
    override.write_text(SKILLS.replace(_TACTICS_ENTRY, "", 1), encoding="utf-8")

    report = validate_rules(tmp_path)

    assert not report.valid
    tactics_locations = {p.location for p in report.problems if "Tactics" in p.found}
    assert tactics_locations == {
        "tables.advanced-education.entries[5]",
        "ladders[1].ranks[2].bonus",
    }


def test_removing_a_characteristic_from_the_registry_breaks_every_career_reference_to_it(
    tmp_path,
):
    # The skills case above is SC-011's "sharpest" registry demonstration but
    # proves only the skills registry; a characteristic code hard-coded into
    # `CharacteristicRegistry.__contains__` as a fallback would pass every
    # other test in the suite while making this one requirement — that a
    # characteristic is known from data, not from the parsing code (FR-012,
    # Constitution V) — false. One problem per characteristic-bearing
    # position in the shipped career: a throw's characteristic, a skill
    # table's characteristic adjustment entry, a table's gate, and a
    # mustering-out benefit's characteristic adjustment.
    edu_block = '[characteristics.EDU]\nlabel = "Education"\nclass = "mental"\n\n'
    assert edu_block in CHARACTERISTICS
    override = tmp_path / "characteristics.toml"
    override.write_text(CHARACTERISTICS.replace(edu_block, "", 1), encoding="utf-8")

    report = validate_rules(tmp_path)

    assert not report.valid
    edu_locations = {p.location for p in report.problems if p.found == "EDU"}
    assert edu_locations == {
        "throws.promotion.characteristic",
        "tables.personal.entries[4]",
        "tables.advanced-education.requires",
        "mustering-out.benefits[1]",
    }
