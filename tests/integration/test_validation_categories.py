"""One case per category in SC-002's closed list. The list is closed and
every category must be covered, or a category could regress into silent
acceptance. Whole-file categories assert an empty location (FR-022).

A file in an override that is not rules data is deliberately absent from
this list: FR-032a reports it rather than rejecting it (see
tests/unit/test_composition.py).
"""

import os
from pathlib import Path

import pytest

from cetools.rules import validate_rules

_DATA = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data"
NAVY = (_DATA / "careers" / "navy.toml").read_text(encoding="utf-8")
CHARACTERISTICS = (_DATA / "registries" / "characteristics.toml").read_text(encoding="utf-8")


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_unrecognized_name(tmp_path):
    text = NAVY.replace('"Comms"', '"Coms"', 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    # FR-013 asks for the registry the name was checked against, not merely
    # that some registry rejected it.
    assert any("Coms" in p.found and "skills registry" in p.expected for p in report.problems)


def test_unrecognized_key(tmp_path):
    text = NAVY.replace("[mustering-out]\n", "[mustering-out]\nchash = 5\n")
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(p.location == "mustering-out.chash" for p in report.problems)


def test_malformed_entry(tmp_path):
    text = NAVY.replace('"Comms"', '"Comms 2x"', 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any("Comms 2x" in p.found for p in report.problems)


def test_well_formed_entry_of_a_form_its_field_does_not_admit(tmp_path):
    # "INT 4+" is a well-formed characteristic check, but tables.service.entries
    # is a skill-table context, which does not admit the check form.
    text = NAVY.replace('"Comms"', '"INT 4+"', 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any("INT 4+" in p.found for p in report.problems)


def test_missing_required_element(tmp_path):
    text = NAVY.replace('[throws.survival]\ncharacteristic = "INT"\ntarget = 5\n\n', "")
    assert text != NAVY
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(p.location == "throws.survival" for p in report.problems)


def test_wrong_value_type(tmp_path):
    text = NAVY.replace(
        '[throws.survival]\ncharacteristic = "INT"\ntarget = 5\n',
        '[throws.survival]\ncharacteristic = "INT"\ntarget = "five"\n',
    )
    assert text != NAVY
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        p.location == "throws.survival.target" and p.found == "str" for p in report.problems
    )


def test_unsupported_schema_version_reports_nothing_else_from_that_file(tmp_path):
    text = NAVY.replace("schema-version = 1", "schema-version = 2", 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    from_navy = [p for p in report.problems if p.file == "navy.toml"]
    assert len(from_navy) == 1
    assert "2" in from_navy[0].found
    assert from_navy[0].location == ""


def test_missing_kind_declaration(tmp_path):
    text = NAVY.replace('schema = "career"\n', "", 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        p.file == "navy.toml" and p.found == "missing" and p.location == ""
        for p in report.problems
    )


def test_unrecognized_kind_declaration(tmp_path):
    # The other half of SC-002's "missing or unrecognized kind declaration":
    # a file that declares a kind nothing in the schema set answers to.
    text = NAVY.replace('schema = "career"', 'schema = "starships"', 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        p.file == "navy.toml" and "starships" in p.found and p.location == ""
        for p in report.problems
    )


def test_replacement_declared_kind_does_not_match_the_kind_it_replaces(tmp_path):
    text = NAVY.replace('schema = "career"', 'schema = "benefits"', 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        p.file == "navy.toml"
        and "career" in p.expected
        and "benefits" in p.found
        and p.location == ""
        for p in report.problems
    )


def test_file_not_well_formed_toml_at_all(tmp_path):
    _write(tmp_path, "navy.toml", "this is not [valid toml")
    report = validate_rules(tmp_path)
    assert not report.valid
    navy_problems = [p for p in report.problems if p.file == "navy.toml"]
    assert len(navy_problems) == 1
    assert navy_problems[0].location == ""


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="root reads a mode-000 file regardless of its mode",
)
def test_file_cannot_be_read(tmp_path):
    # The other half of SC-002's "not well-formed at all, or cannot be read".
    # A second override file carries its own mistake, because FR-020a requires
    # the remaining files to be checked rather than masked by the unreadable one.
    unreadable = _write(tmp_path, "navy.toml", NAVY)
    _write(
        tmp_path,
        "scouts.toml",
        NAVY.replace('name = "Navy"', 'name = "Scouts"', 1).replace('"Comms"', '"Coms"', 1),
    )
    unreadable.chmod(0o000)
    try:
        report = validate_rules(tmp_path)
    finally:
        unreadable.chmod(0o600)
    assert not report.valid
    navy_problems = [p for p in report.problems if p.file == "navy.toml"]
    assert len(navy_problems) == 1
    assert navy_problems[0].location == ""
    assert "read" in navy_problems[0].found
    assert any(p.file == "scouts.toml" and "Coms" in p.found for p in report.problems)


def test_two_careers_in_force_declare_the_same_name(tmp_path):
    _write(tmp_path, "scouts.toml", NAVY)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        "Navy" in p.found
        and "navy.toml" in p.file
        and "scouts.toml" in p.file
        and p.location == ""
        for p in report.problems
    )


def test_two_files_declare_the_same_single_instance_kind(tmp_path):
    _write(tmp_path, "characteristics2.toml", CHARACTERISTICS)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        "characteristics" in p.found
        and "characteristics.toml" in p.file
        and "characteristics2.toml" in p.file
        and p.location == ""
        for p in report.problems
    )


def test_a_single_instance_kind_is_absent(tmp_path):
    text = CHARACTERISTICS.replace('schema = "characteristics"\n', "", 1)
    _write(tmp_path, "characteristics.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        "characteristics" in p.expected and "exactly one" in p.expected and p.location == ""
        for p in report.problems
    )


def test_two_override_files_share_a_basename(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    _write(tmp_path / "a", "navy.toml", NAVY)
    _write(tmp_path / "b", "navy.toml", NAVY)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any("navy.toml" in p.found and p.location == "" for p in report.problems)


def test_sc003_four_distinct_problems_in_one_file_report_together(tmp_path):
    text = (
        NAVY.replace('"Comms"', '"Coms"', 1)
        .replace("[mustering-out]\n", "[mustering-out]\nchash = 5\n")
        .replace(
            '[throws.survival]\ncharacteristic = "INT"\ntarget = 5\n',
            '[throws.survival]\ncharacteristic = "INT"\ntarget = "five"\n',
        )
        .replace('"Gunnery", "Melee Combat"', '"Gunnery (Turret)", "Melee Combat"', 1)
    )
    assert text.count('"Gunnery (Turret)"') == 1
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    navy_problems = [p for p in report.problems if p.file == "navy.toml"]
    assert len(navy_problems) >= 4
