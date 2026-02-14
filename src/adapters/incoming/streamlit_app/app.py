"""Streamlit chat UI adapter for the parking reservation chatbot.

This is the main entry point for the Streamlit application. It provides
a chat-based interface with sidebar controls for role switching and
admin operations.
"""

import asyncio
from uuid import uuid4

import streamlit as st

from src.adapters.incoming.streamlit_app.admin_page import render_admin_sidebar
from src.adapters.incoming.streamlit_app.chat_page import render_chat


def _init_session_state() -> None:
    """Initialize Streamlit session state with defaults."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid4())
    if "user_role" not in st.session_state:
        st.session_state.user_role = "client"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "event_loop" not in st.session_state:
        st.session_state.event_loop = asyncio.new_event_loop()


def _render_sidebar() -> None:
    """Render the sidebar with role switcher and user info."""
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
            st.session_state.user_role = new_role
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
            st.rerun()

        # Admin-specific sidebar section
        if st.session_state.user_role == "admin":
            st.divider()
            render_admin_sidebar()


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
