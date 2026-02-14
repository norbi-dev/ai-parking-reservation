"""Pydantic-AI chatbot agent for the parking reservation system.

This adapter wraps the existing use cases as LLM tools, allowing users to
interact with the parking system through natural language conversation.

Tools return JSON strings with a '__widget__' type marker so the Streamlit
UI can detect and render interactive widgets (tables, cards, buttons) inline
in the chat conversation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import UUID

from pydantic_ai import Agent, RunContext

from src.adapters.incoming.streamlit_app.chat_widgets import (
    AllSpacesResponse,
    AvailabilityResponse,
    MyReservationsResponse,
    PendingReservationsResponse,
    ReservationActionResponse,
    ReservationCreatedResponse,
    ReservationInfo,
    SpaceActionResponse,
    SpaceInfo,
)
from src.core.domain.exceptions import DomainError
from src.core.domain.models import ParkingSpace, Reservation, TimeSlot, UserRole
from src.core.usecases.admin_approval import AdminApprovalService
from src.core.usecases.check_availability import CheckAvailabilityService
from src.core.usecases.manage_parking_spaces import ManageParkingSpacesService
from src.core.usecases.manage_reservations import ManageReservationsService
from src.core.usecases.reserve_parking import ReserveParkingService

SYSTEM_PROMPT = """\
You are a helpful parking reservation assistant. You help users manage parking \
space reservations through a chat-based interface.

**Available actions for clients:**
- Check available parking spaces for a given time period
- Make reservations for parking spaces
- View your existing reservations
- Cancel reservations
- List all parking spaces with details

**Available actions for admin users:**
- All client actions above
- View pending reservations that need approval
- Approve or reject pending reservations with optional notes
- Add or remove parking spaces

