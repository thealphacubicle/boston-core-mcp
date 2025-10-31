#!/usr/bin/env python3
"""MCPEngine-based Boston OpenData MCP server for AWS Lambda deployment."""

import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import httpx
from mcpengine import MCPEngine

# Import shared components
from .ckan import ckan_api_call, health_check, close_http_client
from .config import settings, MAX_RECORDS
from .utils.formatters import (
    format_dataset_summary,
    format_resource_info,
    format_error_message,
    format_api_response_summary,
)
from .utils.exceptions import (
    ValidationError,
    APIError,
    TimeoutError,
    ResourceNotFoundError,
    RateLimitError,
    CircuitBreakerError,
)
from .utils.validators import (
    validate_tool_request,
    validate_pagination_params,
)
from .utils.logger import get_logger, setup_logging, log_tool_execution

# Initialize logger
logger = get_logger("lambda_server")


# ============================================================================
# Context Management
# ============================================================================


@asynccontextmanager
async def app_lifespan(app=None):
    """Manage application lifecycle for HTTP client and other resources.

    Args:
        app: The MCPEngine app instance (passed by MCPEngine, may be unused)
    """
    logger.info(
        "Initializing application lifespan",
        extra={
            "component": "lifespan",
            "environment": settings.environment,
            "debug_mode": settings.debug,
        },
    )

    # Initialize HTTP client
    logger.debug(
        "Creating HTTP client",
        extra={
            "connect_timeout": settings.connect_timeout,
            "read_timeout": settings.read_timeout,
            "max_connections": settings.max_connections,
            "max_keepalive_connections": settings.max_keepalive_connections,
        },
    )

    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=settings.connect_timeout,
            read=settings.read_timeout,
            write=10.0,
            pool=30.0,
        ),
        limits=httpx.Limits(
            max_connections=settings.max_connections,
            max_keepalive_connections=settings.max_keepalive_connections,
            keepalive_expiry=settings.keepalive_expiry,
        ),
        follow_redirects=True,
        max_redirects=5,
    )

    logger.info("HTTP client initialized successfully", extra={"component": "lifespan"})

    try:
        yield {"http_client": http_client}
    finally:
        logger.debug("Closing HTTP client", extra={"component": "lifespan"})
        await http_client.aclose()
        logger.info("HTTP client closed", extra={"component": "lifespan"})


# ============================================================================
# MCPEngine Setup
# ============================================================================

# Initialize MCPEngine with context management
logger.info(
    "Initializing MCPEngine",
    extra={
        "component": "engine",
        "has_lifespan": True,
    },
)
engine = MCPEngine(lifespan=app_lifespan)
logger.info("MCPEngine initialized successfully", extra={"component": "engine"})


# ============================================================================
# MCPEngine Tool Definitions
# ============================================================================


