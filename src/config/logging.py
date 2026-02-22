"""Loguru logging configuration for the parking reservation system.

Configures loguru with:
- Console output with coloured formatting (level from Settings)
- File output with configurable rotation and retention
- Intercept of stdlib logging so third-party libraries (uvicorn, sqlalchemy)
  are routed through loguru as well

All logging settings are centralized in ``Settings`` (pydantic-settings),
which reads from env vars / ``.env`` automatically. Explicit kwargs to
``setup_logging()`` override Settings values.
"""

import logging
import sys
from pathlib import Path

from loguru import logger

from src.config.settings import Settings


def setup_logging(
    *,
    log_level: str | None = None,
    log_file: str | None = None,
    log_rotation: str | None = None,
    log_retention: str | None = None,
) -> None:
    """Configure loguru for the application.

    Removes the default loguru sink and adds:
    - stderr sink at *log_level* with colour
    - rotating file sink at DEBUG (always captures everything)

    Also installs an intercept handler so that stdlib ``logging`` calls
    (e.g. from uvicorn, sqlalchemy) are forwarded to loguru.

    Resolution order for each parameter (first non-None wins):
    1. Explicit kwarg
    2. ``Settings`` value (sourced from env var / ``.env``)

    Args:
        log_level: Minimum level for console output.
        log_file: Path for the rotating log file.
        log_rotation: Max file size before rotation (e.g. "100 MB").
        log_retention: Number of old log files to keep (e.g. "5").
    """
    settings = Settings()

    resolved_level = (log_level or settings.log_level).upper()
    resolved_file = log_file or settings.log_file
    resolved_rotation = log_rotation or settings.log_rotation
    resolved_retention_raw = log_retention or settings.log_retention
    # Loguru accepts int (file count) or a duration string ("30 days").
    # Env vars arrive as strings, so convert pure-digit values to int.
    resolved_retention: int | str = (
        int(resolved_retention_raw)
        if resolved_retention_raw.isdigit()
        else resolved_retention_raw
    )

    # Create logs directory if it doesn't exist
    log_path = Path(resolved_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default loguru handler
    logger.remove()

    # Filter out noisy file-watcher messages that cause a feedback loop:
    # Streamlit's inotify watcher detects writes to the log file, generating
    # a log entry, which writes to the file again, ad infinitum.
    def _drop_file_watcher_noise(record: dict) -> bool:  # type: ignore[type-arg]
        msg = record["message"]
        return "InotifyEvent" not in msg and "in-event" not in msg

    # Console sink
    logger.add(
        sys.stderr,
        level=resolved_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        filter=_drop_file_watcher_noise,
    )

    # File sink with rotation
    logger.add(
        resolved_file,
        level="DEBUG",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        rotation=resolved_rotation,
        retention=resolved_retention,
        compression="zip",
        filter=_drop_file_watcher_noise,
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
