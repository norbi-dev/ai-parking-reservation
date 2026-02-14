"""FastAPI REST API router for parking reservation endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from src.adapters.incoming.api.schemas import (
    AdminActionRequest,
    AvailabilityRequest,
    ChatRequest,
    ChatResponse,
    CreateReservationRequest,
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
from src.core.domain.models import ParkingSpace, Reservation, TimeSlot, UserRole

router = APIRouter()


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


# --- Reservation Endpoints ---


@router.post(
    "/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["reservations"],
)
def create_reservation(
    request: CreateReservationRequest,
) -> ReservationResponse:
    """Create a new parking reservation.

    The reservation will be created with pending status and
    requires administrator approval.
    """
    try:
        time_slot = TimeSlot(
            start_time=request.time_slot.start_time,
            end_time=request.time_slot.end_time,
        )
        logger.debug(
            "API create_reservation: user={}, space={}, slot={}–{}",
            request.user_id,
            request.space_id,
            request.time_slot.start_time,
            request.time_slot.end_time,
        )
        usecase = dependencies.get_reserve_parking_usecase()
        reservation = usecase.execute(
            user_id=request.user_id,
            space_id=request.space_id,
            time_slot=time_slot,
        )
        logger.debug(
            "API create_reservation: success, id={}",
            reservation.reservation_id,
        )
        return _reservation_to_response(reservation)
    except DomainError as e:
        raise _handle_domain_error(e) from e


@router.get(
    "/reservations/{reservation_id}",
    response_model=ReservationResponse,
    tags=["reservations"],
)
def get_reservation(reservation_id: UUID) -> ReservationResponse:
    """Get a specific reservation by ID."""
    logger.debug("API get_reservation: id={}", reservation_id)
    try:
        usecase = dependencies.get_manage_reservations_usecase()
        reservation = usecase.get_reservation(reservation_id)
        return _reservation_to_response(reservation)
    except DomainError as e:
        raise _handle_domain_error(e) from e


@router.get(
    "/reservations/user/{user_id}",
    response_model=list[ReservationResponse],
    tags=["reservations"],
)
def get_user_reservations(user_id: UUID) -> list[ReservationResponse]:
    """Get all reservations for a specific user."""
    logger.debug("API get_user_reservations: user={}", user_id)
    usecase = dependencies.get_manage_reservations_usecase()
    reservations = usecase.get_user_reservations(user_id)
    return [_reservation_to_response(r) for r in reservations]


@router.post(
    "/reservations/{reservation_id}/cancel",
    response_model=ReservationResponse,
    tags=["reservations"],
)
def cancel_reservation(reservation_id: UUID, user_id: UUID) -> ReservationResponse:
    """Cancel a reservation."""
    logger.debug("API cancel_reservation: id={}, user={}", reservation_id, user_id)
    try:
        usecase = dependencies.get_manage_reservations_usecase()
        reservation = usecase.cancel_reservation(reservation_id, user_id)
        return _reservation_to_response(reservation)
    except DomainError as e:
        raise _handle_domain_error(e) from e


# --- Availability Endpoints ---


@router.post(
    "/availability",
    response_model=list[ParkingSpaceResponse],
    tags=["availability"],
)
def check_availability(
    request: AvailabilityRequest,
) -> list[ParkingSpaceResponse]:
    """Check available parking spaces for a given time slot."""
    logger.debug(
        "API check_availability: slot={}–{}",
        request.time_slot.start_time,
        request.time_slot.end_time,
    )
    time_slot = TimeSlot(
        start_time=request.time_slot.start_time,
        end_time=request.time_slot.end_time,
    )
    usecase = dependencies.get_check_availability_usecase()
    spaces = usecase.execute(time_slot)
    return [_space_to_response(s) for s in spaces]


# --- Admin Endpoints ---


@router.get(
    "/admin/reservations/pending",
    response_model=list[ReservationResponse],
    tags=["admin"],
)
def get_pending_reservations() -> list[ReservationResponse]:
    """Get all reservations pending admin approval."""
    logger.debug("API get_pending_reservations")
    usecase = dependencies.get_admin_approval_usecase()
    reservations = usecase.get_pending_reservations()
    return [_reservation_to_response(r) for r in reservations]


@router.post(
    "/admin/reservations/{reservation_id}/approve",
    response_model=ReservationResponse,
    tags=["admin"],
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
    "/admin/reservations/{reservation_id}/reject",
    response_model=ReservationResponse,
    tags=["admin"],
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


# --- Parking Space Management Endpoints ---


@router.get(
    "/admin/spaces",
    response_model=list[ParkingSpaceResponse],
    tags=["admin"],
)
def get_all_spaces() -> list[ParkingSpaceResponse]:
    """Get all parking spaces."""
    logger.debug("API get_all_spaces")
    usecase = dependencies.get_manage_parking_spaces_usecase()
    spaces = usecase.get_all_spaces()
    return [_space_to_response(s) for s in spaces]


@router.post(
    "/admin/spaces",
    response_model=ParkingSpaceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["admin"],
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
    "/admin/spaces/{space_id}",
    response_model=ParkingSpaceResponse,
    tags=["admin"],
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
    "/admin/spaces/{space_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["admin"],
)
def remove_space(space_id: str) -> None:
    """Remove a parking space."""
    logger.debug("API remove_space: id={}", space_id)
    try:
        usecase = dependencies.get_manage_parking_spaces_usecase()
        usecase.remove_space(space_id)
    except DomainError as e:
        raise _handle_domain_error(e) from e


# --- Chat Endpoint ---


@router.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a message to the parking reservation chatbot.

    The chatbot can help with checking availability, making reservations,
    viewing reservations, and admin operations.
    """
    from pydantic_ai.messages import (
        ModelMessage,
        ModelRequest,
        ModelResponse,
        TextPart,
        UserPromptPart,
    )

    try:
        role = UserRole(request.user_role)
    except ValueError:
        logger.error("API chat: invalid user role '{}'", request.user_role)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user role: {request.user_role}. Use 'client' or 'admin'.",
        ) from None

    agent = dependencies.get_parking_agent()
    chat_deps = dependencies.get_chat_deps(request.user_id, role)

    logger.debug(
        "API chat: user={}, role={}, message='{}'",
        request.user_id,
        role.value,
        request.message[:100],
    )

    # Build message history from conversation_history
    message_history: list[ModelMessage] = []
    for msg in request.conversation_history:
        if msg.role == "user":
            message_history.append(
                ModelRequest(parts=[UserPromptPart(content=msg.content)])
            )
        elif msg.role == "assistant":
            message_history.append(ModelResponse(parts=[TextPart(content=msg.content)]))

    try:
        result = await agent.run(
            request.message,
            deps=chat_deps,
            message_history=message_history or None,
        )
        logger.debug("API chat: response length={}", len(result.output))
        return ChatResponse(
            response=result.output,
            user_id=request.user_id,
        )
    except Exception as e:
        logger.exception("API chat: chatbot error: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot error: {e}",
        ) from e
