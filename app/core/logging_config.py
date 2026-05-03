"""
Structured logging setup controlled via environment variables.

When ``LOG_FORMAT=json``, emits JSON lines suitable for log aggregators;
otherwise prints human-readable console lines for local development.
"""

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    """
    Configure the root logger level and handler format.

    Args:
        settings: Parsed application settings (level + format).
    """
    level = getattr(logging, settings.log_level)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if settings.log_format == "json":
        formatter: logging.Formatter = jsonlogger.JsonFormatter(
            "%(levelname)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "name": "logger"},
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    handler.setFormatter(formatter)
    root.addHandler(handler)


def log_extra(**kwargs: Any) -> dict[str, Any]:
    """
    Helper for attaching structured fields to log records.

    Returns:
        Dict suitable as ``extra=`` for ``logger.info(...)`` etc.
    """
    return kwargs
