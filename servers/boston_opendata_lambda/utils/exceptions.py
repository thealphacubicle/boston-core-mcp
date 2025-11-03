#!/usr/bin/env python3
"""Custom exception classes for the Boston OpenData MCP server."""

from typing import Any, Dict, Optional


class OpenDataMCPError(Exception):
    """Base exception for all OpenData MCP errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(OpenDataMCPError):
    """Raised when input validation fails."""

    def __init__(
        self, message: str, field: Optional[str] = None, value: Optional[Any] = None
    ):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": value})
        self.field = field
        self.value = value


class APIError(OpenDataMCPError):
    """Raised when CKAN API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        api_error: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message, "API_ERROR", {"status_code": status_code, "api_error": api_error}
        )
        self.status_code = status_code
        self.api_error = api_error


class RateLimitError(OpenDataMCPError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", {"retry_after": retry_after})
        self.retry_after = retry_after


class TimeoutError(OpenDataMCPError):
    """Raised when a request times out."""

    def __init__(self, message: str, timeout_duration: Optional[float] = None):
        super().__init__(
            message, "TIMEOUT_ERROR", {"timeout_duration": timeout_duration}
        )
        self.timeout_duration = timeout_duration


class CircuitBreakerError(OpenDataMCPError):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_state: Optional[str] = None):
        super().__init__(
            message, "CIRCUIT_BREAKER_ERROR", {"circuit_state": circuit_state}
        )
        self.circuit_state = circuit_state


class ResourceNotFoundError(OpenDataMCPError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            "RESOURCE_NOT_FOUND",
            {"resource_type": resource_type, "resource_id": resource_id},
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConfigurationError(OpenDataMCPError):
    """Raised when there's a configuration error."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR", {"config_key": config_key})
        self.config_key = config_key

