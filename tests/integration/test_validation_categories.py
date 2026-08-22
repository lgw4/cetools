"""One case per category in SC-002's closed list. The list is closed and
every category must be covered, or a category could regress into silent
acceptance. Whole-file categories assert an empty location (FR-022).

A file in an override that is not rules data is deliberately absent from
this list: FR-032a reports it rather than rejecting it (see
tests/unit/test_composition.py).
"""

from pathlib import Path

import pytest

from cetools import rules
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
    # that some registry rejected it. SC-002 asks for the file and, because
    # this problem is not about the file as a whole, the location within it;
    # without those two this could regress into a whole-file problem against
    # any file and still pass.
    assert any(
        p.file == "navy.toml"
        and p.location == "tables.service.entries[0]"
        and "Coms" in p.found
        and "skills registry" in p.expected
        for p in report.problems
    )


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
    assert any(
        p.file == "navy.toml"
        and p.location == "tables.service.entries[0]"
        and "Comms 2x" in p.found
        for p in report.problems
    )


def test_well_formed_entry_of_a_form_its_field_does_not_admit(tmp_path):
    # "INT 4+" is a well-formed characteristic check, but tables.service.entries
    # is a skill-table context, which does not admit the check form.
    text = NAVY.replace('"Comms"', '"INT 4+"', 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    assert any(
        p.file == "navy.toml" and p.location == "tables.service.entries[0]" and "INT 4+" in p.found
        for p in report.problems
    )


def test_a_specialty_given_for_a_skill_that_has_none(tmp_path):
    # FR-007's first half end to end: the shipped registry declares `Comms`
    # with no specialties, so `Comms (Radio)` must be reported distinguishably
    # from an unrecognized skill name. The branch that builds that text was
    # reached by no test outside the enum's own unit cases.
    text = NAVY.replace('"Comms"', '"Comms (Radio)"', 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    matching = [p for p in report.problems if p.location == "tables.service.entries[0]"]
    assert len(matching) == 1
    assert matching[0].found == "Comms (Radio)"
    assert "no specialties" in matching[0].expected


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
        p.file == "navy.toml" and p.location == "throws.survival.target" and p.found == "a string"
        for p in report.problems
    )


@pytest.mark.parametrize(
    ("literal", "found"),
    [("true", "a boolean"), ("1.0", "a number"), ('"1"', "a string")],
)
def test_a_schema_version_of_the_wrong_type_is_a_type_problem(tmp_path, literal, found):
    # Python equality makes `True == 1` and `1.0 == 1`, so comparing the
    # declared version against the supported one without the type guard every
    # other integer-valued field in the module carries let a career declaring
    # `schema-version = true` pass the version gate and validate clean
    # (FR-002, FR-020b).
    text = NAVY.replace("schema-version = 1", f"schema-version = {literal}", 1)
    assert text != NAVY
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    from_navy = [p for p in report.problems if p.file == "navy.toml"]
    assert len(from_navy) == 1
    assert from_navy[0].location == "schema-version"
    assert from_navy[0].found == found
    assert "integer" in from_navy[0].expected


def test_a_missing_schema_version_is_rejected_like_a_mismatched_one(tmp_path):
    # FR-001's other half: a file declaring no version at all, not merely the
    # wrong one. Every existing version-mismatch case replaces the value;
    # none omits the key, so `declared_version != supported` could be guarded
    # with `declared_version is not None and ...` and still pass every one of
    # them, silently accepting an undeclared version — exactly the upgrade
    # story FR-001 exists to close off.
    text = NAVY.replace("schema-version = 1\n", "", 1)
    assert "schema-version" not in text
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    from_navy = [p for p in report.problems if p.file == "navy.toml"]
    assert len(from_navy) == 1
    assert from_navy[0].found == "missing"
    assert from_navy[0].expected == "version 1"
    assert from_navy[0].location == ""


def test_unsupported_schema_version_reports_nothing_else_from_that_file(tmp_path):
    text = NAVY.replace("schema-version = 1", "schema-version = 2", 1)
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    from_navy = [p for p in report.problems if p.file == "navy.toml"]
    assert len(from_navy) == 1
    assert "2" in from_navy[0].found
    assert from_navy[0].location == ""


def test_a_version_mismatched_file_is_not_interpreted_even_when_it_is_full_of_mistakes(tmp_path):
    # FR-002's "MUST NOT attempt to interpret that file's contents", stated so
    # that something can falsify it. The two cases above bump `schema-version`
    # on an otherwise clean file, so their one-problem assertion holds whether
    # or not the contents were interpreted: with the early exit deleted, a
    # version-mismatched file fell through and was fully validated, and the
    # whole suite stayed green. Seeded with two further deliberate mistakes,
    # each of which is a reported problem on its own, the file must still
    # report exactly the version mismatch and nothing else (FR-021,
    # contracts/data-files.md rule 2, quickstart Scenario 2).
    text = (
        NAVY.replace("schema-version = 1", "schema-version = 2", 1)
        .replace('"Comms"', '"Coms"', 1)
        .replace("[mustering-out]\n", "[mustering-out]\nchash = 5\n")
    )
    assert '"Coms"' in text and "chash" in text
    _write(tmp_path, "navy.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    from_navy = [p for p in report.problems if p.file == "navy.toml"]
    assert len(from_navy) == 1, from_navy
    assert from_navy[0].found == "version 2"
    assert from_navy[0].expected == "version 1"
    assert from_navy[0].location == ""


def test_unsupported_schema_version_on_a_single_instance_kind_reports_nothing_else(tmp_path):
    # The same assertion as the case above, for a single-instance kind rather
    # than a career: a career is the one kind the absent-kind check cannot
    # reach, so it cannot show that a file rejected at the header stage is
    # then also reported missing (contracts/data-files.md rule 2, FR-002).
    text = CHARACTERISTICS.replace("schema-version = 2", "schema-version = 99", 1)
    assert text != CHARACTERISTICS
    _write(tmp_path, "characteristics.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    from_file = [p for p in report.problems if p.file == "characteristics.toml"]
    assert len(from_file) == 1
    assert "99" in from_file[0].found
    assert from_file[0].location == ""


def test_a_rejected_single_instance_file_is_not_also_reported_as_absent(tmp_path):
    # The kind is misspelled, so the file is rejected before its contents are
    # interpreted, but it is sitting in the composed data set: naming it and
    # then saying there is no such file states something false (FR-002).
    text = CHARACTERISTICS.replace('schema = "characteristics"', 'schema = "charactristics"', 1)
    assert text != CHARACTERISTICS
    _write(tmp_path, "characteristics.toml", text)
    report = validate_rules(tmp_path)
    assert not report.valid
    from_file = [p for p in report.problems if p.file == "characteristics.toml"]
    assert len(from_file) == 1
    assert "charactristics" in from_file[0].found
    assert from_file[0].location == ""


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
    # FR-020a asks for the malformation "located as precisely as the format
    # allows"; dropping tomllib's own exception text would leave a bare
    # category string here with nothing to show for that clause.
    assert "line" in navy_problems[0].found
    assert "column" in navy_problems[0].found


def test_malformed_toml_leaves_the_remaining_files_checked(tmp_path):
    # FR-020a's second sentence: the malformed file's own `continue` must not
    # become a `break`, or an independent mistake in a second, later-sorted
    # file vanishes from the report along with it (SC-002's "the remaining
    # files ... MUST still be checked"). Asserting only the *absence* of a
    # problem from the second file would be vacuous under a `break`, since an
    # unprocessed file also reports nothing; the second file must carry a
    # deliberate mistake of its own that only a real check catches.
    _write(tmp_path, "navy.toml", "this is not [valid toml")
    _write(
        tmp_path,
        "scouts.toml",
        NAVY.replace('name = "Navy"', 'name = "Scouts"', 1).replace('"Comms"', '"Coms"', 1),
    )
    report = validate_rules(tmp_path)
    assert not report.valid
    navy_problems = [p for p in report.problems if p.file == "navy.toml"]
    assert len(navy_problems) == 1
    assert navy_problems[0].location == ""
    assert any(p.file == "scouts.toml" and "Coms" in p.found for p in report.problems)


def test_undecodable_utf8_leaves_the_remaining_files_checked(tmp_path):
    # The UTF-8 decode branch's own `continue`, isolated from the TOML decode
    # branch above: dropping the problem and keeping the `continue` is
    # covered elsewhere, but turning the `continue` into a `break` — which
    # would mask every file discovered after this one in sorted order — is
    # not.
    (tmp_path / "navy.toml").write_bytes(NAVY.encode("utf-8").replace(b"Navy", b"Na\xffvy", 1))
    _write(tmp_path, "zzz-scouts.toml", NAVY.replace('"Comms"', '"Coms"', 1))
    report = validate_rules(tmp_path)
    assert not report.valid
    navy_problems = [p for p in report.problems if p.file == "navy.toml"]
    assert len(navy_problems) == 1
    assert navy_problems[0].location == ""
    # FR-020a's "located as precisely as the format allows": Python's own
    # `UnicodeDecodeError` text names the byte and the position.
    assert "position" in navy_problems[0].found
    assert any(p.file == "zzz-scouts.toml" and "Coms" in p.found for p in report.problems)


@pytest.mark.needs_enforced_chmod
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
    # FR-020a's precision clause: the OS's own errno text, not a bare
    # category string.
    assert "permission" in navy_problems[0].found.lower()
    assert any(p.file == "scouts.toml" and "Coms" in p.found for p in report.problems)


@pytest.mark.needs_enforced_chmod
def test_directory_within_an_override_cannot_be_listed(tmp_path):
    # The directory-walk analogue of `test_file_cannot_be_read`: a
    # subdirectory the process cannot list is a collected problem naming it,
    # not a subtree passed over in silence (FR-020a, FR-022,
    # contracts/data-files.md). A second, sibling file carries its own
    # mistake so the remaining files are proved still checked.
    unlistable = tmp_path / "locked"
    unlistable.mkdir()
    (unlistable / "navy.toml").write_text(NAVY, encoding="utf-8")
    _write(
        tmp_path,
        "scouts.toml",
        NAVY.replace('name = "Navy"', 'name = "Scouts"', 1).replace('"Comms"', '"Coms"', 1),
    )
    unlistable.chmod(0o000)
    try:
        report = validate_rules(tmp_path)
    finally:
        unlistable.chmod(0o700)
    assert not report.valid
    locked_problems = [p for p in report.problems if p.file == "locked"]
    assert len(locked_problems) == 1
    assert locked_problems[0].location == ""
    assert "permission" in locked_problems[0].found.lower()
    assert any(p.file == "scouts.toml" and "Coms" in p.found for p in report.problems)


def test_two_careers_in_force_declare_the_same_name(tmp_path):
    _write(tmp_path, "scouts.toml", NAVY)
    report = validate_rules(tmp_path)
    assert not report.valid
    matching = [p for p in report.problems if "Navy" in p.found]
    assert len(matching) == 1
    assert matching[0].file == "navy.toml"
    assert matching[0].location == ""
    assert "navy.toml" in matching[0].found and "scouts.toml" in matching[0].found


def test_two_files_declare_the_same_single_instance_kind(tmp_path):
    _write(tmp_path, "characteristics2.toml", CHARACTERISTICS)
    report = validate_rules(tmp_path)
    assert not report.valid
    matching = [p for p in report.problems if "declared by" in p.found]
    assert len(matching) == 1
    assert matching[0].file == "characteristics.toml"
    assert matching[0].location == ""
    assert "characteristics.toml" in matching[0].found
    assert "characteristics2.toml" in matching[0].found


def test_a_problem_naming_two_files_still_carries_one_composition_key(tmp_path):
    # contracts/json-output.md and data-model.md type `problems[].file` as the
    # composition key of *the* file, singular, and contracts/cli.md justifies
    # the text line's shape on the grounds that leading with the file makes
    # the report greppable. Joining two names into that field gives a consumer
    # grouping by key a phantom key matching no file, and one filtering for
    # `navy.toml` misses the problem entirely. FR-019b and FR-010a are
    # satisfied by naming both files in `found`, which is what FR-029a's
    # duplicate-basename problem already does.
    _write(tmp_path, "scouts.toml", NAVY)
    _write(tmp_path, "characteristics2.toml", CHARACTERISTICS)
    report = validate_rules(tmp_path)
    assert not report.valid
    composed = {
        "tasks.toml",
        "characteristics.toml",
        "characteristics2.toml",
        "skills.toml",
        "benefits.toml",
        "navy.toml",
        "scouts.toml",
    }
    for problem in report.problems:
        assert problem.file in composed, problem


def test_a_single_instance_kind_is_absent(tmp_path, monkeypatch):
    # Absence has to be produced at the packaged set, not through an override.
    # An override can only replace a file or add one, so the only way to break
    # a shipped registry from outside is to have it rejected at the header
    # stage — and a file that is present but rejected is not absent, which is
    # what the two tests above forbid reporting.
    real_discover = rules._discover_packaged

    def without_characteristics():
        files, problems = real_discover()
        del files["characteristics.toml"]
        return files, problems

    monkeypatch.setattr(rules, "_discover_packaged", without_characteristics)
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
