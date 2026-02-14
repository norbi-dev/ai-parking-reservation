"""In-memory repository implementations for development and testing."""

from uuid import UUID

from loguru import logger

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
        logger.debug("InMemoryDB: save reservation={}", reservation.reservation_id)
        self._reservations[reservation.reservation_id] = reservation
        return reservation

    def find_by_id(self, reservation_id: UUID) -> Reservation | None:
        """Find a reservation by its ID.

        Args:
            reservation_id: Reservation identifier

        Returns:
            The reservation if found, None otherwise
        """
        logger.debug("InMemoryDB: find reservation by id={}", reservation_id)
        result = self._reservations.get(reservation_id)
        if result is None:
            logger.debug("InMemoryDB: reservation {} not found", reservation_id)
        return result

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
        logger.debug("InMemoryDB: find reservations by user={}", user_id)
        results = [r for r in self._reservations.values() if r.user_id == user_id]
        if status is not None:
            results = [r for r in results if r.status == status]
        logger.debug(
            "InMemoryDB: found {} reservation(s) for user={}",
            len(results),
            user_id,
        )
        return results

    def find_by_status(self, status: ReservationStatus) -> list[Reservation]:
        """Find all reservations with a given status.

        Args:
            status: Status to filter by

        Returns:
            List of matching reservations
        """
        logger.debug("InMemoryDB: find reservations by status={}", status.value)
        results = [r for r in self._reservations.values() if r.status == status]
        logger.debug(
            "InMemoryDB: found {} reservation(s) with status={}",
            len(results),
            status.value,
        )
        return results

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
        logger.debug(
            "InMemoryDB: find overlapping reservations space={}, slot={}–{}",
            space_id,
            time_slot.start_time,
            time_slot.end_time,
        )
        results = []
        for reservation in self._reservations.values():
            if reservation.space_id != space_id:
                continue
            if self._time_slots_overlap(reservation.time_slot, time_slot):
                results.append(reservation)
        logger.debug("InMemoryDB: found {} overlapping reservation(s)", len(results))
        return results

    def update(self, reservation: Reservation) -> Reservation:
        """Update an existing reservation.

        Args:
            reservation: Reservation with updated data

        Returns:
            The updated reservation
        """
        logger.debug("InMemoryDB: update reservation={}", reservation.reservation_id)
        self._reservations[reservation.reservation_id] = reservation
        return reservation

    def delete(self, reservation_id: UUID) -> None:
        """Delete a reservation.

        Args:
            reservation_id: Reservation identifier
        """
        logger.debug("InMemoryDB: delete reservation={}", reservation_id)
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
        logger.debug("InMemoryDB: save space={}", space.space_id)
        self._spaces[space.space_id] = space
        return space

    def find_by_id(self, space_id: str) -> ParkingSpace | None:
        """Find a parking space by its ID.

        Args:
            space_id: Space identifier

        Returns:
            The parking space if found, None otherwise
        """
        logger.debug("InMemoryDB: find space by id={}", space_id)
        return self._spaces.get(space_id)

    def find_all(self) -> list[ParkingSpace]:
        """Find all parking spaces.

        Returns:
            List of all parking spaces
        """
        logger.debug("InMemoryDB: find_all spaces")
        spaces = list(self._spaces.values())
        logger.debug("InMemoryDB: found {} space(s)", len(spaces))
        return spaces

    def find_available(self) -> list[ParkingSpace]:
        """Find all available parking spaces.

        Returns:
            List of available parking spaces
        """
        logger.debug("InMemoryDB: find_available spaces")
        available = [s for s in self._spaces.values() if s.is_available]
        logger.debug("InMemoryDB: found {} available space(s)", len(available))
        return available

    def update(self, space: ParkingSpace) -> ParkingSpace:
        """Update a parking space.

        Args:
            space: Parking space with updated data

        Returns:
            The updated parking space
        """
        logger.debug("InMemoryDB: update space={}", space.space_id)
        self._spaces[space.space_id] = space
        return space

    def delete(self, space_id: str) -> None:
        """Delete a parking space.

        Args:
            space_id: Space identifier
        """
        logger.debug("InMemoryDB: delete space={}", space_id)
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
        logger.debug("InMemoryDB: save user={}", user.user_id)
        self._users[user.user_id] = user
        return user

    def find_by_id(self, user_id: UUID) -> User | None:
        """Find a user by ID.

        Args:
            user_id: User identifier

        Returns:
            The user if found, None otherwise
        """
        logger.debug("InMemoryDB: find user by id={}", user_id)
        return self._users.get(user_id)

    def find_by_username(self, username: str) -> User | None:
        """Find a user by username.

        Args:
            username: Username to search for

        Returns:
            The user if found, None otherwise
        """
        logger.debug("InMemoryDB: find user by username={}", username)
        for user in self._users.values():
            if user.username == username:
                return user
        logger.debug("InMemoryDB: user '{}' not found", username)
        return None
