"""Async REST API client for the Streamlit frontend.

Provides a language-independent HTTP interface to the backend API,
replacing direct Python dependency imports. Any frontend (Streamlit,
React, mobile) can use the same REST endpoints.

All methods are async and use httpx.AsyncClient. The Streamlit adapter
runs them via its own event loop.
"""

from uuid import UUID

import httpx
from loguru import logger

from src.config.settings import Settings

# Timeout for all API calls (seconds)
# Chat requests can take 30-60s for LLM inference (Ollama or OpenRouter)
_TIMEOUT = 90.0


class ParkingAPIClient:
    """Async HTTP client for the parking reservation REST API.

    Args:
        base_url: API base URL (e.g. ``http://localhost:8000/api/v1``)
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=_TIMEOUT,
        )

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    # ── Client endpoints ──────────────────────────────────────────

    async def chat(
        self,
        message: str,
        user_id: UUID,
        user_role: str,
        session_id: UUID | None = None,
    ) -> dict:
        """Send a chat message to the backend.

        Args:
            message: User's message text
            user_id: Current user ID
            user_role: 'client' or 'admin'
            session_id: Existing session ID, or None to create a new one

        Returns:
            Dict with 'response', 'session_id', and 'user_id'

        Raises:
            httpx.HTTPStatusError: On non-2xx responses
        """
        payload: dict = {
            "message": message,
            "user_id": str(user_id),
            "user_role": user_role,
        }
        if session_id is not None:
            payload["session_id"] = str(session_id)

        logger.debug(
            "API client → POST /client/chat: user={}, session={}",
            user_id,
            session_id,
        )
        resp = await self._client.post("/client/chat", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def delete_chat_session(self, session_id: UUID) -> None:
        """Delete a chat session.

        Args:
            session_id: Session to delete
        """
        logger.debug("API client → DELETE /client/chat/sessions/{}", session_id)
        resp = await self._client.delete(f"/client/chat/sessions/{session_id}")
        resp.raise_for_status()

    async def get_user_reservations(self, user_id: UUID) -> list[dict]:
        """Get all reservations for a user.

        Args:
            user_id: User whose reservations to fetch

        Returns:
            List of reservation dicts
        """
        resp = await self._client.get(f"/client/reservations/user/{user_id}")
        resp.raise_for_status()
        return resp.json()

    async def cancel_reservation(self, reservation_id: UUID, user_id: UUID) -> dict:
        """Cancel a reservation.

        Args:
            reservation_id: Reservation to cancel
            user_id: User requesting cancellation

        Returns:
            Updated reservation dict
        """
        resp = await self._client.post(
            f"/client/reservations/{reservation_id}/cancel",
            params={"user_id": str(user_id)},
        )
        resp.raise_for_status()
        return resp.json()

    async def list_spaces(self) -> list[dict]:
        """List all parking spaces (client view).

        Returns:
            List of parking space dicts
        """
        resp = await self._client.get("/client/spaces")
        resp.raise_for_status()
        return resp.json()

    # ── Admin endpoints ───────────────────────────────────────────

    async def get_pending_reservations(self) -> list[dict]:
        """Get all pending reservations (admin).

        Returns:
            List of pending reservation dicts
        """
        resp = await self._client.get("/admin/reservations/pending")
        resp.raise_for_status()
        return resp.json()

    async def approve_reservation(
        self, reservation_id: UUID, admin_notes: str = ""
    ) -> dict:
        """Approve a pending reservation.

        Args:
            reservation_id: Reservation to approve
            admin_notes: Optional admin notes

        Returns:
            Updated reservation dict
        """
        payload = {"admin_notes": admin_notes} if admin_notes else None
        resp = await self._client.post(
            f"/admin/reservations/{reservation_id}/approve",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    async def reject_reservation(
        self, reservation_id: UUID, admin_notes: str = ""
    ) -> dict:
        """Reject a pending reservation.

        Args:
            reservation_id: Reservation to reject
            admin_notes: Optional admin notes

        Returns:
            Updated reservation dict
        """
        payload = {"admin_notes": admin_notes} if admin_notes else None
        resp = await self._client.post(
            f"/admin/reservations/{reservation_id}/reject",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    async def admin_get_all_spaces(self) -> list[dict]:
        """Get all parking spaces (admin view).

        Returns:
            List of parking space dicts
        """
        resp = await self._client.get("/admin/spaces")
        resp.raise_for_status()
        return resp.json()

    async def add_space(self, space_data: dict) -> dict:
        """Add a new parking space (admin).

        Args:
            space_data: Space fields (space_id, location, etc.)

        Returns:
            Created space dict
        """
        resp = await self._client.post("/admin/spaces", json=space_data)
        resp.raise_for_status()
        return resp.json()

    async def update_space(self, space_id: str, space_data: dict) -> dict:
        """Update a parking space (admin).

        Args:
            space_id: Space to update
            space_data: Updated space fields

        Returns:
            Updated space dict
        """
        resp = await self._client.put(f"/admin/spaces/{space_id}", json=space_data)
        resp.raise_for_status()
        return resp.json()

    async def remove_space(self, space_id: str) -> None:
        """Remove a parking space (admin).

        Args:
            space_id: Space to remove
        """
        resp = await self._client.delete(f"/admin/spaces/{space_id}")
        resp.raise_for_status()


def create_api_client() -> ParkingAPIClient:
    """Create a ParkingAPIClient using application settings.

    Returns:
        Configured API client pointing at the backend
    """
    settings = Settings()
    logger.info("Creating API client for {}", settings.api_base_url)
    return ParkingAPIClient(settings.api_base_url)
