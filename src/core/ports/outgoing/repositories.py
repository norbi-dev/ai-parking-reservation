"""Outgoing port interfaces for the parking reservation system.

These define the infrastructure contracts that use cases depend on.
Adapters (repositories, external services) implement these interfaces.
"""

from typing import Protocol
from uuid import UUID

from src.core.domain.models import (
    ConversationSession,
    ParkingSpace,
    Reservation,
    ReservationStatus,
    TimeSlot,
    User,
)


class ReservationRepository(Protocol):
    """Repository interface for reservation persistence."""

    def save(self, reservation: Reservation) -> Reservation:
        """Save a reservation.

        Args:
            reservation: Reservation to save

        Returns:
            The saved reservation
        """
        ...

    def find_by_id(self, reservation_id: UUID) -> Reservation | None:
        """Find a reservation by its ID.

        Args:
            reservation_id: Reservation identifier

        Returns:
            The reservation if found, None otherwise
        """
        ...

    def find_by_user_id(
        self, user_id: UUID, status: ReservationStatus | None = None
    ) -> list[Reservation]:
        """Find all reservations for a user.

        Args:
            user_id: User identifier
            status: Optional status filter

        Returns:
            List of matching reservations
        """
        ...

    def find_by_status(self, status: ReservationStatus) -> list[Reservation]:
        """Find all reservations with a given status.

        Args:
            status: Status to filter by

        Returns:
            List of matching reservations
        """
        ...

    def find_by_space_and_time(
        self, space_id: str, time_slot: TimeSlot
    ) -> list[Reservation]:
        """Find reservations that overlap with the given space and time slot.

        Args:
            space_id: Parking space identifier
            time_slot: Time period to check

        Returns:
            List of overlapping reservations (active ones only)
        """
        ...

    def update(self, reservation: Reservation) -> Reservation:
        """Update an existing reservation.

        Args:
            reservation: Reservation with updated data

        Returns:
            The updated reservation
        """
        ...

    def delete(self, reservation_id: UUID) -> None:
        """Delete a reservation.

        Args:
            reservation_id: Reservation identifier
        """
        ...


class ParkingSpaceRepository(Protocol):
    """Repository interface for parking space persistence."""

    def save(self, space: ParkingSpace) -> ParkingSpace:
        """Save a parking space.

        Args:
            space: Parking space to save

        Returns:
            The saved parking space
        """
        ...

    def find_by_id(self, space_id: str) -> ParkingSpace | None:
        """Find a parking space by its ID.

        Args:
            space_id: Space identifier

        Returns:
            The parking space if found, None otherwise
        """
        ...

    def find_all(self) -> list[ParkingSpace]:
        """Find all parking spaces.

        Returns:
            List of all parking spaces
        """
        ...

    def find_available(self) -> list[ParkingSpace]:
        """Find all available parking spaces.

        Returns:
            List of available parking spaces
        """
        ...

    def update(self, space: ParkingSpace) -> ParkingSpace:
        """Update a parking space.

        Args:
            space: Parking space with updated data

        Returns:
            The updated parking space
        """
        ...

    def delete(self, space_id: str) -> None:
        """Delete a parking space.

        Args:
            space_id: Space identifier
        """
        ...


class UserRepository(Protocol):
    """Repository interface for user persistence."""

    def save(self, user: User) -> User:
        """Save a user.

        Args:
            user: User to save

        Returns:
            The saved user
        """
        ...

    def find_by_id(self, user_id: UUID) -> User | None:
        """Find a user by ID.

        Args:
            user_id: User identifier

        Returns:
            The user if found, None otherwise
        """
        ...

    def find_by_username(self, username: str) -> User | None:
        """Find a user by username.

        Args:
            username: Username to search for

        Returns:
            The user if found, None otherwise
        """
        ...


class ConversationSessionRepository(Protocol):
    """Repository interface for conversation session persistence."""

    def save(self, session: ConversationSession) -> ConversationSession:
        """Save a conversation session.

        Args:
            session: Conversation session to save

        Returns:
            The saved session
        """
        ...

    def find_by_id(self, session_id: UUID) -> ConversationSession | None:
        """Find a conversation session by its ID.

        Args:
            session_id: Session identifier

        Returns:
            The session if found, None otherwise
        """
        ...

    def find_by_user_id(self, user_id: UUID) -> list[ConversationSession]:
        """Find all conversation sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of sessions for the user
        """
        ...

    def update(self, session: ConversationSession) -> ConversationSession:
        """Update an existing conversation session.

        Args:
            session: Session with updated data

        Returns:
            The updated session
        """
        ...

    def delete(self, session_id: UUID) -> None:
        """Delete a conversation session.

        Args:
            session_id: Session identifier
        """
        ...
