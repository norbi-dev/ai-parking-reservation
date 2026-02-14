"""Incoming port interfaces for the parking reservation system.

These define the use case contracts that the application exposes.
Adapters (API, UI) call these interfaces.
"""

from typing import Protocol
from uuid import UUID

from src.core.domain.models import (
    ParkingSpace,
    Reservation,
    ReservationStatus,
    TimeSlot,
)


class ReserveParkingUseCase(Protocol):
    """Use case interface for creating parking reservations.

    This is the primary use case for users to reserve a parking space.
    """

    def execute(self, user_id: UUID, space_id: str, time_slot: TimeSlot) -> Reservation:
        """Create a new parking reservation.

        Args:
            user_id: User making the reservation
            space_id: Parking space identifier
            time_slot: Requested time period

        Returns:
            Reservation with ID and pending status

        Raises:
            SpaceNotAvailableError: If space is not available
            SpaceNotFoundError: If space does not exist
        """
        ...


class CheckAvailabilityUseCase(Protocol):
    """Use case interface for checking parking space availability."""

    def execute(self, time_slot: TimeSlot) -> list[ParkingSpace]:
        """Get all available parking spaces for a given time slot.

        Args:
            time_slot: Time period to check availability for

        Returns:
            List of available parking spaces
        """
        ...

    def is_space_available(self, space_id: str, time_slot: TimeSlot) -> bool:
        """Check if a specific parking space is available.

        Args:
            space_id: Parking space identifier
            time_slot: Time period to check

        Returns:
            True if the space is available for the given time slot
        """
        ...


class ManageReservationsUseCase(Protocol):
    """Use case interface for managing user reservations."""

    def get_user_reservations(
        self, user_id: UUID, status: ReservationStatus | None = None
    ) -> list[Reservation]:
        """Get all reservations for a user, optionally filtered by status.

        Args:
            user_id: User identifier
            status: Optional status filter

        Returns:
            List of reservations
        """
        ...

    def cancel_reservation(self, reservation_id: UUID, user_id: UUID) -> Reservation:
        """Cancel a reservation.

        Args:
            reservation_id: Reservation to cancel
            user_id: User requesting cancellation

        Returns:
            Updated reservation with cancelled status

        Raises:
            ReservationNotFoundError: If reservation does not exist
            AuthorizationError: If user is not the owner
        """
        ...

    def get_reservation(self, reservation_id: UUID) -> Reservation:
        """Get a specific reservation by ID.

        Args:
            reservation_id: Reservation identifier

        Returns:
            The reservation

        Raises:
            ReservationNotFoundError: If reservation does not exist
        """
        ...


class AdminApprovalUseCase(Protocol):
    """Use case interface for administrator reservation approval."""

    def get_pending_reservations(self) -> list[Reservation]:
        """Get all reservations pending admin approval.

        Returns:
            List of pending reservations
        """
        ...

    def approve_reservation(
        self, reservation_id: UUID, admin_notes: str = ""
    ) -> Reservation:
        """Approve a pending reservation.

        Args:
            reservation_id: Reservation to approve
            admin_notes: Optional notes from the administrator

        Returns:
            Updated reservation with confirmed status

        Raises:
            ReservationNotFoundError: If reservation does not exist
        """
        ...

    def reject_reservation(
        self, reservation_id: UUID, admin_notes: str = ""
    ) -> Reservation:
        """Reject a pending reservation.

        Args:
            reservation_id: Reservation to reject
            admin_notes: Optional notes from the administrator

        Returns:
            Updated reservation with rejected status

        Raises:
            ReservationNotFoundError: If reservation does not exist
        """
        ...


class ManageParkingSpacesUseCase(Protocol):
    """Use case interface for managing parking spaces (admin)."""

    def add_space(self, space: ParkingSpace) -> ParkingSpace:
        """Add a new parking space.

        Args:
            space: Parking space to add

        Returns:
            The created parking space
        """
        ...

    def update_space(self, space: ParkingSpace) -> ParkingSpace:
        """Update an existing parking space.

        Args:
            space: Parking space with updated data

        Returns:
            The updated parking space

        Raises:
            SpaceNotFoundError: If space does not exist
        """
        ...

    def remove_space(self, space_id: str) -> None:
        """Remove a parking space.

        Args:
            space_id: Space identifier to remove

        Raises:
            SpaceNotFoundError: If space does not exist
        """
        ...

    def get_all_spaces(self) -> list[ParkingSpace]:
        """Get all parking spaces.

        Returns:
            List of all parking spaces
        """
        ...
