"""Logging setup shared by the CLI and the web server."""

from __future__ import annotations

import logging
import sys

from app.core.config import LogLevel

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%H:%M:%S"

# Third-party loggers that are too chatty at INFO.
_NOISY_LOGGERS = ("httpx", "httpcore", "anthropic")


def configure_logging(level: LogLevel = LogLevel.INFO) -> None:
    """Configure the root logger once; safe to call repeatedly."""
    root = logging.getLogger()
    root.setLevel(level.value)

    if not any(getattr(h, "_app_handler", False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_FORMAT, _DATE_FORMAT))
        handler._app_handler = True  # type: ignore[attr-defined]
        root.addHandler(handler)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
