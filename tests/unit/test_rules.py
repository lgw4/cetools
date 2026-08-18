import re
from pathlib import Path

import pytest

from cetools.errors import RulesDataError, TaskError
from cetools.rules import load_rules, parse_task_parameters, validate_rules
from cetools.tasks import Band

_DATA = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data"
CHARACTERISTICS = (_DATA / "registries" / "characteristics.toml").read_text(encoding="utf-8")
TASKS = (_DATA / "tasks.toml").read_text(encoding="utf-8")
NAVY = (_DATA / "careers" / "navy.toml").read_text(encoding="utf-8")

VALID_TOML = """
schema = "task-parameters"
schema-version = 1

[task]
roll = "2d6"
target = 8
unskilled-dm = -3

[difficulty-dms]
"Simple" = 6
"Easy" = 4
"Routine" = 2
"Average" = 0
"Difficult" = -2
"Very Difficult" = -4
"Formidable" = -6

[characteristic-dms]
"0-2" = -2
"3-5" = -1
"6-8" = 0
"9-11" = 1
"12-14" = 2
"15-17" = 3
"18-20" = 4
"21-23" = 5
"24-26" = 6
"27-29" = 7
"30-32" = 8
"33+" = 9
"""


def _parsed(text: str):
    import tomllib

    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert not problems, problems
    assert parameters is not None
    return parameters


# --- parse_task_parameters: collected-problems restatement of the old reader ---


def test_valid_toml_parses_expected_target_dm_roll_ladder_and_bands():
    parameters = _parsed(VALID_TOML)
    assert parameters.roll == "2d6"
    assert parameters.target == 8
    assert parameters.unskilled_dm == -3
    assert list(parameters.difficulty_dms.items()) == [
        ("Simple", 6),
        ("Easy", 4),
        ("Routine", 2),
        ("Average", 0),
        ("Difficult", -2),
        ("Very Difficult", -4),
        ("Formidable", -6),
    ]
    assert len(parameters.characteristic_bands) == 12
    assert parameters.characteristic_bands[0] == Band(minimum=0, maximum=2, dm=-2)
    assert parameters.characteristic_bands[-1] == Band(minimum=33, maximum=None, dm=9)


def test_missing_task_table_reports_a_problem():
    import tomllib

    text = VALID_TOML.replace("[task]", "[not-task]")
    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert parameters is None
    assert any(p.location == "task" for p in problems)


def test_non_integer_target_reports_a_problem_locating_the_field():
    import tomllib

    text = VALID_TOML.replace("target = 8", 'target = "eight"')
    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert parameters is None
    assert any(p.location == "task.target" and p.found == "a string" for p in problems)


def test_unparseable_roll_reports_a_problem():
    import tomllib

    text = VALID_TOML.replace('roll = "2d6"', 'roll = "not dice notation"')
    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert parameters is None
    assert any(p.location == "task.roll" for p in problems)


def test_d66_roll_reports_a_problem():
    # `d66` parses as notation, but describes a two-digit table die rather than
    # a count and a side count, so it cannot describe a check's dice.
    import tomllib

    text = VALID_TOML.replace('roll = "2d6"', 'roll = "d66"')
    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert parameters is None
    assert any(p.location == "task.roll" for p in problems)


def test_zero_zero_modifier_rungs_reports_a_problem():
    import tomllib

    text = VALID_TOML.replace('"Average" = 0', '"Average" = 1')
    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert parameters is None
    assert any(p.location == "difficulty-dms" for p in problems)


def test_several_unbounded_bands_reports_a_problem():
    import tomllib

    text = VALID_TOML.replace('"30-32" = 8', '"30+" = 8')
    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert parameters is None
    assert any(p.location == "characteristic-dms" for p in problems)


def test_malformed_band_key_reports_a_problem():
    import tomllib

    text = VALID_TOML.replace('"0-2" = -2', '"low" = -2')
    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert parameters is None
    assert any(p.location == "characteristic-dms.low" for p in problems)


def test_unrecognized_key_reports_a_problem():
    import tomllib

    # Inserted before the first table header, or it would join whichever
    # table precedes it rather than landing at the top level.
    text = VALID_TOML.replace("[task]", 'nonsense = "value"\n\n[task]', 1)
    data = tomllib.loads(text)
    parameters, problems = parse_task_parameters(data, "tasks.toml")
    assert parameters is None
    assert any(p.location == "nonsense" for p in problems)


