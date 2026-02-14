"""Use case implementation for managing user reservations."""

from uuid import UUID

from loguru import logger

from src.core.domain.exceptions import AuthorizationError, ReservationNotFoundError
from src.core.domain.models import Reservation, ReservationStatus
from src.core.ports.outgoing.repositories import ReservationRepository


class ManageReservationsService:
    """Service that handles user reservation management.

    Allows users to view their reservations, cancel them, and
    check individual reservation details.
    """

    def __init__(self, reservation_repo: ReservationRepository) -> None:
        self._reservation_repo = reservation_repo

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
        logger.debug("ManageReservations: get_user_reservations user={}", user_id)
        reservations = self._reservation_repo.find_by_user_id(user_id, status)
        logger.debug(
            "ManageReservations: found {} reservation(s) for user={}",
            len(reservations),
            user_id,
        )
        return reservations

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
        logger.debug(
            "ManageReservations: cancel reservation={}, user={}",
            reservation_id,
            user_id,
        )
        reservation = self._reservation_repo.find_by_id(reservation_id)
        if reservation is None:
            logger.error("ManageReservations: reservation {} not found", reservation_id)
            raise ReservationNotFoundError(f"Reservation {reservation_id} not found")

        if reservation.user_id != user_id:
            logger.error(
                "ManageReservations: user {} not authorized to cancel {}",
                user_id,
                reservation_id,
            )
            raise AuthorizationError(
                "User is not authorized to cancel this reservation"
            )

        reservation.cancel()
        updated = self._reservation_repo.update(reservation)
        logger.debug("ManageReservations: reservation {} cancelled", reservation_id)
        return updated

    def get_reservation(self, reservation_id: UUID) -> Reservation:
        """Get a specific reservation by ID.

        Args:
            reservation_id: Reservation identifier

        Returns:
            The reservation

        Raises:
            ReservationNotFoundError: If reservation does not exist
        """
        logger.debug("ManageReservations: get_reservation id={}", reservation_id)
        reservation = self._reservation_repo.find_by_id(reservation_id)
        if reservation is None:
            logger.error("ManageReservations: reservation {} not found", reservation_id)
            raise ReservationNotFoundError(f"Reservation {reservation_id} not found")
        return reservation
