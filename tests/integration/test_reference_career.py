"""SC-004: the reference career exercises every element of the career schema,
evidenced by removing each required element in turn from a copy of the
shipped file and observing a specific rejection naming what is missing.
"""

from pathlib import Path

from cetools.notation import CharacteristicCheck, SkillGrant, SkillReference
from cetools.rules import load_rules, validate_rules

NAVY = (
    Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"
).read_text(encoding="utf-8")


def _removed(*fragments: str) -> str:
    text = NAVY
    for fragment in fragments:
        assert fragment in text, f"fixture assumption broken: {fragment!r} not found in navy.toml"
        text = text.replace(fragment, "", 1)
    assert text != NAVY
    return text


def _validate_missing(tmp_path, *fragments: str, location: str):
    (tmp_path / "navy.toml").write_text(_removed(*fragments), encoding="utf-8")
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        p.file == "navy.toml" and p.location == location for p in report.problems
    ), report.problems


def test_removing_the_name_is_rejected(tmp_path):
    _validate_missing(tmp_path, 'name = "Navy"\n\n', location="name")


def test_removing_the_qualification_throw_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        '[throws.qualification]\ncharacteristic = "INT"\ntarget = 6\n\n',
        location="throws.qualification",
    )


def test_removing_the_survival_throw_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        '[throws.survival]\ncharacteristic = "INT"\ntarget = 5\n\n',
        location="throws.survival",
    )


def test_removing_the_promotion_throw_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        '[throws.promotion]\ncharacteristic = "EDU"\ntarget = 6\n\n',
        location="throws.promotion",
    )


def test_removing_the_re_enlistment_throw_is_rejected(tmp_path):
    _validate_missing(
        tmp_path, "[throws.re-enlistment]\ntarget = 5\n\n", location="throws.re-enlistment"
    )


def test_removing_the_personal_table_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        '[tables.personal]\nentries = ["STR +1", "DEX +1", "END +1", "INT +1", "EDU +1", '
        '"Melee Combat"]\n\n',
        location="tables.personal",
    )


def test_removing_the_service_table_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        '[tables.service]\nentries = ["Comms", "Engineering", "Gun Combat", '
        '"Gunnery", "Melee Combat", "Vehicle"]\n\n',
        location="tables.service",
    )


def test_removing_the_advanced_table_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        '[tables.advanced]\nentries = ["Gravitics", "Jack-of-All-Trades", "Melee Combat", '
        '"Navigation", "Leadership", "Piloting"]\n\n',
        location="tables.advanced",
    )


def test_removing_every_rank_ladder_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        '[[ladders]]\nname = "enlisted"\nranks = [\n  '
        '{ rank = 0, title = "Starman", bonus = "Zero-G 1" },\n]\n\n',
        '[[ladders]]\nname = "officer"\nranks = [\n  '
        '{ rank = 1, title = "Midshipman", bonus = "Melee Combat (Slashing Weapons) 1" },\n  '
        '{ rank = 2, title = "Lieutenant" },\n  '
        '{ rank = 3, title = "Lt Commander", bonus = "Tactics 1" },\n  '
        '{ rank = 4, title = "Commander" },\n  { rank = 5, title = "Captain" },\n  '
        '{ rank = 6, title = "Commodore" },\n]\n\n',
        location="ladders",
    )


def test_removing_mustering_out_cash_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        "cash = [1000, 5000, 10000, 10000, 20000, 50000, 50000]\n",
        location="mustering-out.cash",
    )


def test_removing_mustering_out_benefits_is_rejected(tmp_path):
    _validate_missing(
        tmp_path,
        'benefits = ["Low Passage", "EDU +1", "Weapon", "Mid Passage", "SOC +1", '
        '"High Passage", "Explorers\' Society"]\n',
        location="mustering-out.benefits",
    )


def test_the_reference_career_carries_a_characteristic_gate():
    # FR-018 names a characteristic-gated table among the elements the shipped
    # career must exercise. It is the one element of that list SC-004's
    # remove-and-expect-a-rejection method cannot reach, a gate being optional,
    # so deleting `requires = "EDU 8+"` from navy.toml left the whole suite
    # passing and the requirement proved by nothing.
    gate = load_rules().careers["navy"].tables["advanced-education"].requires
    assert gate == CharacteristicCheck(characteristic="EDU", target=8)


def test_the_reference_career_writes_both_a_specified_specialty_and_an_owed_choice():
    # FR-018 requires the shipped career to exercise every element of the
    # schema, and the four skills that have specialties all appeared bare, so
    # the career exercised FR-008's owed-choice case and never FR-006's
    # base-and-specialty split. The split was proved by unit fixtures alone,
    # which is the gap FR-018 exists to close: a fixture's author can
    # unconsciously avoid the hard parts, and real content cannot.
    navy = load_rules().careers["navy"]
    officer = next(ladder for ladder in navy.ladders if ladder.name == "officer")
    specified = officer.ranks[0].bonus
    assert specified == SkillGrant(
        skill=SkillReference(name="Melee Combat", specialty="Slashing Weapons"), level=1
    )

    # The same skill, bare, elsewhere in the same file: both halves of FR-008's
    # distinction are in the shipped content rather than only in fixtures.
    assert SkillReference(name="Melee Combat", specialty=None) in navy.tables["service"].entries


def test_the_packaged_reference_career_itself_validates_cleanly():
    report = validate_rules()
    assert report.valid