def test_fr022_edited_target_difficulty_unskilled_dm_and_band_bound_are_reflected():
    text = (
        VALID_TOML.replace("target = 8", "target = 10")
        .replace('"Average" = 0', '"Balanced" = 0')
        .replace("unskilled-dm = -3", "unskilled-dm = -5")
        .replace('"0-2" = -2', '"0-4" = -2')
        .replace('"3-5" = -1', '"5-5" = -1')
    )
    parameters = _parsed(text)
    assert parameters.target == 10
    assert parameters.unskilled_dm == -5
    assert parameters.difficulty_dm("Balanced") == 0
    assert parameters.default_difficulty() == "Balanced"
    assert parameters.characteristic_bands[0].maximum == 4


def test_fr022_removed_difficulty_rung_raises_task_error_listing_the_remainder():
    text = VALID_TOML.replace('"Formidable" = -6\n', "")
    parameters = _parsed(text)
    assert len(parameters.difficulty_dms) == 6
    with pytest.raises(TaskError) as exc_info:
        parameters.difficulty_dm("Formidable")
    message = str(exc_info.value)
    assert "Formidable" in message
    for remaining in parameters.difficulty_dms:
        assert remaining in message


def test_fr022_removed_characteristic_band_leaves_a_gap_that_raises():
    text = VALID_TOML.replace('"15-17" = 3\n', "")
    parameters = _parsed(text)
    assert len(parameters.characteristic_bands) == 11
    for score in (15, 16, 17):
        with pytest.raises(RulesDataError, match="no characteristic band covers"):
            parameters.characteristic_dm(score)
    assert parameters.characteristic_dm(14) == 2
    assert parameters.characteristic_dm(18) == 4


# --- load_rules / validate_rules: discovery, the whole packaged set ---


def test_load_rules_reads_the_packaged_data_set():
    rules = load_rules()
    assert rules.task_parameters.roll == "2d6"
    assert rules.task_parameters.target == 8
    assert "STR" in rules.characteristics
    assert "navy" in rules.careers
    assert rules.provenance.is_packaged


def test_load_rules_is_cached_for_the_no_override_call():
    first = load_rules()
    second = load_rules()
    assert first is second


def test_validate_rules_reports_the_packaged_data_set_as_valid():
    report = validate_rules()
    assert report.valid
    assert report.problems == ()
    assert report.file_count == 5


def test_validate_rules_file_count_counts_every_composed_toml():
    report = validate_rules()
    assert report.file_count == 5


def test_load_rules_rejects_a_nonexistent_override_location_as_a_usage_error(tmp_path):
    missing = tmp_path / "does-not-exist"
    # `re.escape`: `match` is a regex, and a Windows path's backslashes would
    # otherwise be read as escape sequences (`C:\Users` fails to compile).
    with pytest.raises(RulesDataError, match=re.escape(str(missing))):
        load_rules(missing)


def test_validate_rules_rejects_a_nonexistent_override_location_as_a_usage_error(tmp_path):
    missing = tmp_path / "does-not-exist"
    with pytest.raises(RulesDataError, match=re.escape(str(missing))):
        validate_rules(missing)


def test_load_rules_accepts_str_or_path_override(tmp_path):
    report_from_path = validate_rules(tmp_path)
    report_from_str = validate_rules(str(tmp_path))
    assert report_from_path.valid == report_from_str.valid


def test_a_supported_schema_version_is_counted_per_kind(tmp_path, monkeypatch):
    # FR-002a states the claim: "a change to one kind's shape MUST NOT
    # invalidate a user-supplied file of a kind whose shape did not change".
    # It is the sole justification the spec's Assumptions give for the version
    # field existing at all, and with every file in the suite declaring
    # version 1 for every kind, nothing could falsify it.
    from cetools import rules as rules_module

    monkeypatch.setitem(rules_module._SUPPORTED_VERSION, "characteristics", 2)
    (tmp_path / "characteristics.toml").write_text(
        CHARACTERISTICS.replace("schema-version = 1", "schema-version = 2", 1), encoding="utf-8"
    )
    report = validate_rules(tmp_path)
    assert report.valid, report.problems


def test_raising_one_kinds_version_rejects_that_kinds_file_and_no_others(tmp_path, monkeypatch):
    # The same claim from the other side: with characteristics at 2 and every
    # packaged file still declaring 1, the characteristics registry is the only
    # file whose version is refused, and the files of the untouched kinds
    # validate as they did. navy.toml is not among those, because a rejected
    # characteristics registry cascades into every name it would have
    # resolved — which is research R13's deliberate choice, not a version
    # judgement about the career.
    from cetools import rules as rules_module

    monkeypatch.setitem(rules_module._SUPPORTED_VERSION, "characteristics", 2)
    report = validate_rules(tmp_path)
    assert not report.valid
    version_problems = [p for p in report.problems if p.expected.startswith("version ")]
    assert [p.file for p in version_problems] == ["characteristics.toml"]
    for untouched in ("tasks.toml", "skills.toml", "benefits.toml"):
        assert not [p for p in report.problems if p.file == untouched]


