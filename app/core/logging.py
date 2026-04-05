"""Logging utilities for the application."""

from __future__ import annotations

import logging

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level_name: str = "INFO") -> int:
    """Configure root logging once for the current process.

    Args:
        level_name: Desired root log level.

    Returns:
        Resolved numeric log level.
    """
    level = getattr(logging, str(level_name).upper(), logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(level=level, format=DEFAULT_LOG_FORMAT)
    else:
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)

    return level


def get_logger(name: str) -> logging.Logger:
    """Return a named application logger.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)

