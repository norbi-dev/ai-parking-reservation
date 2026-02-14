"""Use case implementation for administrator reservation approval."""

from uuid import UUID

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
        return self._reservation_repo.find_by_status(ReservationStatus.PENDING)

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
        reservation = self._reservation_repo.find_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(f"Reservation {reservation_id} not found")

        reservation.approve(admin_notes)
        return self._reservation_repo.update(reservation)

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
        reservation = self._reservation_repo.find_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(f"Reservation {reservation_id} not found")

        reservation.reject(admin_notes)
        return self._reservation_repo.update(reservation)
