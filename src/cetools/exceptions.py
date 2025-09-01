"""Custom exception types for cetools."""


class CetoolsError(Exception):
    """Base class for cetools errors."""


class InvalidInputError(CetoolsError):
    """Raised when user input is invalid."""


class NotFoundError(CetoolsError):
    """Raised when a requested resource is not found."""


# This file contains GitHub Copilot generated content.
