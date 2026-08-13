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


class RulesDataError(CetoolsError):
    """The packaged rules data file is missing, unreadable, malformed, or
    incomplete, with no fallback to built-in values.
    """


class TaskError(CetoolsError):
    """An unknown difficulty name, or a negative characteristic or skill."""
