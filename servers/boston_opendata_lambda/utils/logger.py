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

        # Add timestamp in ISO 8601 format with milliseconds (CloudWatch compatible)
        # Use current time for accurate timestamp
        now = time.time()
        # Format: YYYY-MM-DDTHH:MM:SS.mmmZ
        milliseconds = int((now % 1) * 1000)
        record.timestamp = time.strftime(
            "%Y-%m-%dT%H:%M:%S", time.gmtime(now)
        ) + f".{milliseconds:03d}Z"

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


def extract_request_source(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract request source information from Lambda event.
    
    Args:
        event: Lambda event dictionary
        
    Returns:
        Dictionary with request source information
    """
    source_info = {
        "request_source": "unknown",
        "source_type": "direct_invocation",
        "api_gateway": False,
        "http_method": None,
        "path": None,
        "user_agent": None,
        "source_ip": None,
        "request_id": None,
        "api_id": None,
        "stage": None,
        "resource_path": None,
        "account_id": None,
        "identity": {},
    }
    
    # Check for API Gateway event
    if "requestContext" in event:
        source_info["request_source"] = "api_gateway"
        source_info["source_type"] = "api_gateway"
        source_info["api_gateway"] = True
        
        request_context = event.get("requestContext", {})
        
        # Extract API Gateway v1/v2 information
        if "requestId" in request_context:
            source_info["request_id"] = request_context.get("requestId")
        if "apiId" in request_context:
            source_info["api_id"] = request_context.get("apiId")
        if "stage" in request_context:
            source_info["stage"] = request_context.get("stage")
        if "resourcePath" in request_context:
            source_info["resource_path"] = request_context.get("resourcePath")
        if "accountId" in request_context:
            source_info["account_id"] = request_context.get("accountId")
        if "httpMethod" in request_context:
            source_info["http_method"] = request_context.get("httpMethod")
        if "path" in request_context:
            source_info["path"] = request_context.get("path")
            
        # Extract identity information
        identity = request_context.get("identity", {})
        if identity:
            source_info["identity"] = {
                "source_ip": identity.get("sourceIp"),
                "user_agent": identity.get("userAgent"),
                "user_arn": identity.get("userArn"),
                "cognito_identity_id": identity.get("cognitoIdentityId"),
                "cognito_identity_pool_id": identity.get("cognitoIdentityPoolId"),
            }
            source_info["source_ip"] = identity.get("sourceIp")
            source_info["user_agent"] = identity.get("userAgent")
        
        # API Gateway v2 format
        if "http" in request_context:
            http_info = request_context.get("http", {})
            source_info["http_method"] = http_info.get("method")
            source_info["path"] = http_info.get("path")
            source_info["protocol"] = http_info.get("protocol")
            source_info["user_agent"] = http_info.get("userAgent")
            source_info["source_ip"] = http_info.get("sourceIp")
    
    # Check for direct invocation (EventBridge, SQS, etc.)
    elif "source" in event:
        source_info["request_source"] = event.get("source", "unknown")
        source_info["source_type"] = "eventbridge"
    elif "Records" in event:
        source_info["request_source"] = "sqs"
        source_info["source_type"] = "sqs"
    elif "Records" in event and isinstance(event.get("Records"), list):
        if event["Records"] and "eventSource" in event["Records"][0]:
            source_info["request_source"] = event["Records"][0].get("eventSource", "unknown")
            source_info["source_type"] = event["Records"][0].get("eventSource", "unknown")
    
    return source_info


def sanitize_for_logging(data: Any, max_size: int = 50000) -> Any:
    """Sanitize data for logging by truncating large values.
    
    Args:
        data: Data to sanitize
        max_size: Maximum size in characters for string values
        
    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        return {k: sanitize_for_logging(v, max_size) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_logging(item, max_size) for item in data[:100]]  # Limit to 100 items
    elif isinstance(data, str):
        if len(data) > max_size:
            return data[:max_size] + f"... [truncated {len(data) - max_size} chars]"
        return data
    elif isinstance(data, bytes):
        return f"<bytes: {len(data)} bytes>"
    else:
        return data


def log_lambda_request(
    logger: logging.Logger,
    event: Dict[str, Any],
    context: Any,
    request_id: Optional[str] = None,
) -> None:
    """Log incoming Lambda request with full details.
    
    Args:
        logger: Logger instance
        event: Lambda event dictionary
        context: Lambda context object
        request_id: Optional request ID (will use context if available)
    """
    # Extract request source information
    source_info = extract_request_source(event)
    
    # Get request ID from context or generate one
    if context and hasattr(context, "aws_request_id"):
        request_id = context.aws_request_id
    elif not request_id:
        request_id = str(uuid.uuid4())
    
    # Extract event details
    event_type = type(event).__name__
    event_keys = list(event.keys()) if isinstance(event, dict) else []
    
    # Sanitize event for logging (truncate large values)
    sanitized_event = sanitize_for_logging(event, max_size=10000)
    
    log_data = {
        "component": "lambda_handler",
        "operation": "request_received",
        "request_id": request_id,
        "event_type": event_type,
        "event_keys": event_keys,
        "event_size_bytes": len(json.dumps(event).encode("utf-8")),
        **source_info,
    }
    
    # Add context information if available
    if context:
        context_info = {}
        if hasattr(context, "function_name"):
            context_info["function_name"] = context.function_name
        if hasattr(context, "function_version"):
            context_info["function_version"] = context.function_version
        if hasattr(context, "invoked_function_arn"):
            context_info["invoked_function_arn"] = context.invoked_function_arn
        if hasattr(context, "memory_limit_in_mb"):
            context_info["memory_limit_mb"] = context.memory_limit_in_mb
        if hasattr(context, "remaining_time_in_millis"):
            context_info["remaining_time_ms"] = context.remaining_time_in_millis()
        log_data["lambda_context"] = context_info
    
    logger.info("Lambda request received", extra=log_data)
    
    # Log full event details at DEBUG level
    logger.debug(
        "Full Lambda event details",
        extra={
            "component": "lambda_handler",
            "request_id": request_id,
            "event": sanitized_event,
        },
    )


def log_lambda_response(
    logger: logging.Logger,
    response: Dict[str, Any],
    request_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    status_code: Optional[int] = None,
) -> None:
    """Log Lambda response with full details.
    
    Args:
        logger: Logger instance
        response: Lambda response dictionary
        request_id: Request ID
        duration_ms: Request duration in milliseconds
        status_code: HTTP status code (if applicable)
    """
    # Extract status code from response if not provided
    if status_code is None:
        status_code = response.get("statusCode")
    
    # Sanitize response for logging
    sanitized_response = sanitize_for_logging(response, max_size=10000)
    
    log_data = {
        "component": "lambda_handler",
        "operation": "response_sent",
        "request_id": request_id,
        "status_code": status_code,
        "response_size_bytes": len(json.dumps(response).encode("utf-8")),
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    # Determine success based on status code
    if status_code:
        success = 200 <= status_code < 300
        log_data["success"] = success
        if success:
            logger.info("Lambda response sent successfully", extra=log_data)
        else:
            logger.warning("Lambda response sent with error status", extra=log_data)
    else:
        logger.info("Lambda response sent", extra=log_data)
    
    # Log full response details at DEBUG level
    logger.debug(
        "Full Lambda response details",
        extra={
            "component": "lambda_handler",
            "request_id": request_id,
            "response": sanitized_response,
        },
    )


def log_lambda_error(
    logger: logging.Logger,
    error: Exception,
    request_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    event: Optional[Dict[str, Any]] = None,
) -> None:
    """Log Lambda error with full details.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        request_id: Request ID
        duration_ms: Request duration in milliseconds
        event: Original event (optional)
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    log_data = {
        "component": "lambda_handler",
        "operation": "error_occurred",
        "request_id": request_id,
        "error_type": error_type,
        "error_message": error_message,
        "success": False,
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    if event:
        source_info = extract_request_source(event)
        log_data.update(source_info)
    
    logger.error(
        f"Lambda handler error: {error_type}",
        extra=log_data,
        exc_info=True,
    )


def log_mcp_message(
    logger: logging.Logger,
    message_type: str,
    method: Optional[str] = None,
    request_id: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    result: Optional[Any] = None,
    error: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    **kwargs,
) -> None:
    """Log MCP protocol message with detailed information.
    
    Args:
        logger: Logger instance
        message_type: Type of MCP message (request, response, notification)
        method: MCP method name (e.g., "initialize", "tools/list", "tools/call")
        request_id: MCP request ID
        params: Request parameters
        result: Response result
        error: Error information
        duration_ms: Duration in milliseconds
        **kwargs: Additional fields to include
    """
    log_data = {
        "component": "mcp_protocol",
        "operation": f"mcp_{message_type}",
        "message_type": message_type,
    }
    
    if method:
        log_data["mcp_method"] = method
    if request_id:
        log_data["mcp_request_id"] = request_id
    if params:
        log_data["mcp_params"] = sanitize_for_logging(params, max_size=5000)
    if result is not None:
        log_data["mcp_result"] = sanitize_for_logging(result, max_size=10000)
    if error:
        log_data["mcp_error"] = sanitize_for_logging(error, max_size=2000)
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    log_data.update(kwargs)
    
    if error:
        logger.error(f"MCP {message_type} error: {method}", extra=log_data)
    else:
        logger.info(f"MCP {message_type}: {method}", extra=log_data)


def log_request_processing_status(
    logger: logging.Logger,
    status: str,
    stage: str,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """Log request processing status at various stages.
    
    Args:
        logger: Logger instance
        status: Status of processing (started, in_progress, completed, failed)
        stage: Processing stage (parsing, validation, execution, formatting, etc.)
        request_id: Request ID
        details: Additional details about the stage
        **kwargs: Additional fields to include
    """
    log_data = {
        "component": "request_processor",
        "operation": f"status_{status}",
        "status": status,
        "stage": stage,
    }
    
    if request_id:
        log_data["request_id"] = request_id
    if details:
        log_data["stage_details"] = sanitize_for_logging(details, max_size=5000)
    
    log_data.update(kwargs)
    
    if status == "failed":
        logger.error(f"Request processing failed at stage: {stage}", extra=log_data)
    elif status == "completed":
        logger.info(f"Request processing completed at stage: {stage}", extra=log_data)
    elif status == "started":
        logger.info(f"Request processing started at stage: {stage}", extra=log_data)
    else:
        logger.debug(f"Request processing {status} at stage: {stage}", extra=log_data)

