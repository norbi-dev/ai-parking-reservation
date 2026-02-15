"""Admin-facing REST API routes for parking reservations.

Handles reservation approval/rejection and parking space management.
These endpoints are intended for administrator access only.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from src.adapters.incoming.api.schemas import (
    AdminActionRequest,
    ParkingSpaceRequest,
    ParkingSpaceResponse,
    ReservationResponse,
)
from src.config import dependencies
from src.core.domain.exceptions import (
    AuthorizationError,
    DomainError,
    InvalidReservationError,
    ReservationConflictError,
    ReservationNotFoundError,
    SpaceNotAvailableError,
    SpaceNotFoundError,
)
from src.core.domain.models import ParkingSpace, Reservation

router = APIRouter(tags=["admin"])


def _reservation_to_response(reservation: Reservation) -> ReservationResponse:
    """Convert a domain Reservation to an API response.

    Args:
        reservation: Domain reservation model

    Returns:
        API response model
    """
    return ReservationResponse(
        reservation_id=reservation.reservation_id,
        user_id=reservation.user_id,
        space_id=reservation.space_id,
        status=reservation.status.value,
        start_time=reservation.time_slot.start_time,
        end_time=reservation.time_slot.end_time,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
        admin_notes=reservation.admin_notes,
    )


def _space_to_response(space: ParkingSpace) -> ParkingSpaceResponse:
    """Convert a domain ParkingSpace to an API response.

    Args:
        space: Domain parking space model

    Returns:
        API response model
    """
    return ParkingSpaceResponse(
        space_id=space.space_id,
        location=space.location,
        is_available=space.is_available,
        hourly_rate=space.hourly_rate,
        space_type=space.space_type,
    )


def _handle_domain_error(error: DomainError) -> HTTPException:
    """Map domain exceptions to HTTP exceptions.

    Args:
        error: Domain exception

    Returns:
        Appropriate HTTPException
    """
    status_map: dict[type, int] = {
        SpaceNotFoundError: status.HTTP_404_NOT_FOUND,
        ReservationNotFoundError: status.HTTP_404_NOT_FOUND,
        SpaceNotAvailableError: status.HTTP_409_CONFLICT,
        ReservationConflictError: status.HTTP_409_CONFLICT,
        InvalidReservationError: status.HTTP_409_CONFLICT,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
    }
    http_status = status_map.get(type(error), status.HTTP_400_BAD_REQUEST)
    logger.error(
        "Domain error → HTTP {}: {} ({})",
        http_status,
        error,
        type(error).__name__,
    )
    return HTTPException(status_code=http_status, detail=str(error))


# ── Reservation Approval Endpoints ───────────────────────────────


@router.get(
    "/reservations/pending",
    response_model=list[ReservationResponse],
)
def get_pending_reservations() -> list[ReservationResponse]:
    """Get all reservations pending admin approval."""
    logger.debug("API get_pending_reservations")
    usecase = dependencies.get_admin_approval_usecase()
    reservations = usecase.get_pending_reservations()
    return [_reservation_to_response(r) for r in reservations]


@router.post(
    "/reservations/{reservation_id}/approve",
    response_model=ReservationResponse,
)
def approve_reservation(
    reservation_id: UUID,
    request: AdminActionRequest | None = None,
) -> ReservationResponse:
    """Approve a pending reservation."""
    logger.debug("API approve_reservation: id={}", reservation_id)
    try:
        admin_notes = request.admin_notes if request else ""
        usecase = dependencies.get_admin_approval_usecase()
        reservation = usecase.approve_reservation(reservation_id, admin_notes)
        return _reservation_to_response(reservation)
    except DomainError as e:
        raise _handle_domain_error(e) from e


@router.post(
    "/reservations/{reservation_id}/reject",
    response_model=ReservationResponse,
)
def reject_reservation(
    reservation_id: UUID,
    request: AdminActionRequest | None = None,
) -> ReservationResponse:
    """Reject a pending reservation."""
    logger.debug("API reject_reservation: id={}", reservation_id)
    try:
        admin_notes = request.admin_notes if request else ""
        usecase = dependencies.get_admin_approval_usecase()
        reservation = usecase.reject_reservation(reservation_id, admin_notes)
        return _reservation_to_response(reservation)
    except DomainError as e:
        raise _handle_domain_error(e) from e


# ── Parking Space Management Endpoints ───────────────────────────


@router.get(
    "/spaces",
    response_model=list[ParkingSpaceResponse],
)
def get_all_spaces() -> list[ParkingSpaceResponse]:
    """Get all parking spaces (admin view)."""
    logger.debug("API get_all_spaces (admin)")
    usecase = dependencies.get_manage_parking_spaces_usecase()
    spaces = usecase.get_all_spaces()
    return [_space_to_response(s) for s in spaces]


@router.post(
    "/spaces",
    response_model=ParkingSpaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_space(request: ParkingSpaceRequest) -> ParkingSpaceResponse:
    """Add a new parking space."""
    logger.debug(
        "API add_space: id={}, location={}", request.space_id, request.location
    )
    space = ParkingSpace(
        space_id=request.space_id,
        location=request.location,
        is_available=request.is_available,
        hourly_rate=request.hourly_rate,
        space_type=request.space_type,
    )
    usecase = dependencies.get_manage_parking_spaces_usecase()
    created = usecase.add_space(space)
    return _space_to_response(created)


@router.put(
    "/spaces/{space_id}",
    response_model=ParkingSpaceResponse,
)
def update_space(space_id: str, request: ParkingSpaceRequest) -> ParkingSpaceResponse:
    """Update an existing parking space."""
    logger.debug("API update_space: id={}", space_id)
    try:
        space = ParkingSpace(
            space_id=space_id,
            location=request.location,
            is_available=request.is_available,
            hourly_rate=request.hourly_rate,
            space_type=request.space_type,
        )
        usecase = dependencies.get_manage_parking_spaces_usecase()
        updated = usecase.update_space(space)
        return _space_to_response(updated)
    except DomainError as e:
        raise _handle_domain_error(e) from e


@router.delete(
    "/spaces/{space_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_space(space_id: str) -> None:
    """Remove a parking space."""
    logger.debug("API remove_space: id={}", space_id)
    try:
        usecase = dependencies.get_manage_parking_spaces_usecase()
        usecase.remove_space(space_id)
    except DomainError as e:
        raise _handle_domain_error(e) from e
