"""Admin sidebar for the Streamlit parking reservation UI.

Provides a quick-access admin panel in the sidebar for viewing
and acting on pending reservations without needing to chat.
"""

import streamlit as st

from src.config import dependencies
from src.core.domain.exceptions import DomainError


def render_admin_sidebar() -> None:
    """Render the admin section in the sidebar with pending approvals."""
    st.subheader("Admin Panel")

    usecase = dependencies.get_admin_approval_usecase()
    pending = usecase.get_pending_reservations()

    if not pending:
        st.info("No pending reservations.")
        return

    st.warning(f"{len(pending)} pending approval(s)")

    for reservation in pending:
        short_id = str(reservation.reservation_id)[:8]
        with st.expander(f"#{short_id}... | {reservation.space_id}"):
            st.caption(f"**User:** {str(reservation.user_id)[:8]}...")
            st.caption(f"**From:** {reservation.time_slot.start_time:%Y-%m-%d %H:%M}")
            st.caption(f"**To:** {reservation.time_slot.end_time:%Y-%m-%d %H:%M}")

            admin_notes = st.text_input(
                "Notes",
                key=f"sidebar_notes_{reservation.reservation_id}",
                placeholder="Optional admin notes",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Approve",
                    key=f"sidebar_approve_{reservation.reservation_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        usecase.approve_reservation(
                            reservation.reservation_id, admin_notes
                        )
                        st.success("Approved!")
                        st.rerun()
                    except DomainError as e:
                        st.error(str(e))

            with col2:
                if st.button(
                    "Reject",
                    key=f"sidebar_reject_{reservation.reservation_id}",
                    use_container_width=True,
                ):
                    try:
                        usecase.reject_reservation(
                            reservation.reservation_id, admin_notes
                        )
                        st.warning("Rejected.")
                        st.rerun()
                    except DomainError as e:
                        st.error(str(e))
