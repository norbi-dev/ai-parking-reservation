"""Domain exceptions for the parking reservation system."""


class DomainError(Exception):
    """Base exception for domain-level errors."""


class SpaceNotAvailableError(DomainError):
    """Raised when a parking space is not available for the requested time slot."""


class ReservationNotFoundError(DomainError):
    """Raised when a reservation cannot be found."""


class SpaceNotFoundError(DomainError):
    """Raised when a parking space cannot be found."""


class UserNotFoundError(DomainError):
    """Raised when a user cannot be found."""


class InvalidReservationError(DomainError):
    """Raised when a reservation state transition is invalid."""


class ReservationConflictError(DomainError):
    """Raised when a reservation conflicts with an existing one."""


class AuthorizationError(DomainError):
    """Raised when a user does not have permission to perform an action."""
