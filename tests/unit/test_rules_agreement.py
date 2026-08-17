"""FR-023, SC-015: validation performed on demand and validation performed on
load agree on every data set they are both given, valid and invalid alike.
"""

from pathlib import Path

import pytest

from cetools.errors import RulesDataError
from cetools.rules import load_rules, validate_rules

NAVY = (
    Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"
).read_text(encoding="utf-8")


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
