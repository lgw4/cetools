import cetools
from cetools.errors import CetoolsError, DiceError, RulesDataError, TaskError


def test_cetools_error_subclasses_exception():
    assert issubclass(CetoolsError, Exception)


def test_dice_error_subclasses_cetools_error():
    assert issubclass(DiceError, CetoolsError)


def test_rules_data_error_subclasses_cetools_error():
    assert issubclass(RulesDataError, CetoolsError)


def test_task_error_subclasses_cetools_error():
    assert issubclass(TaskError, CetoolsError)


def test_all_four_errors_importable_from_cetools():
    assert cetools.CetoolsError is CetoolsError
    assert cetools.DiceError is DiceError
    assert cetools.RulesDataError is RulesDataError
    assert cetools.TaskError is TaskError
