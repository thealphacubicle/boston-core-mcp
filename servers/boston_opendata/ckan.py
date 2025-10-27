#!/usr/bin/env python3
"""Enhanced CKAN API client with retry logic, connection pooling, and error handling."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)

from .config import (
    settings,
    CKAN_BASE_URL,
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    RETRY_BACKOFF_MULTIPLIER,
    MAX_RETRY_DELAY,
    MAX_RESPONSE_SIZE,
    MAX_REQUEST_SIZE,
)
from .utils.exceptions import (
    APIError,
    TimeoutError,
    ResourceNotFoundError,
    ValidationError,
)
from .utils.logger import get_logger, log_api_call
from .utils.circuit_breaker import ckan_circuit_breaker
from .utils.rate_limiter import rate_limiter


# Global HTTP client for connection pooling
_http_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()


async def get_http_client() -> httpx.AsyncClient:
    """Get or create the global HTTP client with connection pooling."""
    global _http_client

    if _http_client is None:
        async with _client_lock:
            if _http_client is None:
                # Configure timeouts
                timeout = httpx.Timeout(
                    connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=10.0, pool=30.0
                )

                # Configure connection limits
                limits = httpx.Limits(
                    max_connections=settings.max_connections,
                    max_keepalive_connections=settings.max_keepalive_connections,
                    keepalive_expiry=settings.keepalive_expiry,
                )

                _http_client = httpx.AsyncClient(
                    timeout=timeout,
                    limits=limits,
                    follow_redirects=True,
                    max_redirects=5,
                )

    return _http_client


async def close_http_client() -> None:
    """Close the global HTTP client."""
    global _http_client

    if _http_client is not None:
        async with _client_lock:
            if _http_client is not None:
                await _http_client.aclose()
                _http_client = None


def _is_retryable_exception(exception: Exception) -> bool:
    """Check if an exception should trigger a retry."""
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on server errors (5xx) and some client errors (429, 408)
        status_code = exception.response.status_code
        return status_code >= 500 or status_code in [408, 429]

    if isinstance(
        exception, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
    ):
        return True

    return False


@retry(
    stop=stop_after_attempt(MAX_RETRIES + 1),
    wait=wait_exponential(
        multiplier=RETRY_BACKOFF_MULTIPLIER, min=RETRY_DELAY, max=MAX_RETRY_DELAY
    ),
    retry=retry_if_exception_type(
        (
            httpx.HTTPStatusError,
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.NetworkError,
        )
    ),
    before_sleep=before_sleep_log(get_logger("ckan"), logging.WARNING),
    after=after_log(get_logger("ckan"), logging.INFO),
)
async def _make_http_request(
    client: httpx.AsyncClient, url: str, params: Dict[str, Any], method: str = "GET"
) -> httpx.Response:
    """Make an HTTP request with retry logic."""
    start_time = time.time()

    try:
        if method == "GET":
            response = await client.get(url, params=params)
        else:
            response = await client.post(url, json=params)

        # Check response size
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            raise APIError(f"Response too large: {content_length} bytes")

        return response

    except httpx.HTTPStatusError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(
            get_logger("ckan"),
            f"HTTP_{method}",
            url,
            duration_ms,
            status_code=e.response.status_code,
            error_code="HTTP_ERROR",
        )
        raise

    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(
            get_logger("ckan"),
            f"HTTP_{method}",
            url,
            duration_ms,
            error_code="NETWORK_ERROR",
        )
        raise

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(
            get_logger("ckan"),
            f"HTTP_{method}",
            url,
            duration_ms,
            error_code="UNKNOWN_ERROR",
        )
        raise


async def ckan_api_call(
    action: str,
    params: Optional[Dict[str, Any]] = None,
    method: str = "GET",
    client_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Make a request to the CKAN API with enhanced error handling and retry logic.

    Args:
        action: CKAN API action to call
        params: Parameters to send with the request
        method: HTTP method (GET or POST)
        client_id: Client identifier for rate limiting

    Returns:
        API response result data

    Raises:
        APIError: If the API returns an error
        TimeoutError: If the request times out
        ResourceNotFoundError: If the requested resource is not found
        ValidationError: If the request parameters are invalid
    """
    if params is None:
        params = {}

    # Validate action
    if not action or not isinstance(action, str):
        raise ValidationError("Action must be a non-empty string")

    # Validate method
    if method not in ["GET", "POST"]:
        raise ValidationError("Method must be GET or POST")

    # Check request size
    if method == "POST" and params:
        import json

        request_size = len(json.dumps(params).encode("utf-8"))
        if request_size > MAX_REQUEST_SIZE:
            raise ValidationError(f"Request too large: {request_size} bytes")

    url = f"{CKAN_BASE_URL}/{action}"
    logger = get_logger("ckan")

    # Apply rate limiting
    try:
        await rate_limiter.acquire(
            client_id=client_id, tokens=1, burst=False, timeout=30.0
        )
    except Exception as e:
        logger.warning(f"Rate limiting failed: {e}")
        # Continue without rate limiting in case of rate limiter failure

    # Use circuit breaker
    try:
        result = await ckan_circuit_breaker.call(
            _ckan_api_call_internal, action, params, method, client_id
        )
        return result
    except Exception as e:
        if isinstance(e, APIError):
            raise
        raise APIError(f"CKAN API call failed: {str(e)}")


