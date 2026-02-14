"""Loguru logging configuration for the parking reservation system.

Configures loguru with:
- Console output at DEBUG level with coloured formatting
- File output with rotation for persistent logs
- Intercept of stdlib logging so third-party libraries (uvicorn, sqlalchemy)
  are routed through loguru as well
"""

import logging
import os
import sys
from pathlib import Path

from loguru import logger


def setup_logging(*, log_level: str | None = None, log_file: str | None = None) -> None:
    """Configure loguru for the application.

    Removes the default loguru sink and adds:
    - stderr sink at *log_level* with colour
    - rotating file sink at DEBUG (always captures everything)

    Also installs an intercept handler so that stdlib ``logging`` calls
    (e.g. from uvicorn, sqlalchemy) are forwarded to loguru.

    The console log level is resolved in this order:
    1. Explicit *log_level* argument
    2. ``LOG_LEVEL`` environment variable
    3. Falls back to ``"DEBUG"``

    The log file path is resolved in this order:
    1. Explicit *log_file* argument
    2. ``LOG_FILE`` environment variable
    3. Falls back to ``"logs/app.log"``

    Args:
        log_level: Minimum level for console output (default from env or DEBUG)
        log_file: Path for the rotating log file (default from env or logs/app.log)
    """
    if log_level is None:
        log_level = os.environ.get("LOG_LEVEL", "DEBUG").upper()

    if log_file is None:
        log_file = os.environ.get("LOG_FILE", "logs/app.log")

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default loguru handler
    logger.remove()

    # Console sink
    logger.add(
        sys.stderr,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File sink with rotation
    # Keep max 5 files per service (retention="5")
    logger.add(
        log_file,
        level="DEBUG",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        rotation="10 MB",
        retention=5,  # Keep max 5 files
        compression="zip",
    )

    # Intercept stdlib logging → loguru
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)


class _InterceptHandler(logging.Handler):
    """Route stdlib logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore[assignment]

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
