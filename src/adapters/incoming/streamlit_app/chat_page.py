"""Chat page for the Streamlit parking reservation UI.

Handles the main chat interface where users interact with the
LLM-powered parking reservation assistant. Supports:
- Welcome message with quick-action buttons
- Inline Streamlit widgets for structured agent responses
  (availability tables, reservation cards, approve/reject buttons)
- Plain markdown fallback for conversational text
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import streamlit as st

from src.adapters.incoming.streamlit_app.chat_widgets import parse_widget_response
from src.config import dependencies
from src.core.domain.exceptions import DomainError
from src.core.domain.models import UserRole

# ── Quick-action definitions per role ──────────────────────────────

_CLIENT_ACTIONS = [
    (
        "Check Availability",
        "What parking spaces are available tomorrow from 9am to 5pm?",
    ),
    ("My Reservations", "Show my reservations"),
    ("List Spaces", "List all parking spaces"),
]

_ADMIN_ACTIONS = [
    (
        "Check Availability",
        "What parking spaces are available tomorrow from 9am to 5pm?",
    ),
    ("Pending Approvals", "Show pending reservations"),
    ("List Spaces", "List all parking spaces"),
    ("My Reservations", "Show my reservations"),
]


# ── Welcome message ───────────────────────────────────────────────


def _render_welcome() -> None:
    """Show the welcome message with quick-action buttons."""
    is_admin = st.session_state.user_role == "admin"
    role_label = "Administrator" if is_admin else "Client"
    actions = _ADMIN_ACTIONS if is_admin else _CLIENT_ACTIONS

    with st.chat_message("assistant"):
        st.markdown(
            f"Hello! I'm your parking reservation assistant. "
            f"You're logged in as **{role_label}**.\n\n"
            f"Here's what I can help you with:"
        )

        cols = st.columns(len(actions))
        for col, (label, prompt) in zip(cols, actions):
            with col:
                if st.button(label, key=f"welcome_{label}", use_container_width=True):
                    st.session_state.pending_prompt = prompt
                    st.rerun()


# ── Widget renderers ──────────────────────────────────────────────


def _render_status_badge(status: str) -> str:
    """Return a coloured status label."""
    colours = {
        "pending": "🟡 Pending",
        "confirmed": "🟢 Confirmed",
        "rejected": "🔴 Rejected",
        "cancelled": "⚪ Cancelled",
    }
    return colours.get(status, status)


def _render_space_type_badge(space_type: str) -> str:
    """Return a type indicator."""
    icons = {
        "standard": "🅿️ Standard",
        "electric": "⚡ Electric",
        "handicap": "♿ Handicap",
    }
    return icons.get(space_type, space_type)


def _render_availability_widget(data: dict[str, Any]) -> None:
    """Render available spaces as a table with reserve buttons."""
    st.markdown(data.get("message", ""))
    spaces = data.get("spaces", [])
    if not spaces:
        return

    for space in spaces:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.markdown(f"**{space['space_id']}** — {space['location']}")
            with c2:
                st.markdown(
                    f"${space['hourly_rate']:.2f}/hr | "
                    f"{_render_space_type_badge(space['space_type'])}"
                )
            with c3:
                if st.button(
                    "Reserve",
                    key=f"reserve_{space['space_id']}_{id(data)}",
                    use_container_width=True,
                ):
                    st.session_state.pending_prompt = (
                        f"Reserve space {space['space_id']} for the same time period"
                    )
                    st.rerun()


def _render_reservation_card(
    res: dict[str, Any], *, show_actions: bool = False
) -> None:
    """Render a single reservation as a card."""
    with st.container(border=True):
        short_id = res["reservation_id"][:8]
        st.markdown(f"**Reservation #{short_id}...** — Space **{res['space_id']}**")
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"From: {res['start_time']}")
            st.caption(f"To: {res['end_time']}")
        with c2:
            st.markdown(_render_status_badge(res["status"]))
            st.caption(f"Created: {res['created_at']}")
        if res.get("admin_notes"):
            st.info(f"Admin notes: {res['admin_notes']}")
        if res.get("user_id"):
            st.caption(f"User: {res['user_id'][:8]}...")

        # Inline action buttons
        if show_actions and res["status"] == "pending":
            notes_key = f"notes_{res['reservation_id']}_{id(res)}"
            admin_notes = st.text_input(
                "Admin notes",
                key=notes_key,
                placeholder="Optional notes",
            )
            col_a, col_r = st.columns(2)
            with col_a:
                if st.button(
                    "Approve",
                    key=f"approve_{res['reservation_id']}_{id(res)}",
                    type="primary",
                    use_container_width=True,
                ):
                    _handle_admin_action(res["reservation_id"], "approve", admin_notes)
            with col_r:
                if st.button(
                    "Reject",
                    key=f"reject_{res['reservation_id']}_{id(res)}",
                    use_container_width=True,
                ):
                    _handle_admin_action(res["reservation_id"], "reject", admin_notes)

        # Cancel button for user's own non-terminal reservations
        if not show_actions and res["status"] in ("pending", "confirmed"):
            if st.button(
                "Cancel",
                key=f"cancel_{res['reservation_id']}_{id(res)}",
                use_container_width=True,
            ):
                st.session_state.pending_prompt = (
                    f"Cancel reservation {res['reservation_id']}"
                )
                st.rerun()


def _handle_admin_action(reservation_id: str, action: str, admin_notes: str) -> None:
    """Execute an admin approve/reject directly and inject result into chat."""
    usecase = dependencies.get_admin_approval_usecase()
    try:
        res_uuid = UUID(reservation_id)
        if action == "approve":
            usecase.approve_reservation(res_uuid, admin_notes)
            st.session_state.pending_prompt = (
                f"I just approved reservation {reservation_id}"
            )
        else:
            usecase.reject_reservation(res_uuid, admin_notes)
            st.session_state.pending_prompt = (
                f"I just rejected reservation {reservation_id}"
            )
        st.rerun()
    except DomainError as e:
        st.error(str(e))


def _render_reservation_created_widget(data: dict[str, Any]) -> None:
    """Render a newly created reservation."""
    st.success(data.get("message", "Reservation created!"))
    res = data.get("reservation", {})
    if res:
        _render_reservation_card(res)


def _render_my_reservations_widget(data: dict[str, Any]) -> None:
    """Render the user's reservation list."""
    st.markdown(data.get("message", ""))
    reservations = data.get("reservations", [])
    for res in reservations:
        _render_reservation_card(res)


