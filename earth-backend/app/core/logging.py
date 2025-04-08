import json
import logging
import sys
from typing import Any

from app.core.config import settings


class JSONLogFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after parsing the log record."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_object: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if hasattr(record, "props"):
            log_object.update(record.props)

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_object)


def setup_logging(log_level: str | None = None) -> None:
    """Configure logging with JSON formatter for structured logging."""
    print(settings.LOG_LEVEL)
    level = log_level or settings.LOG_LEVEL or "INFO"
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise TypeError(f"Invalid log level: {level}")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler that outputs JSON
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONLogFormatter())
    root_logger.addHandler(console_handler)

    # Set level for specific loggers if needed
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name, preconfigured for structured logging."""
    logger = logging.getLogger(name)

    # Enhance the logger with a method for adding structured context
    def with_context(self: logging.Logger, **kwargs: Any) -> logging.Logger:
        """Return a logger with the specified context attached to log records."""
        old_factory = self.makeRecord

        def factory(*args: Any, **kwargs_inner: Any) -> logging.LogRecord:
            record = old_factory(*args, **kwargs_inner)
            record.props = getattr(record, "props", {})
            record.props.update(kwargs)
            return record

        self.makeRecord = factory
        return self

    logger.with_context = with_context.__get__(logger)
    return logger
