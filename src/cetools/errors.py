from dataclasses import dataclass


class CetoolsError(Exception):
    """Base class for every error the cetools library raises.

    The library never prints or exits; it only raises. Callers (chiefly
    ``cli.py``) catch this base class at a single site.

    Raised directly only by the ``render`` dispatch fallbacks, where no leaf
    below describes the condition; see ``as_text`` for why that path does not
    get a leaf of its own.
    """


class DiceError(CetoolsError):
    """Invalid dice notation, a die/dice count or side count below 1, or a
    notation or seed of an unsupported type.
    """


_TOML_TYPE_NAMES = {
    bool: "a boolean",
    int: "an integer",
    float: "a number",
    str: "a string",
    list: "an array",
    dict: "a table",
}


def type_name(value: object) -> str:
    """Name a value's type the way the data files spell it, for the `found`
    half of a type problem (FR-020b).

    The rest of a problem line is TOML's vocabulary in English -- "a [task]
    table", "an empty array", "a non-empty string" -- so a bare Python type
    name was the one word in a report that named the implementation rather
    than the file the author is looking at, and `dict` and `list` are not
    words TOML uses at all. Settled here rather than at each site so the
    three schema modules cannot drift apart.

    Keyed on the exact type, which is what keeps `bool` from answering as an
    integer it subclasses. Anything unmapped falls back to the Python name
    rather than guessing: TOML's date and time types reach no field in this
    schema, and inventing a word for them would be worse than saying which
    type was actually seen.
    """
    return _TOML_TYPE_NAMES.get(type(value), type(value).__name__)


@dataclass(frozen=True, slots=True, order=True)
class ValidationProblem:
    """One thing wrong with one rules data file.

    Sorts by ``(file, location)`` so a report is stable run to run.
    ``location`` is a dotted key path with array indices, and is the empty
    string for a problem about the file as a whole (an unreadable file, a
    missing header) rather than an optional field: every problem has a
    location, and the file-as-a-whole location is simply empty.
    """

    file: str
    location: str = ""
    found: str = ""
    expected: str = ""


@dataclass
class RulesDataError(CetoolsError):
    """The packaged rules data file is missing, unreadable, malformed, or
    incomplete, with no fallback to built-in values.

    Retains its message-only constructor because ``tasks.py`` raises this
    type for runtime invariant failures (a characteristic score no band
    covers) that are not data-file problems and carry no location.
    """

    message: str
    problems: tuple[ValidationProblem, ...] = ()

    def __post_init__(self) -> None:
        self.problems = tuple(self.problems)
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class TaskError(CetoolsError):
    """An unknown difficulty name, or a negative characteristic or skill."""
