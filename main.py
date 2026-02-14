"""Main entry point for the Streamlit parking reservation UI."""

from src.config.logging import setup_logging

setup_logging()

from loguru import logger  # noqa: E402

from src.adapters.incoming.streamlit_app.app import run_app  # noqa: E402

logger.info("Starting Streamlit parking reservation UI")
run_app()
