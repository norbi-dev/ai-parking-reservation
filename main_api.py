"""Main entry point for the FastAPI REST API server."""

import uvicorn
from fastapi import FastAPI

from src.adapters.incoming.api.routes import router
from src.config.dependencies import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Parking Reservation API",
        description=(
            "REST API for parking space reservations with "
            "human-in-the-loop admin approval."
        ),
        version="0.1.0",
    )
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main_api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