@engine.tool()
async def search_datasets(query: str, limit: int = 10) -> str:
    """Search for datasets on Boston's Open Data portal.

    Use keywords like '311', 'crime', 'permits', 'parking', etc.
    Returns matching datasets with descriptions and IDs.

    Args:
        query: Search keywords (e.g., '311', 'crime', 'building permits')
        limit: Maximum number of results to return (1-100)

    Returns:
        Formatted string with search results
    """
    start_time = time.time()
    tool_name = "search_datasets"

    logger.info(
        f"Tool execution started: {tool_name}",
        extra={
            "tool": tool_name,
            "query": query,
            "requested_limit": limit,
        },
    )

    try:
        # Validate parameters
        if not query or not isinstance(query, str):
            logger.warning(
                f"Validation failed for {tool_name}",
                extra={"tool": tool_name, "error": "Query must be a non-empty string"},
            )
            return format_error_message(
                "Validation Error", "Query must be a non-empty string"
            )

        if not isinstance(limit, int) or limit < 1 or limit > 100:
            logger.debug(
                f"Limit adjusted for {tool_name}",
                extra={
                    "tool": tool_name,
                    "requested_limit": limit,
                    "adjusted_limit": 10,
                },
            )
            limit = 10

        # Make API call
        client_id = f"req_{int(time.time() * 1000)}"
        logger.debug(
            f"Making CKAN API call for {tool_name}",
            extra={
                "tool": tool_name,
                "action": "package_search",
                "client_id": client_id,
            },
        )

        result = await ckan_api_call(
            "package_search",
            {"q": query, "rows": limit},
            client_id=client_id,
        )

        datasets = result.get("results", [])
        total_count = result.get("count", 0)

        logger.debug(
            f"CKAN API call completed for {tool_name}",
            extra={
                "tool": tool_name,
                "total_count": total_count,
                "returned_count": len(datasets),
            },
        )

        if not datasets:
            logger.info(
                f"No datasets found for {tool_name}",
                extra={"tool": tool_name, "query": query},
            )
            return f"🔍 No datasets found matching '{query}'"

        output = f"🔍 Found {total_count} dataset(s) matching '{query}' (showing {len(datasets)}):\n\n"
        for i, dataset in enumerate(datasets, 1):
            output += format_dataset_summary(dataset, i) + "\n"

        output += "\n💡 **Next steps:**\n"
        output += "• Use `get_dataset_info` with a dataset ID to see resources\n"
        output += "• Use `query_datastore` with a resource ID to get actual data"

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger, tool_name, duration_ms, success=True, datasets_found=len(datasets)
        )

        return output

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_code = type(e).__name__

        logger.error(
            f"Tool execution failed: {tool_name}",
            extra={
                "tool": tool_name,
                "error": str(e),
                "error_type": error_code,
                "query": query,
            },
            exc_info=True,
        )

        if isinstance(e, ValidationError):
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="VALIDATION_ERROR",
            )
            return format_error_message("Validation Error", str(e))
        elif isinstance(e, APIError):
            log_tool_execution(
                logger, tool_name, duration_ms, success=False, error_code="API_ERROR"
            )
            return format_error_message("API Error", str(e))
        else:
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="INTERNAL_ERROR",
            )
            return format_error_message(
                "Internal Error", f"An unexpected error occurred: {str(e)}"
            )


@engine.tool()
async def list_all_datasets(limit: int = 20) -> str:
    """List all available datasets on Boston's Open Data portal.

    Returns dataset names/IDs. Use this to browse what's available.

    Args:
        limit: Number of datasets to return (1-100)

    Returns:
        Formatted string with list of datasets
    """
    start_time = time.time()
    tool_name = "list_all_datasets"

    logger.info(
        f"Tool execution started: {tool_name}",
        extra={"tool": tool_name, "requested_limit": limit},
    )

    try:
        # Validate parameters
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            logger.debug(
                f"Limit adjusted for {tool_name}",
                extra={
                    "tool": tool_name,
                    "requested_limit": limit,
                    "adjusted_limit": 20,
                },
            )
            limit = 20

        # Make API call
        client_id = f"req_{int(time.time() * 1000)}"
        logger.debug(
            f"Making CKAN API call for {tool_name}",
            extra={"tool": tool_name, "action": "package_list", "client_id": client_id},
        )

        dataset_names = await ckan_api_call(
            "package_list", {"limit": limit}, client_id=client_id
        )

        if not dataset_names:
            logger.info(f"No datasets found for {tool_name}", extra={"tool": tool_name})
            return "No datasets found on Boston's Open Data portal."

        logger.debug(
            f"CKAN API call completed for {tool_name}",
            extra={"tool": tool_name, "dataset_count": len(dataset_names)},
        )

        output = f"📚 Boston Open Data Datasets (showing {len(dataset_names)}):\n\n"
        for i, dn in enumerate(dataset_names, 1):
            output += f"{i}. `{dn}`\n"
        output += "\n💡 Use `get_dataset_info` with a dataset ID to see details."

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            tool_name,
            duration_ms,
            success=True,
            datasets_returned=len(dataset_names),
        )

        return output

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_code = type(e).__name__

        logger.error(
            f"Tool execution failed: {tool_name}",
            extra={"tool": tool_name, "error": str(e), "error_type": error_code},
            exc_info=True,
        )

        if isinstance(e, ValidationError):
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="VALIDATION_ERROR",
            )
            return format_error_message("Validation Error", str(e))
        elif isinstance(e, APIError):
            log_tool_execution(
                logger, tool_name, duration_ms, success=False, error_code="API_ERROR"
            )
            return format_error_message("API Error", str(e))
        else:
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="INTERNAL_ERROR",
            )
            return format_error_message(
                "Internal Error", f"An unexpected error occurred: {str(e)}"
            )


