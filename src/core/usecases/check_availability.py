"""Use case implementation for checking parking space availability."""

from loguru import logger

from src.core.domain.models import ParkingSpace, ReservationStatus, TimeSlot
from src.core.ports.outgoing.repositories import (
    ParkingSpaceRepository,
    ReservationRepository,
)


class CheckAvailabilityService:
    """Service that handles parking space availability checks.

    Checks both space status and existing reservations to determine
    true availability for a given time slot.
    """

    def __init__(
        self,
        reservation_repo: ReservationRepository,
        space_repo: ParkingSpaceRepository,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._space_repo = space_repo

    def execute(self, time_slot: TimeSlot) -> list[ParkingSpace]:
        """Get all available parking spaces for a given time slot.

        Args:
            time_slot: Time period to check availability for

        Returns:
            List of available parking spaces with no active conflicts
        """
        logger.debug(
            "CheckAvailability: slot={}–{}",
            time_slot.start_time,
            time_slot.end_time,
        )
        all_spaces = self._space_repo.find_available()
        available = []

        for space in all_spaces:
            if self.is_space_available(space.space_id, time_slot):
                available.append(space)

        logger.debug(
            "CheckAvailability: {}/{} spaces available",
            len(available),
            len(all_spaces),
        )
        return available

    def is_space_available(self, space_id: str, time_slot: TimeSlot) -> bool:
        """Check if a specific parking space is available.

        Args:
            space_id: Parking space identifier
            time_slot: Time period to check

        Returns:
            True if the space is available for the given time slot
        """
        space = self._space_repo.find_by_id(space_id)
        if space is None or not space.is_available:
            return False

        conflicting = self._reservation_repo.find_by_space_and_time(space_id, time_slot)
        active_conflicts = [
            r
            for r in conflicting
            if r.status in (ReservationStatus.PENDING, ReservationStatus.CONFIRMED)
        ]
        return len(active_conflicts) == 0
