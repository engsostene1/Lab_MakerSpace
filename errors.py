#exceptions that will trap errors found in main to avoid system crashes 
class MakerSpaceError(Exception):
    """Base class for all application-specific errors."""
class ValidationError(MakerSpaceError):
    """Raised when user-supplied data fails validation (bad input)."""
class NotFoundError(MakerSpaceError):
    """Raised when a requested member/equipment/loan record does not exist."""
class ConflictError(MakerSpaceError):
    """Raised when an action cannot proceed due to current state
    forexample borrowing equipment that is already borrowed)."""