@engine.tool()
async def get_dataset_info(dataset_id: str) -> str:
    """Get detailed information about a specific dataset, including all its resources.

    Use the dataset ID (name) from search results.
    This shows you resource IDs needed to query the actual data.

    Args:
        dataset_id: Dataset ID or name (e.g., '311-service-requests', 'crime-incident-reports')

    Returns:
        Formatted string with dataset details
    """
    start_time = time.time()
    tool_name = "get_dataset_info"

    logger.info(
        f"Tool execution started: {tool_name}",
        extra={"tool": tool_name, "dataset_id": dataset_id},
    )

    try:
        # Validate parameters
        if not dataset_id or not isinstance(dataset_id, str):
            logger.warning(
                f"Validation failed for {tool_name}",
                extra={
                    "tool": tool_name,
                    "error": "Dataset ID must be a non-empty string",
                },
            )
            return format_error_message(
                "Validation Error", "Dataset ID must be a non-empty string"
            )

        # Make API call
        client_id = f"req_{int(time.time() * 1000)}"
        logger.debug(
            f"Making CKAN API call for {tool_name}",
            extra={
                "tool": tool_name,
                "action": "package_show",
                "dataset_id": dataset_id,
                "client_id": client_id,
            },
        )

        dataset = await ckan_api_call(
            "package_show",
            {"id": dataset_id},
            client_id=client_id,
        )

        title = dataset.get("title", "Untitled Dataset")
        name = dataset.get("name", "N/A")
        notes = dataset.get("notes", "No description available")
        resources = dataset.get("resources", [])

        queryable_resources = [r for r in resources if r.get("datastore_active")]

        logger.debug(
            f"CKAN API call completed for {tool_name}",
            extra={
                "tool": tool_name,
                "dataset_id": dataset_id,
                "dataset_name": name,
                "resource_count": len(resources),
                "queryable_resources": len(queryable_resources),
            },
        )

        output = f"📊 **{title}**\n\n"
        output += f"🆔 Dataset ID: `{name}`\n"
        output += f"🔗 URL: https://data.boston.gov/dataset/{name}\n\n"
        output += f"📝 **Description:**\n{notes}\n\n"

        if dataset.get("organization"):
            org = dataset["organization"]
            output += f"🏛️  Organization: {org.get('title', 'Unknown')}\n"
        if dataset.get("metadata_created"):
            output += f"📅 Created: {dataset['metadata_created'][:10]}\n"
        if dataset.get("metadata_modified"):
            output += f"🔄 Updated: {dataset['metadata_modified'][:10]}\n"

        output += f"\n📁 **Resources ({len(resources)}):**\n\n"
        if not resources:
            output += "No resources available.\n"
        else:
            for i, resource in enumerate(resources, 1):
                output += format_resource_info(resource, i) + "\n"

        if queryable_resources:
            output += "\n✅ **Queryable Resources:**\n"
            for r in queryable_resources:
                output += f"• `{r['id']}` - {r.get('name', 'Unnamed')}\n"
            output += "\n💡 Use `query_datastore` with a resource ID above to get data."
        else:
            output += "\n⚠️  No queryable resources found. These may be downloadable files only."

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            tool_name,
            duration_ms,
            success=True,
            dataset_id=dataset_id,
            resource_count=len(resources),
            queryable_count=len(queryable_resources),
        )

        return output

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_code = type(e).__name__

        logger.error(
            f"Tool execution failed: {tool_name}",
            extra={
                "tool": tool_name,
                "dataset_id": dataset_id,
                "error": str(e),
                "error_type": error_code,
            },
            exc_info=True,
        )

        if isinstance(e, ValidationError):
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="VALIDATION_ERROR",
            )
            return format_error_message("Validation Error", str(e))
        elif isinstance(e, ResourceNotFoundError):
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="RESOURCE_NOT_FOUND",
            )
            return format_error_message("Resource Not Found", str(e))
        elif isinstance(e, APIError):
            log_tool_execution(
                logger, tool_name, duration_ms, success=False, error_code="API_ERROR"
            )
            return format_error_message("API Error", str(e))
        else:
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="INTERNAL_ERROR",
            )
            return format_error_message(
                "Internal Error", f"An unexpected error occurred: {str(e)}"
            )


