import re

import pytest

from cetools.errors import RulesDataError, TaskError
from cetools.rules import load_rules, parse_task_parameters, validate_rules
from cetools.tasks import Band

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
    assert any(p.location == "task.target" and p.found == "str" for p in problems)


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


def test_supported_schema_version_is_a_literal_not_derived_from_package_version():
    # FR-003: the declared schema version must never be read from or compared
    # against the package's own release version.
    from importlib.metadata import version

    from cetools import rules as rules_module

    installed = version("cetools")
    for supported in rules_module._SUPPORTED_VERSION.values():
        assert str(supported) != installed
        assert isinstance(supported, int)
