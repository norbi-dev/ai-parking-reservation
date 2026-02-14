"""Streamlit UI adapter for the parking reservation chatbot."""

import streamlit as st

from src.adapters.incoming.streamlit_app.admin_page import render_admin_page
from src.adapters.incoming.streamlit_app.client_page import render_client_page


def run_app() -> None:
    """Run the Streamlit application with client and admin pages."""
    st.set_page_config(
        page_title="Parking Reservation System",
        page_icon="🅿️",
        layout="wide",
    )

    st.title("Parking Reservation System")

    page = st.sidebar.radio(
        "Navigation",
        ["Client", "Admin"],
        index=0,
    )

    if page == "Client":
        render_client_page()
    else:
        render_admin_page()