async def _ckan_api_call_internal(
    action: str, params: Dict[str, Any], method: str, client_id: Optional[str]
) -> Dict[str, Any]:
    """Internal CKAN API call implementation."""
    url = f"{CKAN_BASE_URL}/{action}"
    logger = get_logger("ckan")
    start_time = time.time()

    try:
        client = await get_http_client()
        response = await _make_http_request(client, url, params, method)

        # Check for specific HTTP status codes
        if response.status_code == 404:
            raise ResourceNotFoundError(f"Resource not found: {action}")
        elif response.status_code == 429:
            raise APIError("Rate limit exceeded by CKAN API", status_code=429)
        elif response.status_code >= 500:
            raise APIError(
                f"CKAN API server error: {response.status_code}",
                status_code=response.status_code,
            )

        response.raise_for_status()

        # Parse JSON response
        try:
            data = response.json()
        except Exception as e:
            raise APIError(f"Invalid JSON response: {str(e)}")

        # Check CKAN API success flag
        if not data.get("success", False):
            error_info = data.get("error", {})
            if isinstance(error_info, dict):
                error_msg = error_info.get("message", str(error_info))
            else:
                error_msg = str(error_info)

            # Handle specific CKAN errors
            if "not found" in error_msg.lower():
                raise ResourceNotFoundError(f"Resource not found: {error_msg}")
            elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                raise APIError(f"Permission denied: {error_msg}", status_code=403)
            else:
                raise APIError(f"CKAN API Error: {error_msg}")

        result = data.get("result", {})

        # Log successful API call
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(
            logger, f"ckan_{action}", url, duration_ms, status_code=response.status_code
        )

        return result

    except httpx.TimeoutException as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"ckan_{action}", url, duration_ms, error_code="TIMEOUT")
        raise TimeoutError(f"Request timed out after {settings.api_timeout}s")

    except httpx.HTTPStatusError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(
            logger,
            f"ckan_{action}",
            url,
            duration_ms,
            status_code=e.response.status_code,
            error_code="HTTP_ERROR",
        )

        if e.response.status_code == 404:
            raise ResourceNotFoundError(f"Resource not found: {action}")
        elif e.response.status_code == 429:
            raise APIError("Rate limit exceeded", status_code=429)
        else:
            raise APIError(f"HTTP {e.response.status_code}: {e.response.text[:500]}")

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(
            logger, f"ckan_{action}", url, duration_ms, error_code="UNKNOWN_ERROR"
        )
        raise APIError(f"Unexpected error: {str(e)}")


async def health_check() -> Dict[str, Any]:
    """Perform a health check on the CKAN API.

    Returns:
        Health check result with status and details
    """
    logger = get_logger("ckan")

    try:
        # Try a simple API call to check connectivity
        result = await ckan_api_call("status_show")

        return {
            "status": "healthy",
            "ckan_api": "available",
            "timestamp": time.time(),
            "details": result,
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "ckan_api": "unavailable",
            "timestamp": time.time(),
            "error": str(e),
        }
