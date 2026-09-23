"""
errors.py
---------
Small custom exception hierarchy so services.py can raise meaningful,
specific errors, and main.py can catch them and show a clean message
to the user instead of a raw traceback / crash.
"""


class MakerSpaceError(Exception):
    """Base class for all application-specific errors."""


class ValidationError(MakerSpaceError):
    """Raised when user-supplied data fails validation (bad input)."""


class NotFoundError(MakerSpaceError):
    """Raised when a requested member/equipment/loan record does not exist."""


class ConflictError(MakerSpaceError):
    """Raised when an action cannot proceed due to current state
    (e.g. borrowing equipment that is already borrowed)."""
