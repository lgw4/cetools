class CetoolsError(Exception):
    """Base class for every error the cetools library raises.

    The library never prints or exits; it only raises. Callers (chiefly
    ``cli.py``) catch this base class at a single site.
    """


class DiceError(CetoolsError):
    """Invalid dice notation, or a die/dice count or side count below 1."""


class RulesDataError(CetoolsError):
    """The packaged rules data file is missing, unreadable, malformed, or
    incomplete, with no fallback to built-in values.
    """


class TaskError(CetoolsError):
    """An unknown difficulty name, or a negative characteristic or skill."""
