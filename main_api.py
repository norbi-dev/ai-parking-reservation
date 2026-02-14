"""Main entry point for the FastAPI REST API server."""

from src.config.logging import setup_logging

setup_logging()

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from loguru import logger  # noqa: E402

from src.adapters.incoming.api.routes import router  # noqa: E402
from src.config.dependencies import get_settings  # noqa: E402


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    logger.info("Creating FastAPI application")
    app = FastAPI(
        title="Parking Reservation API",
        description=(
            "REST API for parking space reservations with "
            "human-in-the-loop admin approval."
        ),
        version="0.1.0",
    )
    app.include_router(router, prefix="/api/v1")
    logger.debug("Registered API router at /api/v1")
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    logger.info(
        "Starting API server on {}:{}",
        settings.api_host,
        settings.api_port,
    )
    uvicorn.run(
        "main_api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
