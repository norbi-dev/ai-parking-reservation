"""Client page for the Streamlit parking reservation UI."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import streamlit as st

from src.config import dependencies
from src.core.domain.exceptions import DomainError
from src.core.domain.models import TimeSlot


def render_client_page() -> None:
    """Render the client-facing reservation page."""
    st.header("Reserve a Parking Space")

    # Initialize session state for user
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid4())

    user_id = UUID(st.session_state.user_id)

    tab1, tab2 = st.tabs(["Make Reservation", "My Reservations"])

    with tab1:
        _render_reservation_form(user_id)

    with tab2:
        _render_user_reservations(user_id)


def _render_reservation_form(user_id: UUID) -> None:
    """Render the reservation creation form.

    Args:
        user_id: Current user's ID
    """
    st.subheader("Check Availability & Reserve")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().date())
        start_time = st.time_input("Start Time", value=datetime.now().time())
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
        end_time = st.time_input(
            "End Time", value=(datetime.now() + timedelta(hours=2)).time()
        )

    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)

    if st.button("Check Availability"):
        if end_dt <= start_dt:
            st.error("End time must be after start time.")
            return

        time_slot = TimeSlot(start_time=start_dt, end_time=end_dt)
        usecase = dependencies.get_check_availability_usecase()
        available_spaces = usecase.execute(time_slot)

        if not available_spaces:
            st.warning("No spaces available for the selected time slot.")
        else:
            st.success(f"{len(available_spaces)} space(s) available!")
            st.session_state.available_spaces = available_spaces
            st.session_state.selected_time_slot = time_slot

    if "available_spaces" in st.session_state:
        spaces = st.session_state.available_spaces
        space_options = {
            (
                f"{s.space_id} - {s.location} (${s.hourly_rate}/hr, {s.space_type})"
            ): s.space_id
            for s in spaces
        }
        selected = st.selectbox("Select a space", list(space_options.keys()))

        if selected and st.button("Reserve Space"):
            space_id = space_options[selected]
            time_slot = st.session_state.selected_time_slot

            try:
                usecase = dependencies.get_reserve_parking_usecase()
                reservation = usecase.execute(
                    user_id=user_id,
                    space_id=space_id,
                    time_slot=time_slot,
                )
                st.success(
                    f"Reservation created! ID: {reservation.reservation_id}\n"
                    f"Status: {reservation.status.value}\n"
                    "Awaiting admin approval."
                )
                # Clear the available spaces to reset the form
                del st.session_state.available_spaces
                del st.session_state.selected_time_slot
            except DomainError as e:
                st.error(f"Failed to create reservation: {e}")


def _render_user_reservations(user_id: UUID) -> None:
    """Render the user's existing reservations.

    Args:
        user_id: Current user's ID
    """
    st.subheader("Your Reservations")

    usecase = dependencies.get_manage_reservations_usecase()
    reservations = usecase.get_user_reservations(user_id)

    if not reservations:
        st.info("You have no reservations yet.")
        return

    for reservation in reservations:
        with st.expander(
            f"Reservation {reservation.reservation_id} - "
            f"Space {reservation.space_id} - "
            f"Status: {reservation.status.value}"
        ):
            st.write(f"**Space:** {reservation.space_id}")
            st.write(f"**From:** {reservation.time_slot.start_time}")
            st.write(f"**To:** {reservation.time_slot.end_time}")
            st.write(f"**Status:** {reservation.status.value}")
            st.write(f"**Created:** {reservation.created_at}")
            if reservation.admin_notes:
                st.write(f"**Admin Notes:** {reservation.admin_notes}")

            if reservation.status.value in ("pending", "confirmed"):
                if st.button(
                    "Cancel",
                    key=f"cancel_{reservation.reservation_id}",
                ):
                    try:
                        usecase.cancel_reservation(reservation.reservation_id, user_id)
                        st.success("Reservation cancelled.")
                        st.rerun()
                    except DomainError as e:
                        st.error(f"Failed to cancel: {e}")
