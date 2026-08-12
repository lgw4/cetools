import pytest

from cetools.errors import RulesDataError
from cetools.rules import _task_parameters_from_toml, load_task_parameters

VALID_TOML = """
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


def test_valid_toml_parses_expected_target_dm_roll_ladder_and_bands():
    parameters = _task_parameters_from_toml(VALID_TOML)
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
    assert parameters.characteristic_bands[0].minimum == 0
    assert parameters.characteristic_bands[0].maximum == 2
    assert parameters.characteristic_bands[0].dm == -2
    assert parameters.characteristic_bands[-1].minimum == 33
    assert parameters.characteristic_bands[-1].maximum is None
    assert parameters.characteristic_bands[-1].dm == 9


def test_load_task_parameters_reads_the_packaged_file():
    parameters = load_task_parameters()
    assert parameters.roll == "2d6"
    assert parameters.target == 8
    assert parameters.unskilled_dm == -3
    assert parameters.default_difficulty() == "Average"
    assert len(parameters.characteristic_bands) == 12


def test_missing_task_table_raises_rules_data_error():
    text = VALID_TOML.replace("[task]", "[not-task]")
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_missing_difficulty_dms_table_raises_rules_data_error():
    text = VALID_TOML.replace("[difficulty-dms]", "[not-difficulty-dms]")
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_missing_characteristic_dms_table_raises_rules_data_error():
    text = VALID_TOML.replace("[characteristic-dms]", "[not-characteristic-dms]")
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_non_integer_target_raises_rules_data_error():
    text = VALID_TOML.replace("target = 8", 'target = "eight"')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_non_integer_unskilled_dm_raises_rules_data_error():
    text = VALID_TOML.replace("unskilled-dm = -3", 'unskilled-dm = "minus three"')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_unparseable_roll_raises_rules_data_error():
    text = VALID_TOML.replace('roll = "2d6"', 'roll = "not dice notation"')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_non_integer_difficulty_value_raises_rules_data_error():
    text = VALID_TOML.replace('"Average" = 0', '"Average" = "zero"')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_malformed_band_key_raises_rules_data_error():
    text = VALID_TOML.replace('"0-2" = -2', '"low" = -2')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_non_integer_band_value_raises_rules_data_error():
    text = VALID_TOML.replace('"0-2" = -2', '"0-2" = "minus two"')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_zero_unbounded_bands_raises_rules_data_error():
    text = VALID_TOML.replace('"33+" = 9', '"33-40" = 9')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_several_unbounded_bands_raises_rules_data_error():
    text = VALID_TOML.replace('"30-32" = 8', '"30+" = 8')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_zero_zero_modifier_rungs_raises_rules_data_error():
    text = VALID_TOML.replace('"Average" = 0', '"Average" = 1')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_several_zero_modifier_rungs_raises_rules_data_error():
    text = VALID_TOML.replace('"Routine" = 2', '"Routine" = 0')
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml(text)


def test_invalid_toml_raises_rules_data_error():
    with pytest.raises(RulesDataError):
        _task_parameters_from_toml("this is not [valid toml")


def test_missing_packaged_file_raises_rules_data_error(monkeypatch):
    from cetools import rules

    class _AbsentTraversable:
        def joinpath(self, name):
            return self

        def read_text(self, encoding="utf-8"):
            raise FileNotFoundError("tasks.toml")

    monkeypatch.setattr(rules.resources, "files", lambda package: _AbsentTraversable())
    with pytest.raises(RulesDataError):
        rules.load_task_parameters()


def test_unreadable_packaged_file_raises_rules_data_error(monkeypatch):
    from cetools import rules

    class _UnreadableTraversable:
        def joinpath(self, name):
            return self

        def read_text(self, encoding="utf-8"):
            raise OSError("permission denied")

    monkeypatch.setattr(rules.resources, "files", lambda package: _UnreadableTraversable())
    with pytest.raises(RulesDataError):
        rules.load_task_parameters()


def test_sc010_edited_target_difficulty_unskilled_dm_and_band_bound_are_reflected():
    text = (
        VALID_TOML.replace("target = 8", "target = 10")
        .replace('"Average" = 0', '"Balanced" = 0')
        .replace("unskilled-dm = -3", "unskilled-dm = -5")
        .replace('"0-2" = -2', '"0-4" = -2')
        .replace('"3-5" = -1', '"5-5" = -1')
    )
    parameters = _task_parameters_from_toml(text)
    assert parameters.target == 10
    assert parameters.unskilled_dm == -5
    assert parameters.difficulty_dm("Balanced") == 0
    assert parameters.default_difficulty() == "Balanced"
    assert parameters.characteristic_bands[0].maximum == 4


def test_fr023_decoy_file_in_working_directory_is_ignored(tmp_path, monkeypatch):
    decoy = tmp_path / "tasks.toml"
    decoy.write_text(VALID_TOML.replace("target = 8", "target = 999"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    parameters = load_task_parameters()
    assert parameters.target == 8
