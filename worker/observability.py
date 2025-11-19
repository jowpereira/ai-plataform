"""Observability utilities for the generic worker runtime."""

from __future__ import annotations

import json
import logging
from logging import Handler
from pathlib import Path
from typing import Final

from worker.config import ObservabilityConfig

_LEVEL_MAP: Final[dict[str, int]] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


class _JsonLogFormatter(logging.Formatter):
    """Simple JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class ObservabilityManager:
    """Configures logging/metrics/tracing based on ObservabilityConfig."""

    def __init__(self, config: ObservabilityConfig):
        self._config = config
        self._logging_configured = False

    def setup(self) -> None:
        """Configure logging (metrics/tracing hooks reserved for future work)."""
        self._configure_logging()
        # Metrics/tracing wiring will be added once exporters are defined in config

    def _configure_logging(self) -> None:
        log_cfg = self._config.logging
        if not log_cfg.enabled:
            return

        root_logger = logging.getLogger()
        level = _LEVEL_MAP.get(log_cfg.level.lower(), logging.INFO)
        root_logger.setLevel(level)

        formatter: logging.Formatter
        if log_cfg.format == "json":
            formatter = _JsonLogFormatter()
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            )

        # Remove handlers we previously configured to avoid duplicates
        for handler in list(root_logger.handlers):
            if getattr(handler, "_worker_managed", False):
                root_logger.removeHandler(handler)

        # Always add console handler for local visibility
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._worker_managed = True  # type: ignore[attr-defined]
        root_logger.addHandler(console_handler)

        if log_cfg.output_path:
            self._configure_file_handler(root_logger, formatter, log_cfg.output_path)

        self._logging_configured = True

    def _configure_file_handler(
        self,
        logger: logging.Logger,
        formatter: logging.Formatter,
        output_path: str,
    ) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler._worker_managed = True  # type: ignore[attr-defined]
        logger.addHandler(file_handler)

    def register_handler(self, handler: Handler) -> None:
        """Allow callers to register extra handlers after base setup."""
        handler._worker_managed = True  # type: ignore[attr-defined]
        logging.getLogger().addHandler(handler)

    def is_logging_configured(self) -> bool:
        """Return True once logging handlers were added."""
        return self._logging_configured