def _render_reservation_action_widget(data: dict[str, Any]) -> None:
    """Render result of a reservation action (cancel/approve/reject)."""
    message = data.get("message", "")
    if "approved" in message.lower():
        st.success(message)
    elif "rejected" in message.lower():
        st.warning(message)
    elif "cancelled" in message.lower():
        st.info(message)
    else:
        st.markdown(message)
    res = data.get("reservation", {})
    if res:
        _render_reservation_card(res)


def _render_all_spaces_widget(data: dict[str, Any]) -> None:
    """Render all parking spaces as a table."""
    st.markdown(data.get("message", ""))
    spaces = data.get("spaces", [])
    if not spaces:
        return

    for space in spaces:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.markdown(f"**{space['space_id']}** — {space['location']}")
            with c2:
                st.markdown(
                    f"${space['hourly_rate']:.2f}/hr | "
                    f"{_render_space_type_badge(space['space_type'])}"
                )
            with c3:
                status = (
                    "Available" if space.get("is_available", True) else "Unavailable"
                )
                st.markdown(
                    f"{'🟢' if space.get('is_available', True) else '🔴'} {status}"
                )


def _render_pending_reservations_widget(data: dict[str, Any]) -> None:
    """Render pending reservations with approve/reject buttons."""
    st.markdown(data.get("message", ""))
    reservations = data.get("reservations", [])
    if not reservations:
        st.info("No pending reservations.")
        return

    for res in reservations:
        _render_reservation_card(res, show_actions=True)


