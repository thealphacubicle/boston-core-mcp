#!/usr/bin/env python3
"""Structured logging setup for the Boston OpenData MCP server."""

import json
import logging
import sys
import time
import uuid
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Add request ID if not present
        if not hasattr(record, "request_id"):
            record.request_id = getattr(record, "request_id", str(uuid.uuid4())[:8])

        # Add timestamp in ISO format
        record.timestamp = time.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime(record.created)
        )

        return True


def setup_logging(
    level: str = "INFO", format_type: str = "json", include_extra: bool = True
) -> logging.Logger:
    """Set up structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type ("json" or "text")
        include_extra: Whether to include extra fields in JSON logs

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("boston_opendata")
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, level.upper()))

    # Set formatter
    if format_type == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(levelname)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
        )

    handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())

    logger.addHandler(handler)

    # Prevent duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (defaults to "boston_opendata")

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"boston_opendata.{name}")
    return logging.getLogger("boston_opendata")


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


def log_api_call(
    logger: logging.Logger,
    operation: str,
    endpoint: str,
    duration_ms: float,
    status_code: Optional[int] = None,
    error_code: Optional[str] = None,
    **kwargs,
) -> None:
    """Log an API call with structured data.

    Args:
        logger: Logger instance
        operation: Operation being performed
        endpoint: API endpoint being called
        duration_ms: Duration in milliseconds
        status_code: HTTP status code (if applicable)
        error_code: Error code (if applicable)
        **kwargs: Additional fields to include in log
    """
    log_data = {
        "component": "api_client",
        "operation": operation,
        "api_endpoint": endpoint,
        "duration_ms": duration_ms,
    }

    if status_code is not None:
        log_data["status_code"] = status_code

    if error_code is not None:
        log_data["error_code"] = error_code

    log_data.update(kwargs)

    if error_code:
        logger.error(f"API call failed: {operation}", extra=log_data)
    else:
        logger.info(f"API call completed: {operation}", extra=log_data)


def log_tool_execution(
    logger: logging.Logger,
    tool_name: str,
    duration_ms: float,
    success: bool,
    error_code: Optional[str] = None,
    **kwargs,
) -> None:
    """Log tool execution with structured data.

    Args:
        logger: Logger instance
        tool_name: Name of the tool being executed
        duration_ms: Duration in milliseconds
        success: Whether the execution was successful
        error_code: Error code (if applicable)
        **kwargs: Additional fields to include in log
    """
    log_data = {
        "component": "tool_handler",
        "operation": f"tool_{tool_name}",
        "duration_ms": duration_ms,
        "success": success,
    }

    if error_code is not None:
        log_data["error_code"] = error_code

    log_data.update(kwargs)

    if success:
        logger.info(f"Tool executed successfully: {tool_name}", extra=log_data)
    else:
        logger.error(f"Tool execution failed: {tool_name}", extra=log_data)

