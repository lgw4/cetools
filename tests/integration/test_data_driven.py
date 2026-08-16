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


def test_a_career_throw_takes_effect_with_no_code_edit(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace("target = 8", "target = 11", 1), encoding="utf-8")
    rules = load_rules(override)
    assert rules.careers["navy"].throws["promotion"].target == 11


def test_a_skill_table_entry_takes_effect_with_no_code_edit(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace('"Ship\'s Boat"', '"Admin"', 1), encoding="utf-8")
    rules = load_rules(override)
    entries = rules.careers["navy"].tables["service"].entries
    assert entries[0].name == "Admin"


def test_a_rank_bonus_takes_effect_with_no_code_edit(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.replace('bonus = "Gunnery 1"', 'bonus = "Gunnery 3"', 1), encoding="utf-8"
    )
    rules = load_rules(override)
    (enlisted,) = (ladder for ladder in rules.careers["navy"].ladders if ladder.name == "enlisted")
    (petty_officer,) = (rank for rank in enlisted.ranks if rank.title == "Petty Officer")
    assert petty_officer.bonus.level == 3


def test_removing_a_registry_entry_breaks_every_career_reference_to_it(tmp_path):
    assert '"Gunnery" = []\n' in SKILLS
    override = tmp_path / "skills.toml"
    override.write_text(SKILLS.replace('"Gunnery" = []\n', "", 1), encoding="utf-8")

    report = validate_rules(tmp_path)

    assert not report.valid
    gunnery_locations = {p.location for p in report.problems if "Gunnery" in p.found}
    assert gunnery_locations == {
        "tables.service.entries[3]",
        "tables.advanced.entries[4]",
        "ladders[0].ranks[1].bonus",
    }
