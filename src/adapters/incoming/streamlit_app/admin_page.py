"""Admin page for the Streamlit parking reservation UI."""

import streamlit as st

from src.config import dependencies
from src.core.domain.exceptions import DomainError
from src.core.domain.models import ParkingSpace


def render_admin_page() -> None:
    """Render the administrator dashboard page."""
    st.header("Administrator Dashboard")

    tab1, tab2 = st.tabs(["Pending Approvals", "Manage Spaces"])

    with tab1:
        _render_pending_approvals()

    with tab2:
        _render_manage_spaces()


def _render_pending_approvals() -> None:
    """Render the pending reservation approvals section."""
    st.subheader("Pending Reservations")

    usecase = dependencies.get_admin_approval_usecase()
    pending = usecase.get_pending_reservations()

    if not pending:
        st.info("No pending reservations.")
        return

    for reservation in pending:
        with st.expander(
            f"Reservation {reservation.reservation_id} - Space {reservation.space_id}"
        ):
            st.write(f"**User ID:** {reservation.user_id}")
            st.write(f"**Space:** {reservation.space_id}")
            st.write(f"**From:** {reservation.time_slot.start_time}")
            st.write(f"**To:** {reservation.time_slot.end_time}")
            st.write(f"**Created:** {reservation.created_at}")

            admin_notes = st.text_input(
                "Admin Notes",
                key=f"notes_{reservation.reservation_id}",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Approve",
                    key=f"approve_{reservation.reservation_id}",
                    type="primary",
                ):
                    try:
                        usecase.approve_reservation(
                            reservation.reservation_id, admin_notes
                        )
                        st.success("Reservation approved!")
                        st.rerun()
                    except DomainError as e:
                        st.error(f"Failed to approve: {e}")

            with col2:
                if st.button(
                    "Reject",
                    key=f"reject_{reservation.reservation_id}",
                ):
                    try:
                        usecase.reject_reservation(
                            reservation.reservation_id, admin_notes
                        )
                        st.warning("Reservation rejected.")
                        st.rerun()
                    except DomainError as e:
                        st.error(f"Failed to reject: {e}")


def _render_manage_spaces() -> None:
    """Render the parking space management section."""
    st.subheader("Parking Spaces")

    usecase = dependencies.get_manage_parking_spaces_usecase()
    spaces = usecase.get_all_spaces()

    # Display existing spaces
    if spaces:
        for space in spaces:
            with st.expander(
                f"{space.space_id} - {space.location} "
                f"({'Available' if space.is_available else 'Unavailable'})"
            ):
                st.write(f"**Type:** {space.space_type}")
                st.write(f"**Hourly Rate:** ${space.hourly_rate:.2f}")
                st.write(
                    f"**Status:** "
                    f"{'Available' if space.is_available else 'Unavailable'}"
                )

                if st.button(
                    "Remove",
                    key=f"remove_{space.space_id}",
                ):
                    try:
                        usecase.remove_space(space.space_id)
                        st.success(f"Space {space.space_id} removed.")
                        st.rerun()
                    except DomainError as e:
                        st.error(f"Failed to remove: {e}")

    # Add new space form
    st.subheader("Add New Space")
    with st.form("add_space_form"):
        space_id = st.text_input("Space ID (e.g., F1)")
        location = st.text_input("Location (e.g., Level 3, Section F)")
        hourly_rate = st.number_input(
            "Hourly Rate ($)", min_value=0.0, value=5.0, step=0.5
        )
        space_type = st.selectbox("Type", ["standard", "electric", "handicap"])

        if st.form_submit_button("Add Space"):
            if not space_id or not location:
                st.error("Space ID and Location are required.")
            else:
                new_space = ParkingSpace(
                    space_id=space_id,
                    location=location,
                    hourly_rate=hourly_rate,
                    space_type=space_type,
                )
                usecase.add_space(new_space)
                st.success(f"Space {space_id} added!")
                st.rerun()