def _render_space_action_widget(data: dict[str, Any]) -> None:
    """Render result of a space add/remove action."""
    message = data.get("message", "")
    if "added" in message.lower():
        st.success(message)
    elif "removed" in message.lower():
        st.info(message)
    else:
        st.markdown(message)
    space = data.get("space", {})
    if space:
        with st.container(border=True):
            st.markdown(
                f"**{space['space_id']}** — {space.get('location', 'N/A')} | "
                f"${space.get('hourly_rate', 0):.2f}/hr | "
                f"{_render_space_type_badge(space.get('space_type', 'standard'))}"
            )


# Dispatch table for widget types
_WIDGET_RENDERERS = {
    "availability": _render_availability_widget,
    "reservation_created": _render_reservation_created_widget,
    "my_reservations": _render_my_reservations_widget,
    "reservation_action": _render_reservation_action_widget,
    "all_spaces": _render_all_spaces_widget,
    "pending_reservations": _render_pending_reservations_widget,
    "space_action": _render_space_action_widget,
}


def _render_message_content(content: str) -> None:
    """Render a message, detecting widget JSON and rendering widgets."""
    widget_data = parse_widget_response(content)
    if widget_data:
        widget_type = str(widget_data.get("__widget__", ""))
        renderer = _WIDGET_RENDERERS.get(widget_type)
        if renderer:
            renderer(widget_data)
            # Also render any text outside the JSON block
            import json
            import re

            json_str = json.dumps(widget_data)
            # Remove the JSON block from content to show remaining text
            cleaned = content.replace(json_str, "").strip()
            # Also remove code-fenced versions
            cleaned = re.sub(
                r"```(?:json)?\s*\{.*?\}\s*```", "", cleaned, flags=re.DOTALL
            ).strip()
            if cleaned:
                st.markdown(cleaned)
            return

    # Fallback: plain markdown
    st.markdown(content)


# ── Main chat render ──────────────────────────────────────────────


def render_chat() -> None:
    """Render the chat interface with welcome message, history, and input."""
    # Show welcome if no messages yet
    if not st.session_state.messages:
        _render_welcome()

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            _render_message_content(message["content"])

    # Handle pending prompt from button clicks
    prompt = st.session_state.pending_prompt
    if prompt:
        st.session_state.pending_prompt = None
        _process_user_message(prompt)
        return

    # Chat input
    if user_input := st.chat_input("Ask about parking reservations..."):
        _process_user_message(user_input)


def _process_user_message(prompt: str) -> None:
    """Process a user message: show it, get response, and display it."""
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get chatbot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = _get_chatbot_response(prompt)
        _render_message_content(response)

    # Add assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": response})


def _get_chatbot_response(user_message: str) -> str:
    """Send a message to the chatbot and get a response.

    Args:
        user_message: The user's message text

    Returns:
        The chatbot's response text (may contain widget JSON)
    """
    user_id = UUID(st.session_state.user_id)
    user_role = UserRole(st.session_state.user_role)

    agent = dependencies.get_parking_agent()
    chat_deps = dependencies.get_chat_deps(user_id, user_role)

    # Build message history for context (excluding the current message)
    from pydantic_ai.messages import (
        ModelMessage,
        ModelRequest,
        ModelResponse,
        TextPart,
        UserPromptPart,
    )

    message_history: list[ModelMessage] = []
    for msg in st.session_state.messages[:-1]:  # Exclude current user message
        if msg["role"] == "user":
            message_history.append(
                ModelRequest(parts=[UserPromptPart(content=msg["content"])])
            )
        elif msg["role"] == "assistant":
            message_history.append(
                ModelResponse(parts=[TextPart(content=msg["content"])])
            )

    try:
        loop = st.session_state.event_loop
        result = loop.run_until_complete(
            agent.run(
                user_message,
                deps=chat_deps,
                message_history=message_history or None,
            )
        )
        return str(result.output)
    except Exception as e:
        return f"Sorry, I encountered an error: {e}"
