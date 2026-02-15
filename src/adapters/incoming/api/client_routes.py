"""Client-facing REST API routes for parking reservations.

Handles reservation CRUD, availability checks, and chat interactions
for regular (non-admin) users.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from src.adapters.incoming.api.schemas import (
    AvailabilityRequest,
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    CreateReservationRequest,
    ParkingSpaceResponse,
    ReservationResponse,
)
from src.config import dependencies
from src.core.domain.exceptions import DomainError
from src.core.domain.models import ParkingSpace, Reservation, TimeSlot, UserRole

router = APIRouter(tags=["client"])


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
    from src.core.domain.exceptions import (
        AuthorizationError,
        InvalidReservationError,
        ReservationConflictError,
        ReservationNotFoundError,
        SpaceNotAvailableError,
        SpaceNotFoundError,
    )

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


# ── Reservation Endpoints ─────────────────────────────────────────


@router.post(
    "/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
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


# ── Availability Endpoints ────────────────────────────────────────


@router.post(
    "/availability",
    response_model=list[ParkingSpaceResponse],
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


@router.get(
    "/spaces",
    response_model=list[ParkingSpaceResponse],
)
def list_spaces() -> list[ParkingSpaceResponse]:
    """List all parking spaces (read-only for clients)."""
    logger.debug("API list_spaces (client)")
    usecase = dependencies.get_manage_parking_spaces_usecase()
    spaces = usecase.get_all_spaces()
    return [_space_to_response(s) for s in spaces]


# ── Chat Endpoints (Session-Based) ───────────────────────────────


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a message to the parking reservation chatbot.

    Uses backend-managed conversation sessions. The server maintains
    the full conversation history; the client only tracks the session_id.

    If session_id is omitted or null, a new session is created automatically.
    """
    try:
        role = UserRole(request.user_role)
    except ValueError:
        logger.error("API chat: invalid user role '{}'", request.user_role)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid user role: {request.user_role}. Use 'client' or 'admin'."
            ),
        ) from None

    chat_service = dependencies.get_chat_conversation_service()
    chat_deps = dependencies.get_chat_deps(request.user_id, role)

    # Get or create session
    session = chat_service.get_or_create_session(
        request.session_id, request.user_id, role
    )

    logger.debug(
        "API chat: user={}, role={}, session={}, message='{}'",
        request.user_id,
        role.value,
        session.session_id,
        request.message[:100],
    )

    try:
        response, session_id = await chat_service.send_message(
            session.session_id, request.message, chat_deps
        )
        logger.debug("API chat: response length={}", len(response))
        return ChatResponse(
            response=response,
            session_id=session_id,
            user_id=request.user_id,
        )
    except Exception as e:
        logger.exception("API chat: chatbot error: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot error: {e}",
        ) from e


@router.post(
    "/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_session(
    user_id: UUID,
    user_role: str = "client",
) -> ChatSessionResponse:
    """Create a new chat session explicitly.

    Most clients can skip this — POST /chat creates a session
    automatically when session_id is omitted.
    """
    try:
        role = UserRole(user_role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user role: {user_role}.",
        ) from None

    chat_service = dependencies.get_chat_conversation_service()
    session = chat_service.get_or_create_session(None, user_id, role)
    logger.info("API: created chat session={}", session.session_id)
    return ChatSessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        created_at=session.created_at,
    )


@router.delete(
    "/chat/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_chat_session(session_id: UUID) -> None:
    """Delete a chat session and its conversation history."""
    logger.debug("API: deleting chat session={}", session_id)
    chat_service = dependencies.get_chat_conversation_service()
    chat_service.delete_session(session_id)
