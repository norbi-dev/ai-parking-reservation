"""Domain models for the parking reservation system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from src.core.domain.exceptions import InvalidReservationError


class ReservationStatus(Enum):
    """Status of a parking reservation."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class UserRole(Enum):
    """Role of a user in the system."""

    CLIENT = "client"
    ADMIN = "admin"


@dataclass(frozen=True)
class TimeSlot:
    """Value object representing a time period for a reservation.

    Args:
        start_time: Start of the reservation period
        end_time: End of the reservation period
    """

    start_time: datetime
    end_time: datetime

    def __post_init__(self) -> None:
        """Validate that end_time is after start_time."""
        if self.end_time <= self.start_time:
            msg = "end_time must be after start_time"
            raise ValueError(msg)

    @property
    def duration_hours(self) -> float:
        """Calculate duration in hours."""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600


@dataclass
class ParkingSpace:
    """Domain model representing a parking space.

    Args:
        space_id: Unique identifier for the parking space
        location: Physical location description
        is_available: Whether the space is currently available
        hourly_rate: Cost per hour in currency units
        space_type: Type of parking space (e.g., standard, handicap, electric)
    """

    space_id: str
    location: str
    is_available: bool = True
    hourly_rate: float = 5.0
    space_type: str = "standard"


@dataclass
class User:
    """Domain model representing a user.

    Args:
        user_id: Unique identifier for the user
        username: Login username
        email: User email address
        role: User role (client or admin)
        full_name: User's full name
    """

    user_id: UUID = field(default_factory=uuid4)
    username: str = ""
    email: str = ""
    role: UserRole = UserRole.CLIENT
    full_name: str = ""


@dataclass
class Reservation:
    """Domain model representing a parking reservation.

    This orchestrates: check availability → create reservation → await approval
    → notify user.

    Args:
        reservation_id: Unique identifier for the reservation
        user_id: ID of the user who made the reservation
        space_id: ID of the reserved parking space
        time_slot: Time period of the reservation
        status: Current status of the reservation
        created_at: When the reservation was created
        updated_at: When the reservation was last updated
        admin_notes: Notes from the administrator
    """

    user_id: UUID
    space_id: str
    time_slot: TimeSlot
    reservation_id: UUID = field(default_factory=uuid4)
    status: ReservationStatus = ReservationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    admin_notes: str = ""

    def approve(self, admin_notes: str = "") -> None:
        """Approve the reservation.

        Args:
            admin_notes: Optional notes from the administrator

        Raises:
            InvalidReservationError: If the reservation is not in pending status
        """
        if self.status != ReservationStatus.PENDING:
            msg = f"Cannot approve reservation with status {self.status.value}"
            raise InvalidReservationError(msg)
        self.status = ReservationStatus.CONFIRMED
        self.admin_notes = admin_notes
        self.updated_at = datetime.now()

    def reject(self, admin_notes: str = "") -> None:
        """Reject the reservation.

        Args:
            admin_notes: Optional notes from the administrator

        Raises:
            InvalidReservationError: If the reservation is not in pending status
        """
        if self.status != ReservationStatus.PENDING:
            msg = f"Cannot reject reservation with status {self.status.value}"
            raise InvalidReservationError(msg)
        self.status = ReservationStatus.REJECTED
        self.admin_notes = admin_notes
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """Cancel the reservation.

        Raises:
            InvalidReservationError: If the reservation is already rejected or cancelled
        """
        if self.status in (ReservationStatus.REJECTED, ReservationStatus.CANCELLED):
            msg = f"Cannot cancel reservation with status {self.status.value}"
            raise InvalidReservationError(msg)
        self.status = ReservationStatus.CANCELLED
        self.updated_at = datetime.now()

    @property
    def total_cost(self) -> float:
        """Calculate the total cost based on duration and hourly rate.

        Note: This requires the parking space hourly rate to be provided
        externally. Returns 0.0 as a placeholder.
        """
        return 0.0
