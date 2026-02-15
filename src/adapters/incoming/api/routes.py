"""FastAPI REST API router aggregator.

Mounts client and admin sub-routers under separate prefixes,
providing clear separation of concerns for access control.

Route structure:
    /api/v1/client/  — client-facing endpoints (reservations, availability, chat)
    /api/v1/admin/   — admin-facing endpoints (approval, space management)
"""

from fastapi import APIRouter

from src.adapters.incoming.api.admin_routes import router as admin_router
from src.adapters.incoming.api.client_routes import router as client_router

router = APIRouter()

router.include_router(client_router, prefix="/client")
router.include_router(admin_router, prefix="/admin")
