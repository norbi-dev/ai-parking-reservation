"""In-memory repository implementations for development and testing."""

from uuid import UUID

from src.core.domain.models import (
    ParkingSpace,
    Reservation,
    ReservationStatus,
    TimeSlot,
    User,
)


class InMemoryReservationRepository:
    """In-memory implementation of ReservationRepository.

    Stores reservations in a dictionary for development and testing.
    """

    def __init__(self) -> None:
        self._reservations: dict[UUID, Reservation] = {}

    def save(self, reservation: Reservation) -> Reservation:
        """Save a reservation to memory.

        Args:
            reservation: Reservation to save

        Returns:
            The saved reservation
        """
        self._reservations[reservation.reservation_id] = reservation
        return reservation

    def find_by_id(self, reservation_id: UUID) -> Reservation | None:
        """Find a reservation by its ID.

        Args:
            reservation_id: Reservation identifier

        Returns:
            The reservation if found, None otherwise
        """
        return self._reservations.get(reservation_id)

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
        results = [r for r in self._reservations.values() if r.user_id == user_id]
        if status is not None:
            results = [r for r in results if r.status == status]
        return results

    def find_by_status(self, status: ReservationStatus) -> list[Reservation]:
        """Find all reservations with a given status.

        Args:
            status: Status to filter by

        Returns:
            List of matching reservations
        """
        return [r for r in self._reservations.values() if r.status == status]

    def find_by_space_and_time(
        self, space_id: str, time_slot: TimeSlot
    ) -> list[Reservation]:
        """Find reservations that overlap with the given space and time slot.

        Args:
            space_id: Parking space identifier
            time_slot: Time period to check

        Returns:
            List of overlapping reservations
        """
        results = []
        for reservation in self._reservations.values():
            if reservation.space_id != space_id:
                continue
            if self._time_slots_overlap(reservation.time_slot, time_slot):
                results.append(reservation)
        return results

    def update(self, reservation: Reservation) -> Reservation:
        """Update an existing reservation.

        Args:
            reservation: Reservation with updated data

        Returns:
            The updated reservation
        """
        self._reservations[reservation.reservation_id] = reservation
        return reservation

    def delete(self, reservation_id: UUID) -> None:
        """Delete a reservation.

        Args:
            reservation_id: Reservation identifier
        """
        self._reservations.pop(reservation_id, None)

    @staticmethod
    def _time_slots_overlap(slot1: TimeSlot, slot2: TimeSlot) -> bool:
        """Check if two time slots overlap.

        Args:
            slot1: First time slot
            slot2: Second time slot

        Returns:
            True if the time slots overlap
        """
        return slot1.start_time < slot2.end_time and slot2.start_time < slot1.end_time


class InMemoryParkingSpaceRepository:
    """In-memory implementation of ParkingSpaceRepository.

    Stores parking spaces in a dictionary for development and testing.
    """

    def __init__(self) -> None:
        self._spaces: dict[str, ParkingSpace] = {}

    def save(self, space: ParkingSpace) -> ParkingSpace:
        """Save a parking space.

        Args:
            space: Parking space to save

        Returns:
            The saved parking space
        """
        self._spaces[space.space_id] = space
        return space

    def find_by_id(self, space_id: str) -> ParkingSpace | None:
        """Find a parking space by its ID.

        Args:
            space_id: Space identifier

        Returns:
            The parking space if found, None otherwise
        """
        return self._spaces.get(space_id)

    def find_all(self) -> list[ParkingSpace]:
        """Find all parking spaces.

        Returns:
            List of all parking spaces
        """
        return list(self._spaces.values())

    def find_available(self) -> list[ParkingSpace]:
        """Find all available parking spaces.

        Returns:
            List of available parking spaces
        """
        return [s for s in self._spaces.values() if s.is_available]

    def update(self, space: ParkingSpace) -> ParkingSpace:
        """Update a parking space.

        Args:
            space: Parking space with updated data

        Returns:
            The updated parking space
        """
        self._spaces[space.space_id] = space
        return space

    def delete(self, space_id: str) -> None:
        """Delete a parking space.

        Args:
            space_id: Space identifier
        """
        self._spaces.pop(space_id, None)


class InMemoryUserRepository:
    """In-memory implementation of UserRepository.

    Stores users in a dictionary for development and testing.
    """

    def __init__(self) -> None:
        self._users: dict[UUID, User] = {}

    def save(self, user: User) -> User:
        """Save a user.

        Args:
            user: User to save

        Returns:
            The saved user
        """
        self._users[user.user_id] = user
        return user

    def find_by_id(self, user_id: UUID) -> User | None:
        """Find a user by ID.

        Args:
            user_id: User identifier

        Returns:
            The user if found, None otherwise
        """
        return self._users.get(user_id)

    def find_by_username(self, username: str) -> User | None:
        """Find a user by username.

        Args:
            username: Username to search for

        Returns:
            The user if found, None otherwise
        """
        for user in self._users.values():
            if user.username == username:
                return user
        return None
