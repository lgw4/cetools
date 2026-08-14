"""Composition: how an override location combines with the packaged data set,
at library level and before any command exists (FR-028, FR-029, FR-032,
FR-032a, FR-032b).
"""

import shutil
from pathlib import Path

import pytest

from cetools.errors import RulesDataError
from cetools.provenance import Disposition
from cetools.rules import load_rules, validate_rules

NAVY = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"


def test_a_basename_matching_a_packaged_file_replaces_it(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.read_text(encoding="utf-8").replace("target = 5", "target = 9"), encoding="utf-8"
    )
    rules = load_rules(override)
    assert rules.careers["navy"].throws["survival"].target == 9
    assert len(rules.provenance.files) == 1
    assert rules.provenance.files[0].file == "navy.toml"
    assert rules.provenance.files[0].disposition is Disposition.REPLACED


def test_a_basename_matching_nothing_is_admitted_as_an_addition(tmp_path):
    override = tmp_path / "scouts.toml"
    text = NAVY.read_text(encoding="utf-8").replace('name = "Navy"', 'name = "Scouts"')
    override.write_text(text, encoding="utf-8")
    rules = load_rules(override)
    assert "navy" in rules.careers
    assert "scouts" in rules.careers
    assert rules.provenance.files[0].disposition is Disposition.ADDED


def test_a_non_toml_file_is_recorded_as_ignored_without_failing_the_load(tmp_path):
    (tmp_path / "notes.md").write_text("just some notes", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ("notes.md",)


def test_a_dot_prefixed_file_is_passed_over_silently(tmp_path):
    (tmp_path / ".DS_Store").write_text("binary junk", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ()
    assert report.provenance.is_packaged


def test_a_dot_prefixed_file_with_a_wrong_extension_still_appears_nowhere(tmp_path):
    (tmp_path / ".hidden.yaml").write_text("junk", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ()


def test_an_override_holding_only_ignored_files_still_composes_as_packaged(tmp_path):
    (tmp_path / "notes.md").write_text("just some notes", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.is_packaged
    assert report.provenance.ignored == ("notes.md",)


def test_an_existing_but_empty_location_composes_as_packaged(tmp_path):
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.is_packaged
    assert report.provenance.files == ()
    assert report.provenance.ignored == ()


def test_a_location_that_does_not_exist_is_a_usage_error_naming_it(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(RulesDataError, match="nope"):
        validate_rules(missing)


def test_two_override_files_sharing_a_basename_is_a_problem_naming_both(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    shutil.copy(NAVY, tmp_path / "a" / "navy.toml")
    shutil.copy(NAVY, tmp_path / "b" / "navy.toml")
    report = validate_rules(tmp_path)
    assert not report.valid
    combined = " ".join(f"{p.file} {p.found} {p.expected}" for p in report.problems)
    assert "a/navy.toml" in combined or "a" + "\\" + "navy.toml" in combined
    assert "b/navy.toml" in combined or "b" + "\\" + "navy.toml" in combined


def test_a_replacement_at_any_depth_within_the_override_is_positioned_by_basename(tmp_path):
    nested = tmp_path / "some" / "nested" / "path"
    nested.mkdir(parents=True)
    override = nested / "navy.toml"
    override.write_text(
        NAVY.read_text(encoding="utf-8").replace("target = 5", "target = 1"), encoding="utf-8"
    )
    rules = load_rules(override.parent)
    assert rules.careers["navy"].throws["survival"].target == 1
    assert rules.provenance.files[0].disposition is Disposition.REPLACED


def test_a_single_file_override_composes_exactly_as_a_directory_holding_it_alone(tmp_path):
    (tmp_path / "navy.toml").write_bytes(NAVY.read_bytes())
    directory_result = validate_rules(tmp_path)
    file_result = validate_rules(tmp_path / "navy.toml")
    assert directory_result.valid == file_result.valid
    assert directory_result.provenance.files == file_result.provenance.files
