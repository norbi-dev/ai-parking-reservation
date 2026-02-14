"""Use case implementation for administrator reservation approval."""

from uuid import UUID

from loguru import logger

from src.core.domain.exceptions import ReservationNotFoundError
from src.core.domain.models import Reservation, ReservationStatus
from src.core.ports.outgoing.repositories import ReservationRepository


class AdminApprovalService:
    """Service that handles administrator reservation approval.

    Implements the human-in-the-loop pattern where reservations
    require administrator approval before being confirmed.
    """

    def __init__(self, reservation_repo: ReservationRepository) -> None:
        self._reservation_repo = reservation_repo

    def get_pending_reservations(self) -> list[Reservation]:
        """Get all reservations pending admin approval.

        Returns:
            List of pending reservations
        """
        logger.debug("AdminApproval: get_pending_reservations")
        pending = self._reservation_repo.find_by_status(ReservationStatus.PENDING)
        logger.debug("AdminApproval: found {} pending reservation(s)", len(pending))
        return pending

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
        logger.debug("AdminApproval: approve reservation={}", reservation_id)
        reservation = self._reservation_repo.find_by_id(reservation_id)
        if reservation is None:
            logger.error("AdminApproval: reservation {} not found", reservation_id)
            raise ReservationNotFoundError(f"Reservation {reservation_id} not found")

        reservation.approve(admin_notes)
        updated = self._reservation_repo.update(reservation)
        logger.debug("AdminApproval: reservation {} approved", reservation_id)
        return updated

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
        logger.debug("AdminApproval: reject reservation={}", reservation_id)
        reservation = self._reservation_repo.find_by_id(reservation_id)
        if reservation is None:
            logger.error("AdminApproval: reservation {} not found", reservation_id)
            raise ReservationNotFoundError(f"Reservation {reservation_id} not found")

        reservation.reject(admin_notes)
        updated = self._reservation_repo.update(reservation)
        logger.debug("AdminApproval: reservation {} rejected", reservation_id)
        return updated