**Important rules:**
- Always confirm details before making a reservation
- When showing times, use a clear human-readable format
- If the user provides relative times like "tomorrow at 2pm", calculate the \
actual datetime based on the current time provided in your context
- Be concise but friendly
- When users ask to reserve a space, first check availability, then make the \
reservation
- Format currency values with $ and 2 decimal places
- The current date and time is provided in each request context
- When the user greets you or asks what you can do, briefly list the available \
actions relevant to their role
- Tools return structured data that the UI will render as interactive widgets. \
After calling a tool, provide a brief natural-language summary of what happened \
alongside the tool result. Do not repeat the raw data from the tool response.
"""


@dataclass
class ChatDeps:
    """Dependencies injected into the chatbot agent tools.

    Attributes:
        user_id: Current user's UUID
        user_role: Current user's role (client or admin)
        reserve_parking: Use case for creating reservations
        check_availability: Use case for checking space availability
        manage_reservations: Use case for viewing/cancelling reservations
        admin_approval: Use case for admin approval actions
        manage_spaces: Use case for managing parking spaces
    """

    user_id: UUID
    user_role: UserRole
    reserve_parking: ReserveParkingService
    check_availability: CheckAvailabilityService
    manage_reservations: ManageReservationsService
    admin_approval: AdminApprovalService
    manage_spaces: ManageParkingSpacesService


def _space_to_info(space: ParkingSpace) -> SpaceInfo:
    """Convert a domain ParkingSpace to a serialisable SpaceInfo."""
    return SpaceInfo(
        space_id=space.space_id,
        location=space.location,
        hourly_rate=space.hourly_rate,
        space_type=space.space_type,
        is_available=space.is_available,
    )


def _reservation_to_info(reservation: Reservation) -> ReservationInfo:
    """Convert a domain Reservation to a serialisable ReservationInfo."""
    return ReservationInfo(
        reservation_id=str(reservation.reservation_id),
        space_id=reservation.space_id,
        start_time=reservation.time_slot.start_time.strftime("%Y-%m-%d %H:%M"),
        end_time=reservation.time_slot.end_time.strftime("%Y-%m-%d %H:%M"),
        status=reservation.status.value,
        created_at=reservation.created_at.strftime("%Y-%m-%d %H:%M"),
        admin_notes=reservation.admin_notes,
        user_id=str(reservation.user_id),
    )


def create_parking_agent(model_name: str) -> Agent[ChatDeps, str]:
    """Create and configure the parking reservation chatbot agent.

    Args:
        model_name: The model identifier (e.g., 'ollama:gpt-oss:20b')

    Returns:
        Configured pydantic-ai Agent with all parking tools registered
    """
    agent: Agent[ChatDeps, str] = Agent(
        model_name,
        system_prompt=SYSTEM_PROMPT,
        deps_type=ChatDeps,
        output_type=str,
    )

    @agent.system_prompt
    def add_user_context(ctx: RunContext[ChatDeps]) -> str:
        """Add dynamic user context to the system prompt."""
        role_label = ctx.deps.user_role.value
        is_admin = role_label == "admin"
        if is_admin:
            role_note = (
                "The user IS an administrator. "
                "Use admin tools when they ask for admin operations."
            )
        else:
            role_note = "The user IS a client. They cannot perform admin operations."
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return (
            f"\n**Current user context:**\n"
            f"- User ID: {ctx.deps.user_id}\n"
            f"- Role: {role_label}\n"
            f"- {role_note}\n"
            f"- Current time: {now}\n"
        )

    # --- Client Tools ---

    @agent.tool
    def check_availability(
        ctx: RunContext[ChatDeps],
        start_time: str,
        end_time: str,
    ) -> str:
        """Check which parking spaces are available for a given time period.

        Args:
            ctx: Run context with dependencies
            start_time: Start datetime in ISO format (YYYY-MM-DDTHH:MM)
            end_time: End datetime in ISO format (YYYY-MM-DDTHH:MM)

        Returns:
            JSON widget response with available spaces
        """
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            time_slot = TimeSlot(start_time=start_dt, end_time=end_dt)
        except (ValueError, TypeError) as e:
            return f"Invalid date/time format: {e}. Use YYYY-MM-DDTHH:MM format."

        try:
            spaces = ctx.deps.check_availability.execute(time_slot)
        except DomainError as e:
            return f"Error checking availability: {e}"

        if not spaces:
            msg = "No parking spaces available for the requested time."
            return AvailabilityResponse(
                message=msg,
                spaces=[],
            ).to_json()

        return AvailabilityResponse(
            message=f"Found {len(spaces)} available space(s):",
            spaces=[asdict(_space_to_info(s)) for s in spaces],
        ).to_json()

    @agent.tool
    def reserve_space(
        ctx: RunContext[ChatDeps],
        space_id: str,
        start_time: str,
        end_time: str,
    ) -> str:
        """Reserve a parking space for the current user.

        Args:
            ctx: Run context with dependencies
            space_id: The parking space identifier (e.g., 'A1', 'B2')
            start_time: Start datetime in ISO format (YYYY-MM-DDTHH:MM)
            end_time: End datetime in ISO format (YYYY-MM-DDTHH:MM)

        Returns:
            JSON widget response with reservation details
        """
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            time_slot = TimeSlot(start_time=start_dt, end_time=end_dt)
        except (ValueError, TypeError) as e:
            return f"Invalid date/time format: {e}. Use YYYY-MM-DDTHH:MM format."

        try:
            reservation = ctx.deps.reserve_parking.execute(
                user_id=ctx.deps.user_id,
                space_id=space_id,
                time_slot=time_slot,
            )
        except DomainError as e:
            return f"Could not create reservation: {e}"

        return ReservationCreatedResponse(
            message="Reservation created successfully! Awaiting admin approval.",
            reservation=asdict(_reservation_to_info(reservation)),
        ).to_json()

    @agent.tool
    def get_my_reservations(ctx: RunContext[ChatDeps]) -> str:
        """Get all reservations for the current user.

        Args:
            ctx: Run context with dependencies

        Returns:
            JSON widget response with user's reservations
        """
        reservations = ctx.deps.manage_reservations.get_user_reservations(
            ctx.deps.user_id
        )
        if not reservations:
            return MyReservationsResponse(
                message="You have no reservations.",
                reservations=[],
            ).to_json()

        return MyReservationsResponse(
            message=f"You have {len(reservations)} reservation(s):",
            reservations=[asdict(_reservation_to_info(r)) for r in reservations],
        ).to_json()

    @agent.tool
    def cancel_reservation(
        ctx: RunContext[ChatDeps],
        reservation_id: str,
    ) -> str:
        """Cancel one of the current user's reservations.

        Args:
            ctx: Run context with dependencies
            reservation_id: The UUID of the reservation to cancel

        Returns:
            JSON widget response with cancelled reservation details
        """
        try:
            res_uuid = UUID(reservation_id)
        except ValueError:
            return f"Invalid reservation ID format: {reservation_id}"

        try:
            reservation = ctx.deps.manage_reservations.cancel_reservation(
                res_uuid, ctx.deps.user_id
            )
        except DomainError as e:
            return f"Could not cancel reservation: {e}"

        return ReservationActionResponse(
            message="Reservation cancelled successfully.",
            reservation=asdict(_reservation_to_info(reservation)),
        ).to_json()

    @agent.tool
    def list_all_spaces(ctx: RunContext[ChatDeps]) -> str:
        """List all parking spaces in the system with their details.

        Args:
            ctx: Run context with dependencies

        Returns:
            JSON widget response with all parking spaces
        """
        spaces = ctx.deps.manage_spaces.get_all_spaces()
        if not spaces:
            return AllSpacesResponse(
                message="No parking spaces are configured in the system.",
                spaces=[],
            ).to_json()

        return AllSpacesResponse(
            message=f"Total parking spaces: {len(spaces)}",
            spaces=[asdict(_space_to_info(s)) for s in spaces],
        ).to_json()

    # --- Admin-Only Tools ---

    @agent.tool
    def get_pending_reservations(ctx: RunContext[ChatDeps]) -> str:
        """Get all reservations pending admin approval. Admin only.

        Args:
            ctx: Run context with dependencies

        Returns:
            JSON widget response with pending reservations
        """
        if ctx.deps.user_role != UserRole.ADMIN:
            return "Access denied. Only administrators can view pending reservations."

        pending = ctx.deps.admin_approval.get_pending_reservations()
        if not pending:
            return PendingReservationsResponse(
                message="No reservations pending approval.",
                reservations=[],
            ).to_json()

        return PendingReservationsResponse(
            message=f"Pending reservations: {len(pending)}",
            reservations=[asdict(_reservation_to_info(r)) for r in pending],
        ).to_json()

    @agent.tool
    def approve_reservation(
        ctx: RunContext[ChatDeps],
        reservation_id: str,
        admin_notes: str = "",
    ) -> str:
        """Approve a pending reservation. Admin only.

        Args:
            ctx: Run context with dependencies
            reservation_id: The UUID of the reservation to approve
            admin_notes: Optional notes from the administrator

        Returns:
            JSON widget response with approved reservation details
        """
        if ctx.deps.user_role != UserRole.ADMIN:
            return "Access denied. Only administrators can approve reservations."

        try:
            res_uuid = UUID(reservation_id)
        except ValueError:
            return f"Invalid reservation ID format: {reservation_id}"

        try:
            reservation = ctx.deps.admin_approval.approve_reservation(
                res_uuid, admin_notes
            )
        except DomainError as e:
            return f"Could not approve reservation: {e}"

        return ReservationActionResponse(
            message="Reservation approved successfully!",
            reservation=asdict(_reservation_to_info(reservation)),
        ).to_json()

    @agent.tool
    def reject_reservation(
        ctx: RunContext[ChatDeps],
        reservation_id: str,
        admin_notes: str = "",
    ) -> str:
        """Reject a pending reservation. Admin only.

        Args:
            ctx: Run context with dependencies
            reservation_id: The UUID of the reservation to reject
            admin_notes: Optional notes from the administrator

        Returns:
            JSON widget response with rejected reservation details
        """
        if ctx.deps.user_role != UserRole.ADMIN:
            return "Access denied. Only administrators can reject reservations."

        try:
            res_uuid = UUID(reservation_id)
        except ValueError:
            return f"Invalid reservation ID format: {reservation_id}"

        try:
            reservation = ctx.deps.admin_approval.reject_reservation(
                res_uuid, admin_notes
            )
        except DomainError as e:
            return f"Could not reject reservation: {e}"

        return ReservationActionResponse(
            message="Reservation rejected.",
            reservation=asdict(_reservation_to_info(reservation)),
        ).to_json()

    @agent.tool
    def add_parking_space(
        ctx: RunContext[ChatDeps],
        space_id: str,
        location: str,
        hourly_rate: float = 5.0,
        space_type: str = "standard",
    ) -> str:
        """Add a new parking space. Admin only.

        Args:
            ctx: Run context with dependencies
            space_id: Unique space identifier (e.g., 'F1')
            location: Physical location description
            hourly_rate: Cost per hour in dollars
            space_type: Type of space (standard, electric, handicap)

        Returns:
            JSON widget response with the added space details
        """
        if ctx.deps.user_role != UserRole.ADMIN:
            return "Access denied. Only administrators can add parking spaces."

        space = ParkingSpace(
            space_id=space_id,
            location=location,
            hourly_rate=hourly_rate,
            space_type=space_type,
        )
        try:
            created = ctx.deps.manage_spaces.add_space(space)
        except DomainError as e:
            return f"Could not add parking space: {e}"

        return SpaceActionResponse(
            message="Parking space added successfully!",
            space=asdict(_space_to_info(created)),
        ).to_json()

    @agent.tool
    def remove_parking_space(
        ctx: RunContext[ChatDeps],
        space_id: str,
    ) -> str:
        """Remove a parking space. Admin only.

        Args:
            ctx: Run context with dependencies
            space_id: The space identifier to remove

        Returns:
            Confirmation or error message
        """
        if ctx.deps.user_role != UserRole.ADMIN:
            return "Access denied. Only administrators can remove parking spaces."

        try:
            ctx.deps.manage_spaces.remove_space(space_id)
        except DomainError as e:
            return f"Could not remove parking space: {e}"

        return SpaceActionResponse(
            message=f"Parking space {space_id} removed successfully.",
        ).to_json()

    return agent