@engine.tool()
async def query_datastore(
    resource_id: str,
    limit: int = 10,
    offset: int = 0,
    search_text: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    sort: Optional[str] = None,
    fields: Optional[List[str]] = None,
) -> str:
    """Query actual data from a DataStore resource.

    You must have the resource_id from get_dataset_info.
    Supports filtering, searching, sorting, and limiting results.

    Args:
        resource_id: Resource ID (UUID format) from get_dataset_info
        limit: Number of records to return (1-1000)
        offset: Number of records to skip (for pagination)
        search_text: Full-text search across all fields (optional)
        filters: Filter by specific field values (optional)
        sort: Sort by field name. Use 'field_name asc' or 'field_name desc'
        fields: Specific fields to return (optional)

    Returns:
        Formatted string with query results
    """
    start_time = time.time()
    tool_name = "query_datastore"

    logger.info(
        f"Tool execution started: {tool_name}",
        extra={
            "tool": tool_name,
            "resource_id": resource_id,
            "limit": limit,
            "offset": offset,
            "has_search_text": search_text is not None,
            "has_filters": filters is not None,
            "has_sort": sort is not None,
            "has_fields": fields is not None,
        },
    )

    try:
        # Validate parameters
        if not resource_id or not isinstance(resource_id, str):
            logger.warning(
                f"Validation failed for {tool_name}",
                extra={
                    "tool": tool_name,
                    "error": "Resource ID must be a non-empty string",
                },
            )
            return format_error_message(
                "Validation Error", "Resource ID must be a non-empty string"
            )

        # Validate pagination parameters
        limit, offset = validate_pagination_params(limit, offset, MAX_RECORDS)

        logger.debug(
            f"Pagination parameters validated for {tool_name}",
            extra={"tool": tool_name, "limit": limit, "offset": offset},
        )

        # Build query parameters
        params = {"resource_id": resource_id, "limit": limit, "offset": offset}
        if search_text:
            params["q"] = search_text
        if filters:
            params["filters"] = json.dumps(filters)
        if sort:
            params["sort"] = sort
        if fields:
            params["fields"] = ",".join(fields)

        # Make API call
        client_id = f"req_{int(time.time() * 1000)}"
        logger.debug(
            f"Making CKAN API call for {tool_name}",
            extra={
                "tool": tool_name,
                "action": "datastore_search",
                "resource_id": resource_id,
                "client_id": client_id,
                "query_params_keys": list(params.keys()),
            },
        )

        result = await ckan_api_call("datastore_search", params, client_id=client_id)
        records = result.get("records", [])
        total = result.get("total", 0)
        fields_info = result.get("fields", [])

        logger.debug(
            f"CKAN API call completed for {tool_name}",
            extra={
                "tool": tool_name,
                "resource_id": resource_id,
                "total_records": total,
                "returned_records": len(records),
                "field_count": len(fields_info),
            },
        )

        if not records:
            logger.info(
                f"No records found for {tool_name}",
                extra={"tool": tool_name, "resource_id": resource_id},
            )
            return "No records found matching your query."

        # Format response
        output = format_api_response_summary(
            total, len(records), offset, total > (offset + limit)
        )

        field_names = [f.get("id") for f in fields_info if f.get("id") != "_id"]
        output += f"**Fields:** {', '.join(field_names[:10])}"
        if len(field_names) > 10:
            output += f" ... (+{len(field_names) - 10} more)"
        output += "\n\n"

        output += "**Records:**\n\n"
        for i, record in enumerate(records[:20], 1):
            output += f"**Record {i + offset}:**\n"
            displayed_fields = field_names[:8] if not fields else fields[:8]
            for field in displayed_fields:
                value = record.get(field, "N/A")
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                elif value is None:
                    value = "N/A"
                output += f"  • **{field}:** {value}\n"
            if len(field_names) > 8 and not fields:
                output += f"  • ... (+{len(field_names) - 8} more fields)\n"
            output += "\n"

        if len(records) > 20:
            output += f"... and {len(records) - 20} more records\n\n"

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            tool_name,
            duration_ms,
            success=True,
            resource_id=resource_id,
            total_records=total,
            returned_records=len(records),
            field_count=len(field_names),
        )

        return output

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_code = type(e).__name__

        logger.error(
            f"Tool execution failed: {tool_name}",
            extra={
                "tool": tool_name,
                "resource_id": resource_id,
                "error": str(e),
                "error_type": error_code,
            },
            exc_info=True,
        )

        if isinstance(e, ValidationError):
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="VALIDATION_ERROR",
            )
            return format_error_message("Validation Error", str(e))
        elif isinstance(e, ResourceNotFoundError):
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="RESOURCE_NOT_FOUND",
            )
            return format_error_message("Resource Not Found", str(e))
        elif isinstance(e, APIError):
            log_tool_execution(
                logger, tool_name, duration_ms, success=False, error_code="API_ERROR"
            )
            return format_error_message("API Error", str(e))
        else:
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="INTERNAL_ERROR",
            )
            return format_error_message(
                "Internal Error", f"An unexpected error occurred: {str(e)}"
            )


