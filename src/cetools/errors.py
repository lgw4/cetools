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
