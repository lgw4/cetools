import re
import tomllib
from functools import cache
from importlib import resources

from cetools.dice import parse_notation
from cetools.errors import DiceError, RulesDataError
from cetools.tasks import Band, TaskParameters

_BAND_RANGE = re.compile(r"^(\d+)-(\d+)$")
_BAND_UNBOUNDED = re.compile(r"^(\d+)\+$")


def _task_parameters_from_toml(text: str) -> TaskParameters:
    """Parse and validate `tasks.toml` text into `TaskParameters`.

    Holds the entire validation table from contracts/tasks-toml.md. Raises
    `RulesDataError` on any failure, with no fallback to built-in values
    (FR-024). Kept separate from `load_task_parameters` so every failure
    path is reachable from a test without a file on disk.
    """
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise RulesDataError(f"invalid TOML: {exc}") from exc

    for table in ("task", "difficulty-dms", "characteristic-dms"):
        if table not in data:
            raise RulesDataError(f"missing required table [{table}]")

    task = data["task"]

    roll = task.get("roll")
    if not isinstance(roll, str):
        raise RulesDataError("task.roll must be a string")
    try:
        parse_notation(roll)
    except DiceError as exc:
        raise RulesDataError(f"task.roll is not valid dice notation: {roll!r}") from exc

    target = task.get("target")
    if not isinstance(target, int) or isinstance(target, bool):
        raise RulesDataError("task.target must be an integer")

    unskilled_dm = task.get("unskilled-dm")
    if not isinstance(unskilled_dm, int) or isinstance(unskilled_dm, bool):
        raise RulesDataError("task.unskilled-dm must be an integer")

    difficulty_dms: dict[str, int] = {}
    zero_count = 0
    for name, value in data["difficulty-dms"].items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise RulesDataError(f"difficulty-dms.{name!r} must be an integer")
        if value == 0:
            zero_count += 1
        difficulty_dms[name] = value
    if zero_count != 1:
        raise RulesDataError(
            f"exactly one difficulty rung must have a modifier of 0, found {zero_count}"
        )

    bands: list[Band] = []
    unbounded_count = 0
    for key, value in data["characteristic-dms"].items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise RulesDataError(f"characteristic-dms.{key!r} must be an integer")
        range_match = _BAND_RANGE.match(key)
        unbounded_match = _BAND_UNBOUNDED.match(key)
        if range_match:
            minimum, maximum = int(range_match.group(1)), int(range_match.group(2))
        elif unbounded_match:
            minimum, maximum = int(unbounded_match.group(1)), None
            unbounded_count += 1
        else:
            raise RulesDataError(f"malformed characteristic band key: {key!r}")
        bands.append(Band(minimum=minimum, maximum=maximum, dm=value))
    if unbounded_count != 1:
        raise RulesDataError(
            f"exactly one characteristic band must be unbounded, found {unbounded_count}"
        )
    bands.sort(key=lambda band: band.minimum)

    return TaskParameters(
        roll=roll,
        target=target,
        unskilled_dm=unskilled_dm,
        difficulty_dms=difficulty_dms,
        characteristic_bands=tuple(bands),
    )


@cache
def load_task_parameters() -> TaskParameters:
    """Read the packaged `tasks.toml` through `importlib.resources` and parse it.

    Performs no filesystem search (FR-023). Cached because the file never
    changes within a process; tests that exercise this function must call
    `load_task_parameters.cache_clear()` afterwards.
    """
    try:
        text = resources.files("cetools.data").joinpath("tasks.toml").read_text(encoding="utf-8")
    except OSError as exc:
        raise RulesDataError(f"could not read packaged tasks.toml: {exc}") from exc
    return _task_parameters_from_toml(text)