@engine.tool()
async def get_datastore_schema(resource_id: str) -> str:
    """Get the schema/structure of a DataStore resource.

    Shows field names, data types, and descriptions.
    Useful before querying to understand available fields.

    Args:
        resource_id: Resource ID to get schema for

    Returns:
        Formatted string with schema information
    """
    start_time = time.time()
    tool_name = "get_datastore_schema"

    logger.info(
        f"Tool execution started: {tool_name}",
        extra={"tool": tool_name, "resource_id": resource_id},
    )

    try:
        # Validate parameters
        if not resource_id or not isinstance(resource_id, str):
            logger.warning(
                f"Validation failed for {tool_name}",
                extra={
                    "tool": tool_name,
                    "error": "Resource ID must be a non-empty string",
                },
            )
            return format_error_message(
                "Validation Error", "Resource ID must be a non-empty string"
            )

        # Make API call
        client_id = f"req_{int(time.time() * 1000)}"
        logger.debug(
            f"Making CKAN API call for {tool_name}",
            extra={
                "tool": tool_name,
                "action": "datastore_search",
                "resource_id": resource_id,
                "client_id": client_id,
            },
        )

        result = await ckan_api_call(
            "datastore_search",
            {"resource_id": resource_id, "limit": 0},
            client_id=client_id,
        )
        fields = result.get("fields", [])

        logger.debug(
            f"CKAN API call completed for {tool_name}",
            extra={
                "tool": tool_name,
                "resource_id": resource_id,
                "field_count": len(fields),
            },
        )

        if not fields:
            logger.info(
                f"No schema information available for {tool_name}",
                extra={"tool": tool_name, "resource_id": resource_id},
            )
            return "No schema information available for this resource."

        output = f"📋 **DataStore Schema**\n\n"
        output += f"🆔 Resource ID: `{resource_id}`\n"
        output += f"📊 Total fields: {len(fields)}\n\n"
        output += "**Fields:**\n\n"

        for field in fields:
            field_id = field.get("id", "unknown")
            field_type = field.get("type", "unknown")
            if field_id == "_id":
                continue
            output += f"• **{field_id}**\n"
            output += f"  Type: `{field_type}`\n\n"

        output += "\n💡 Use `query_datastore` with this resource_id to fetch data."

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            tool_name,
            duration_ms,
            success=True,
            resource_id=resource_id,
            field_count=len(fields),
        )

        return output

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_code = type(e).__name__

        logger.error(
            f"Tool execution failed: {tool_name}",
            extra={
                "tool": tool_name,
                "resource_id": resource_id,
                "error": str(e),
                "error_type": error_code,
            },
            exc_info=True,
        )

        if isinstance(e, ValidationError):
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="VALIDATION_ERROR",
            )
            return format_error_message("Validation Error", str(e))
        elif isinstance(e, ResourceNotFoundError):
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="RESOURCE_NOT_FOUND",
            )
            return format_error_message("Resource Not Found", str(e))
        elif isinstance(e, APIError):
            log_tool_execution(
                logger, tool_name, duration_ms, success=False, error_code="API_ERROR"
            )
            return format_error_message("API Error", str(e))
        else:
            log_tool_execution(
                logger,
                tool_name,
                duration_ms,
                success=False,
                error_code="INTERNAL_ERROR",
            )
            return format_error_message(
                "Internal Error", f"An unexpected error occurred: {str(e)}"
            )


