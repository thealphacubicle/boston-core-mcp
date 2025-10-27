"""Utility modules for the Boston OpenData MCP server."""

from .circuit_breaker import ckan_circuit_breaker
from .exceptions import (
    APIError,
    TimeoutError,
    ResourceNotFoundError,
    ValidationError,
    RateLimitError,
    CircuitBreakerError,
    ConfigurationError,
)
from .formatters import (
    format_dataset_summary,
    format_resource_info,
    format_error_message,
    format_health_status,
    format_api_response_summary,
)
from .logger import get_logger, setup_logging, log_api_call, log_tool_execution
from .rate_limiter import rate_limiter
from .validators import validate_tool_request, validate_pagination_params

__all__ = [
    "ckan_circuit_breaker",
    "APIError",
    "TimeoutError",
    "ResourceNotFoundError",
    "ValidationError",
    "RateLimitError",
    "CircuitBreakerError",
    "ConfigurationError",
    "format_dataset_summary",
    "format_resource_info",
    "format_error_message",
    "format_health_status",
    "format_api_response_summary",
    "get_logger",
    "setup_logging",
    "log_api_call",
    "log_tool_execution",
    "rate_limiter",
    "validate_tool_request",
    "validate_pagination_params",
]
