"""Streamlit chat UI adapter for the parking reservation chatbot.

This is the main entry point for the Streamlit application. It provides
a fully chat-driven interface where users interact with an AI assistant
to manage parking reservations. Both client and admin operations are
handled through the chat with inline interactive widgets.

All backend communication goes through the REST API — the frontend
is language-independent and has no direct dependency on Python backend
internals.
"""

import asyncio
from uuid import uuid4

import streamlit as st
from loguru import logger

from src.adapters.incoming.streamlit_app.api_client import create_api_client
from src.adapters.incoming.streamlit_app.chat_page import render_chat


def _init_session_state() -> None:
    """Initialize Streamlit session state with defaults."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid4())
        logger.debug("Streamlit: new session user_id={}", st.session_state.user_id)
    if "user_role" not in st.session_state:
        st.session_state.user_role = "client"
    if "messages" not in st.session_state:
        # Display messages for UI rendering (role + content)
        st.session_state.messages = []
    if "backend_session_id" not in st.session_state:
        # Backend conversation session ID - will be created on first message
        st.session_state.backend_session_id = None
    if "event_loop" not in st.session_state:
        st.session_state.event_loop = asyncio.new_event_loop()
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "api_client" not in st.session_state:
        st.session_state.api_client = create_api_client()
        logger.debug("Streamlit: API client initialized")


def _render_sidebar() -> None:
    """Render the sidebar with role switcher and session info."""
    with st.sidebar:
        st.header("Settings")

        # Role switcher
        role = st.radio(
            "Role",
            ["Client", "Admin"],
            index=0 if st.session_state.user_role == "client" else 1,
            key="role_selector",
        )
        new_role = role.lower() if role else "client"
        if new_role != st.session_state.user_role:
            logger.debug(
                "Streamlit: role switched from {} to {}",
                st.session_state.user_role,
                new_role,
            )
            st.session_state.user_role = new_role
            st.session_state.messages = []
            st.session_state.backend_session_id = None  # Clear backend session
            st.session_state.pending_prompt = None
            st.rerun()

        st.divider()

        # User session info
        st.subheader("Session Info")
        st.text_input(
            "User ID",
            value=st.session_state.user_id,
            disabled=True,
        )
        st.caption(f"Role: **{st.session_state.user_role.upper()}**")

        st.divider()

        # Clear chat button
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.backend_session_id = None  # Clear backend session
            st.session_state.pending_prompt = None
            st.rerun()


def run_app() -> None:
    """Run the Streamlit chat application."""
    st.set_page_config(
        page_title="Parking Reservation Chatbot",
        page_icon="🅿️",
        layout="wide",
    )

    _init_session_state()
    _render_sidebar()

    st.title("Parking Reservation Chatbot")
    st.caption(
        "Chat with the AI assistant to check availability, "
        "make reservations, and manage your parking."
    )

    render_chat()