# ============================================================================
# Lambda Handler
# ============================================================================

# Create Lambda-compatible handler
logger.debug("Creating Lambda handler", extra={"component": "handler"})
handler = engine.get_lambda_handler()
logger.info("Lambda handler created successfully", extra={"component": "handler"})


# ============================================================================
# Health Check (for testing)
# ============================================================================


async def perform_health_check() -> Dict[str, Any]:
    """Perform a health check for monitoring."""
    logger.info("Health check initiated", extra={"component": "health_check"})

    try:
        ckan_health = await health_check()
        is_healthy = ckan_health["status"] == "healthy"

        logger.info(
            "Health check completed",
            extra={
                "component": "health_check",
                "status": "healthy" if is_healthy else "unhealthy",
                "ckan_api_status": ckan_health.get("status"),
            },
        )

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": time.time(),
            "details": {
                "ckan_api": ckan_health,
                "environment": settings.environment,
                "version": "1.0.0",
            },
        }
    except Exception as e:
        logger.error(
            "Health check failed",
            extra={
                "component": "health_check",
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e),
        }


# ============================================================================
# Local Development Server (for testing)
# ============================================================================

if __name__ == "__main__":
    # For local testing, use MCPEngine's built-in HTTP server
    import uvicorn

    # Initialize logging for local development
    setup_logging(level=settings.log_level, format_type=settings.log_format)

    logger.info(
        "Starting Boston OpenData MCP Server (Lambda version) for local testing",
        extra={
            "component": "server",
            "mode": "local_development",
            "environment": settings.environment,
            "host": "0.0.0.0",
            "port": 8000,
        },
    )

    logger.info(
        "Server configuration",
        extra={
            "component": "server",
            "server_url": "http://localhost:8000",
            "proxy_command": "mcpengine proxy boston-opendata-lambda http://localhost:8000 --mode http --claude",
        },
    )

    # Use MCPEngine's built-in HTTP app
    # MCPEngine provides http_app() which returns a Starlette-compatible app
    http_app = engine.http_app()

    logger.info(
        "HTTP app initialized, starting uvicorn server",
        extra={"component": "server", "log_level": "info"},
    )

    # Start the server using uvicorn
    uvicorn.run(http_app, host="0.0.0.0", port=8000, log_level="info")
