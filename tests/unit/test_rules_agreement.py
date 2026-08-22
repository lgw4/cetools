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
