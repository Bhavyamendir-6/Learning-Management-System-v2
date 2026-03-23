"""
utils/logging_config.py — Centralized logging configuration for the LMS Agent.

Call setup_logging() exactly once at application startup (fastapi_backend/app.py).
All other modules just do:  logger = logging.getLogger(__name__)

Environment variables:
  LOG_LEVEL   — DEBUG | INFO | WARNING | ERROR  (default: INFO)
  LOG_TO_FILE — true | false                    (default: true)
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_dir: Path | None = None) -> None:
    """
    Configure root logging for the entire LMS application.

    - Reads LOG_LEVEL from environment (default: INFO).
    - Writes to console + rotating file (5 MB × 3 backups) unless LOG_TO_FILE=false.
    - Silences noisy third-party libraries at WARNING.
    - Safe to call multiple times — uses force=True to reconfigure cleanly.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(level)

    handlers: list[logging.Handler] = [console_handler]

    log_to_file = os.getenv("LOG_TO_FILE", "true").lower() != "false"
    if log_to_file:
        if log_dir is None:
            log_dir = Path(__file__).resolve().parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "lms_agent.log",
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        file_handler.setLevel(level)
        handlers.append(file_handler)

    # force=True tears down any handlers added before this call
    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Silence noisy third-party loggers
    _QUIET_LOGGERS = (
        "httpx",
        "httpcore",
        "google.auth",
        "google.auth.transport",
        "urllib3",
        "asyncio",
        "multipart",
        "uvicorn.access",  # HTTP access log is handled by our middleware
    )
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "[logging_config] Logging initialized | level=%s | file=%s",
        level_name,
        str(log_dir / "lms_agent.log") if log_to_file else "disabled",
    )
