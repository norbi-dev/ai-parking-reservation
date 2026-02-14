"""Use case implementation for creating parking reservations."""

from uuid import UUID

from loguru import logger

from src.core.domain.exceptions import (
    ReservationConflictError,
    SpaceNotAvailableError,
    SpaceNotFoundError,
)
from src.core.domain.models import Reservation, ReservationStatus, TimeSlot
from src.core.ports.outgoing.repositories import (
    ParkingSpaceRepository,
    ReservationRepository,
)


class ReserveParkingService:
    """Service that handles parking reservation creation.

    This orchestrates: check availability → validate space → create reservation
    with pending status → await admin approval.
    """

    def __init__(
        self,
        reservation_repo: ReservationRepository,
        space_repo: ParkingSpaceRepository,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._space_repo = space_repo

    def execute(self, user_id: UUID, space_id: str, time_slot: TimeSlot) -> Reservation:
        """Create a new parking reservation.

        Args:
            user_id: User making the reservation
            space_id: Parking space identifier
            time_slot: Requested time period

        Returns:
            Reservation with ID and pending status

        Raises:
            SpaceNotFoundError: If the parking space does not exist
            SpaceNotAvailableError: If the space is marked as unavailable
            ReservationConflictError: If the space is already reserved for the time slot
        """
        logger.debug(
            "ReserveParking: user={}, space={}, slot={}–{}",
            user_id,
            space_id,
            time_slot.start_time,
            time_slot.end_time,
        )
        space = self._space_repo.find_by_id(space_id)
        if space is None:
            logger.error("ReserveParking: space {} not found", space_id)
            raise SpaceNotFoundError(f"Parking space {space_id} not found")

        if not space.is_available:
            logger.error("ReserveParking: space {} not available", space_id)
            raise SpaceNotAvailableError(
                f"Space {space_id} is not available for reservations"
            )

        conflicting = self._reservation_repo.find_by_space_and_time(space_id, time_slot)
        active_conflicts = [
            r
            for r in conflicting
            if r.status in (ReservationStatus.PENDING, ReservationStatus.CONFIRMED)
        ]
        if active_conflicts:
            logger.error(
                "ReserveParking: conflict on space {} ({} existing)",
                space_id,
                len(active_conflicts),
            )
            raise ReservationConflictError(
                f"Space {space_id} already has a reservation "
                "for the requested time slot"
            )

        reservation = Reservation(
            user_id=user_id,
            space_id=space_id,
            time_slot=time_slot,
        )

        saved = self._reservation_repo.save(reservation)
        logger.debug(
            "ReserveParking: created reservation={}, status={}",
            saved.reservation_id,
            saved.status.value,
        )
        return saved
