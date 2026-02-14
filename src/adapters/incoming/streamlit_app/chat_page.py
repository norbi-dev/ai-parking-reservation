"""Chat page for the Streamlit parking reservation UI.

Handles the main chat interface where users interact with the
LLM-powered parking reservation assistant.
"""

from __future__ import annotations

from uuid import UUID

import streamlit as st

from src.config import dependencies
from src.core.domain.models import UserRole


def render_chat() -> None:
    """Render the chat interface with message history and input."""
    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about parking reservations..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get chatbot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = _get_chatbot_response(prompt)
            st.markdown(response)

        # Add assistant message to history
        st.session_state.messages.append({"role": "assistant", "content": response})


def _get_chatbot_response(user_message: str) -> str:
    """Send a message to the chatbot and get a response.

    Args:
        user_message: The user's message text

    Returns:
        The chatbot's response text
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
        return result.output
    except Exception as e:
        return f"Sorry, I encountered an error: {e}"