class TestBooleansAreNotIntegers:
    """Every integer-valued field in this module guards on the exact type,
    because `True == 1` in Python and nowhere in TOML. Weakening any of these
    to a bare `isinstance` check left the whole suite green, and the
    consequence is a rules value changed with no report rather than a worse
    message: `"Difficult" = true` composed as difficulty modifier `1`, and
    `target = true` yielded `Throw(target=True)` (FR-020b, FR-014).
    """

    def _problems(self, text: str):
        import tomllib

        parameters, problems = parse_task_parameters(tomllib.loads(text), "tasks.toml")
        assert parameters is None
        return problems

    def test_a_boolean_task_target(self):
        problems = self._problems(VALID_TOML.replace("target = 8", "target = true"))
        matching = [p for p in problems if p.location == "task.target"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"
        assert matching[0].expected == "an integer"

    def test_a_boolean_unskilled_dm(self):
        problems = self._problems(VALID_TOML.replace("unskilled-dm = -3", "unskilled-dm = true"))
        matching = [p for p in problems if p.location == "task.unskilled-dm"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"

    def test_a_boolean_difficulty_modifier(self):
        problems = self._problems(VALID_TOML.replace('"Difficult" = -2', '"Difficult" = true'))
        matching = [p for p in problems if p.location == "difficulty-dms.Difficult"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"

    def test_a_boolean_characteristic_band_modifier(self):
        problems = self._problems(VALID_TOML.replace('"9-11" = 1', '"9-11" = true'))
        matching = [p for p in problems if p.location == "characteristic-dms.9-11"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"


class TestCollectedRatherThanRaisedOrDropped:
    """Five branches that could each be neutered with the suite green. Each is
    a problem the loader is required to collect (FR-020, FR-021, FR-023,
    SC-002), and losing one is a file that vanishes from the data set with no
    report, or a `validate_rules` call that raises instead of reporting.
    """

    def test_a_file_that_is_not_utf8_is_reported_rather_than_dropped(self, tmp_path):
        # The sibling `tomllib.TOMLDecodeError` branch three lines below this
        # one is covered, so the gap was an asymmetry rather than a drawn
        # line: with the `problems.append` removed and the `continue` kept, an
        # override career file with one bad byte left the data set with no
        # report at all and exit 0. SC-002's closed list names "a file that is
        # not well-formed at all, or cannot be read".
        (tmp_path / "navy.toml").write_bytes(NAVY.encode("utf-8").replace(b"Navy", b"Na\xffvy", 1))
        report = validate_rules(tmp_path)
        assert not report.valid
        navy_problems = [p for p in report.problems if p.file == "navy.toml"]
        assert len(navy_problems) == 1
        assert navy_problems[0].location == ""
        assert "UTF-8" in navy_problems[0].found

    def test_a_non_string_roll_is_collected_rather_than_sent_into_the_dice_parser(self, tmp_path):
        # Losing the type check sends a non-string into `_check_dice`, which
        # leaves `validate_rules` raising rather than collecting — an FR-021
        # and FR-023 break, not merely a worse message.
        (tmp_path / "tasks.toml").write_text(
            TASKS.replace('roll = "2d6"', "roll = 6", 1), encoding="utf-8"
        )
        report = validate_rules(tmp_path)
        assert not report.valid
        matching = [p for p in report.problems if p.location == "task.roll"]
        assert len(matching) == 1
        assert matching[0].found == "an integer"
        assert matching[0].expected == "a string"

    def test_a_misspelled_key_inside_the_task_table_reports_both_halves(self, tmp_path):
        # The `tasks.toml` analogue of the five career sites T084 closed: a
        # misspelling is an unrecognized key *and* a missing required one, and
        # only the second was proved. An author shown one of the two fixes the
        # wrong thing (FR-020, FR-021).
        (tmp_path / "tasks.toml").write_text(
            TASKS.replace("unskilled-dm = -3", "unskiled-dm = -3", 1), encoding="utf-8"
        )
        report = validate_rules(tmp_path)
        assert not report.valid
        locations = [p.location for p in report.problems if p.file == "tasks.toml"]
        assert "task.unskiled-dm" in locations
        assert "task.unskilled-dm" in locations

    def test_a_packaged_file_that_cannot_be_read_is_reported(self, monkeypatch, tmp_path):
        # The override-side twin of this branch is covered and the packaged
        # side was not. It also exercises the one source of `_singleton_slots`
        # nothing else reaches: `skills.toml` is gone from the packaged map
        # because it never read, so only its canonical basename can say which
        # slot it occupied, and without that the report would both name the
        # file and say there is no such file (FR-002, FR-020a).
        from cetools import rules as rules_module

        real_walk = rules_module._walk_toml

        class _Unreadable:
            name = "skills.toml"

            def read_bytes(self):
                raise OSError(13, "Permission denied")

        def walk(traversable):
            for entry in real_walk(traversable):
                yield _Unreadable() if entry.name == "skills.toml" else entry

        monkeypatch.setattr(rules_module, "_walk_toml", walk)
        report = validate_rules(tmp_path)
        assert not report.valid
        skills_problems = [p for p in report.problems if p.file == "skills.toml"]
        assert len(skills_problems) == 1
        assert skills_problems[0].location == ""
        assert "read" in skills_problems[0].found
        assert not [p for p in report.problems if "exactly one file declaring" in p.expected]

    def test_a_rejected_file_declaring_a_kind_at_any_basename_occupies_that_slot(
        self, monkeypatch, tmp_path
    ):
        # The other source of `_singleton_slots`, isolated: `house-skills.toml`
        # is neither a packaged basename nor a canonical one, so only what it
        # declared can say it stands for the skills registry. Its version is
        # refused, so its contents are not interpreted — and reporting the
        # kind absent as well would name a file and then deny it exists.
        from cetools import rules as rules_module

        real_discover = rules_module._discover_packaged

        def without_skills():
            files, problems = real_discover()
            del files["skills.toml"]
            return files, problems

        monkeypatch.setattr(rules_module, "_discover_packaged", without_skills)
        (tmp_path / "house-skills.toml").write_text(
            'schema = "skills"\nschema-version = 2\n\n[skills]\n"Comms" = []\n', encoding="utf-8"
        )
        report = validate_rules(tmp_path)
        assert not report.valid
        version_problems = [p for p in report.problems if p.expected == "version 1"]
        assert [p.file for p in version_problems] == ["house-skills.toml"]
        assert not [p for p in report.problems if "declaring kind 'skills'" in p.expected]


def test_canonical_file_names_the_packaged_declarer_of_every_single_instance_kind():
    """`_singleton_slots` reads a basename's slot out of `_CANONICAL_FILE`
    alone, which is only sound while that literal names the packaged file that
    actually declares each kind. Pinned here rather than kept as a second,
    always-agreeing source inside `_singleton_slots`, where neither could be
    shown to matter (FR-010a, FR-029).
    """
    from cetools import rules as rules_module

    packaged, problems = rules_module._discover_packaged()
    assert not problems
    declarers = rules_module._packaged_kind_map(packaged)
    for kind, basename in rules_module._CANONICAL_FILE.items():
        assert declarers.get(basename) == kind
    assert sorted(rules_module._CANONICAL_FILE) == sorted(rules_module._SINGLETON_KINDS)


def test_problems_arrive_sorted_by_file_then_location(tmp_path):
    """data-model.md and contracts/cli.md both state `(file, location)` order
    as the reason a report is stable run to run, which SC-002 and SC-003
    depend on to assert content — and nothing asserted it. Deleting the sort,
    or reversing it, left all 628 tests passing: the one test that mentions
    the order asserts that *rendering* must not re-sort, deferring to a
    guarantee nothing held.

    Broken in two files at once, and in two places within one of them, chosen
    so that the order the problems accumulate in differs from the sorted order
    on both axes: `tasks.toml` is validated first but sorts last, and within
    `navy.toml` the throws are read before the mustering-out block but sort
    after it (FR-022).
    """
    (tmp_path / "tasks.toml").write_text(
        TASKS.replace("target = 8", 'target = "eight"', 1), encoding="utf-8"
    )
    (tmp_path / "navy.toml").write_text(
        NAVY.replace("target = 5", 'target = "five"', 1).replace(
            "cash = [1000,", 'cash = ["1000",', 1
        ),
        encoding="utf-8",
    )
    report = validate_rules(tmp_path)
    assert not report.valid
    pairs = [(p.file, p.location) for p in report.problems]
    assert pairs == [
        ("navy.toml", "mustering-out.cash[0]"),
        ("navy.toml", "throws.survival.target"),
        ("tasks.toml", "task.target"),
    ]


def test_supported_schema_version_is_a_literal_not_derived_from_package_version():
    # FR-003: the declared schema version must never be read from or compared
    # against the package's own release version.
    from importlib.metadata import version

    from cetools import rules as rules_module

    installed = version("cetools")
    for supported in rules_module._SUPPORTED_VERSION.values():
        assert str(supported) != installed
        assert isinstance(supported, int)
