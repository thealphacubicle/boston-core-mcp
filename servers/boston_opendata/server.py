#!/usr/bin/env python3
"""Production-ready Boston OpenData MCP server with enhanced error handling and validation."""

import json
import sys
import time
from typing import Any, Dict, List, Optional

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

from .ckan import ckan_api_call, health_check, close_http_client
from .utils.formatters import (
    format_dataset_summary,
    format_resource_info,
    format_error_message,
    format_health_status,
    format_api_response_summary,
)
from .config import settings, MAX_RECORDS
from .utils.exceptions import (
    ValidationError,
    APIError,
    TimeoutError,
    ResourceNotFoundError,
    RateLimitError,
    CircuitBreakerError,
)
from .utils.validators import validate_tool_request, validate_pagination_params
from .utils.logger import get_logger, log_tool_execution, setup_logging
from .utils.rate_limiter import rate_limiter


# ============================================================================
# Server Setup
# ============================================================================

# Initialize logging
logger = setup_logging(
    level=settings.log_level,
    format_type=settings.log_format,
    include_extra=settings.log_include_extra,
)

app = Server("boston-opendata-server")

# Health check state
_health_status = {"status": "starting", "last_check": None, "details": {}}


# ============================================================================
# MCP Tool Definitions
# ============================================================================


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Define available MCP tools for Boston Open Data"""
    return [
        Tool(
            name="search_datasets",
            description=(
                "Search for datasets on Boston's Open Data portal. "
                "Use keywords like '311', 'crime', 'permits', 'parking', etc. "
                "Returns matching datasets with descriptions and IDs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords (e.g., '311', 'crime', 'building permits')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (1-100)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="list_all_datasets",
            description=(
                "List all available datasets on Boston's Open Data portal. "
                "Returns dataset names/IDs. Use this to browse what's available."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of datasets to return (1-100)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    }
                },
            },
        ),
        Tool(
            name="get_dataset_info",
            description=(
                "Get detailed information about a specific dataset, including all its resources. "
                "Use the dataset ID (name) from search results. "
                "This shows you resource IDs needed to query the actual data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": (
                            "Dataset ID or name (e.g., '311-service-requests', 'crime-incident-reports'). "
                            "Get this from search_datasets results."
                        ),
                    }
                },
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="query_datastore",
            description=(
                "Query actual data from a DataStore resource. "
                "You must have the resource_id from get_dataset_info. "
                "Supports filtering, searching, sorting, and limiting results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_id": {
                        "type": "string",
                        "description": (
                            "Resource ID (UUID format) from get_dataset_info. "
                            "Only resources with DataStore active can be queried."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of records to return (1-1000)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 1000,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of records to skip (for pagination)",
                        "default": 0,
                        "minimum": 0,
                    },
                    "search_text": {
                        "type": "string",
                        "description": "Full-text search across all fields (optional)",
                    },
                    "filters": {
                        "type": "object",
                        "description": (
                            "Filter by specific field values (optional). "
                            "Example: {'status': 'Open', 'type': 'Pothole'}"
                        ),
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "Sort by field name. Use 'field_name asc' or 'field_name desc'. "
                            "Example: 'date desc'"
                        ),
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to return (optional). Returns all fields if not specified.",
                    },
                },
                "required": ["resource_id"],
            },
        ),
        Tool(
            name="get_datastore_schema",
            description=(
                "Get the schema/structure of a DataStore resource. "
                "Shows field names, data types, and descriptions. "
                "Useful before querying to understand available fields."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_id": {
                        "type": "string",
                        "description": "Resource ID to get schema for",
                    }
                },
                "required": ["resource_id"],
            },
        ),
    ]


# ============================================================================
# MCP Tool Handlers
# ============================================================================


@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool execution requests from clients with enhanced error handling and validation."""
    start_time = time.time()
    request_id = f"req_{int(time.time() * 1000)}"

    # Set request ID in logger context
    logger = get_logger("server")

    try:
        # Validate tool request
        try:
            validated_args = validate_tool_request(name, arguments)
        except ValidationError as e:
            log_tool_execution(logger, name, 0, False, "VALIDATION_ERROR")
            return [
                TextContent(
                    type="text",
                    text=format_error_message(
                        "Validation Error",
                        str(e),
                        {
                            "field": getattr(e, "field", None),
                            "value": getattr(e, "value", None),
                        },
                    ),
                )
            ]

        # Execute tool based on name
        if name == "search_datasets":
            return await _handle_search_datasets(
                validated_args, logger, request_id, start_time
            )
        elif name == "list_all_datasets":
            return await _handle_list_all_datasets(
                validated_args, logger, request_id, start_time
            )
        elif name == "get_dataset_info":
            return await _handle_get_dataset_info(
                validated_args, logger, request_id, start_time
            )
        elif name == "query_datastore":
            return await _handle_query_datastore(
                validated_args, logger, request_id, start_time
            )
        elif name == "get_datastore_schema":
            return await _handle_get_datastore_schema(
                validated_args, logger, request_id, start_time
            )
        else:
            raise ValidationError(f"Unknown tool: {name}")

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_code = getattr(e, "error_code", "UNKNOWN_ERROR")
        log_tool_execution(logger, name, duration_ms, False, error_code)

        # Handle specific exception types
        if isinstance(e, ValidationError):
            return [
                TextContent(
                    type="text",
                    text=format_error_message(
                        "Validation Error", str(e), {"field": getattr(e, "field", None)}
                    ),
                )
            ]
        elif isinstance(e, APIError):
            return [
                TextContent(
                    type="text",
                    text=format_error_message(
                        "API Error",
                        str(e),
                        {"status_code": getattr(e, "status_code", None)},
                    ),
                )
            ]
        elif isinstance(e, ResourceNotFoundError):
            return [
                TextContent(
                    type="text",
                    text=format_error_message(
                        "Resource Not Found",
                        str(e),
                        {"resource_type": getattr(e, "resource_type", None)},
                    ),
                )
            ]
        elif isinstance(e, RateLimitError):
            return [
                TextContent(
                    type="text",
                    text=format_error_message(
                        "Rate Limit Exceeded",
                        str(e),
                        {"retry_after": getattr(e, "retry_after", None)},
                    ),
                )
            ]
        elif isinstance(e, TimeoutError):
            return [
                TextContent(
                    type="text",
                    text=format_error_message(
                        "Timeout Error",
                        str(e),
                        {"timeout_duration": getattr(e, "timeout_duration", None)},
                    ),
                )
            ]
        elif isinstance(e, CircuitBreakerError):
            return [
                TextContent(
                    type="text",
                    text=format_error_message(
                        "Service Unavailable",
                        "The service is temporarily unavailable. Please try again later.",
                        {"circuit_state": getattr(e, "circuit_state", None)},
                    ),
                )
            ]
        else:
            logger.error(f"Unexpected error in tool {name}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=format_error_message(
                        "Internal Error",
                        "An unexpected error occurred. Please try again later.",
                        {"error_type": type(e).__name__},
                    ),
                )
            ]


async def _handle_search_datasets(
    args, logger, request_id: str, start_time: float
) -> List[TextContent]:
    """Handle search_datasets tool execution."""
    try:
        result = await ckan_api_call(
            "package_search",
            {"q": args.query, "rows": args.limit},
            client_id=request_id,
        )
        datasets = result.get("results", [])
        total_count = result.get("count", 0)

        if not datasets:
            duration_ms = (time.time() - start_time) * 1000
            log_tool_execution(logger, "search_datasets", duration_ms, True)
            return [
                TextContent(
                    type="text", text=f"🔍 No datasets found matching '{args.query}'"
                )
            ]

        output = f"🔍 Found {total_count} dataset(s) matching '{args.query}' (showing {len(datasets)}):\n\n"
        for i, dataset in enumerate(datasets, 1):
            output += format_dataset_summary(dataset, i) + "\n"

        output += "\n💡 **Next steps:**\n"
        output += "• Use `get_dataset_info` with a dataset ID to see resources\n"
        output += "• Use `query_datastore` with a resource ID to get actual data"

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger, "search_datasets", duration_ms, True, results_count=len(datasets)
        )
        return [TextContent(type="text", text=output)]

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            "search_datasets",
            duration_ms,
            False,
            getattr(e, "error_code", "API_ERROR"),
        )
        raise


async def _handle_list_all_datasets(
    args, logger, request_id: str, start_time: float
) -> List[TextContent]:
    """Handle list_all_datasets tool execution."""
    try:
        dataset_names = await ckan_api_call(
            "package_list", {"limit": args.limit}, client_id=request_id
        )

        if not dataset_names:
            duration_ms = (time.time() - start_time) * 1000
            log_tool_execution(logger, "list_all_datasets", duration_ms, True)
            return [
                TextContent(
                    type="text", text="No datasets found on Boston's Open Data portal."
                )
            ]

        output = f"📚 Boston Open Data Datasets (showing {len(dataset_names)}):\n\n"
        for i, dn in enumerate(dataset_names, 1):
            output += f"{i}. `{dn}`\n"
        output += "\n💡 Use `get_dataset_info` with a dataset ID to see details."

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            "list_all_datasets",
            duration_ms,
            True,
            results_count=len(dataset_names),
        )
        return [TextContent(type="text", text=output)]

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            "list_all_datasets",
            duration_ms,
            False,
            getattr(e, "error_code", "API_ERROR"),
        )
        raise


async def _handle_get_dataset_info(
    args, logger, request_id: str, start_time: float
) -> List[TextContent]:
    """Handle get_dataset_info tool execution."""
    try:
        dataset = await ckan_api_call(
            "package_show", {"id": args.dataset_id}, client_id=request_id
        )

        title = dataset.get("title", "Untitled Dataset")
        name = dataset.get("name", "N/A")
        notes = dataset.get("notes", "No description available")
        resources = dataset.get("resources", [])

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

        queryable = [r for r in resources if r.get("datastore_active")]
        if queryable:
            output += "\n✅ **Queryable Resources:**\n"
            for r in queryable:
                output += f"• `{r['id']}` - {r.get('name', 'Unnamed')}\n"
            output += "\n💡 Use `query_datastore` with a resource ID above to get data."
        else:
            output += "\n⚠️  No queryable resources found. These may be downloadable files only."

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger, "get_dataset_info", duration_ms, True, resource_count=len(resources)
        )
        return [TextContent(type="text", text=output)]

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            "get_dataset_info",
            duration_ms,
            False,
            getattr(e, "error_code", "API_ERROR"),
        )
        raise


async def _handle_query_datastore(
    args, logger, request_id: str, start_time: float
) -> List[TextContent]:
    """Handle query_datastore tool execution."""
    try:
        # Validate pagination parameters
        limit, offset = validate_pagination_params(args.limit, args.offset, MAX_RECORDS)

        params = {"resource_id": args.resource_id, "limit": limit, "offset": offset}
        if args.search_text:
            params["q"] = args.search_text
        if args.filters:
            params["filters"] = json.dumps(args.filters)
        if args.sort:
            params["sort"] = args.sort
        if args.fields:
            params["fields"] = ",".join(args.fields)

        result = await ckan_api_call("datastore_search", params, client_id=request_id)
        records = result.get("records", [])
        total = result.get("total", 0)
        fields_info = result.get("fields", [])

        if not records:
            duration_ms = (time.time() - start_time) * 1000
            log_tool_execution(logger, "query_datastore", duration_ms, True)
            return [
                TextContent(type="text", text="No records found matching your query.")
            ]

        # Use the new formatter for response summary
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
            displayed_fields = field_names[:8] if not args.fields else args.fields[:8]
            for field in displayed_fields:
                value = record.get(field, "N/A")
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                elif value is None:
                    value = "N/A"
                output += f"  • **{field}:** {value}\n"
            if len(field_names) > 8 and not args.fields:
                output += f"  • ... (+{len(field_names) - 8} more fields)\n"
            output += "\n"

        if len(records) > 20:
            output += f"... and {len(records) - 20} more records\n\n"

        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger, "query_datastore", duration_ms, True, results_count=len(records)
        )
        return [TextContent(type="text", text=output)]

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            "query_datastore",
            duration_ms,
            False,
            getattr(e, "error_code", "API_ERROR"),
        )
        raise


async def _handle_get_datastore_schema(
    args, logger, request_id: str, start_time: float
) -> List[TextContent]:
    """Handle get_datastore_schema tool execution."""
    try:
        result = await ckan_api_call(
            "datastore_search",
            {"resource_id": args.resource_id, "limit": 0},
            client_id=request_id,
        )
        fields = result.get("fields", [])

        if not fields:
            duration_ms = (time.time() - start_time) * 1000
            log_tool_execution(logger, "get_datastore_schema", duration_ms, True)
            return [
                TextContent(
                    type="text",
                    text="No schema information available for this resource.",
                )
            ]

        output = f"📋 **DataStore Schema**\n\n"
        output += f"🆔 Resource ID: `{args.resource_id}`\n"
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
            logger, "get_datastore_schema", duration_ms, True, field_count=len(fields)
        )
        return [TextContent(type="text", text=output)]

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_tool_execution(
            logger,
            "get_datastore_schema",
            duration_ms,
            False,
            getattr(e, "error_code", "API_ERROR"),
        )
        raise


# ============================================================================
# Health Check and Monitoring
# ============================================================================


async def perform_health_check() -> Dict[str, Any]:
    """Perform a comprehensive health check."""
    global _health_status

    try:
        # Check CKAN API health
        ckan_health = await health_check()

        # Check rate limiter status
        rate_limiter_status = await rate_limiter.get_status()

        # Update health status
        _health_status = {
            "status": "healthy" if ckan_health["status"] == "healthy" else "unhealthy",
            "last_check": time.time(),
            "details": {
                "ckan_api": ckan_health,
                "rate_limiter": rate_limiter_status,
                "environment": settings.environment,
                "version": "1.0.0",
            },
        }

        return _health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        _health_status = {
            "status": "unhealthy",
            "last_check": time.time(),
            "details": {"error": str(e)},
        }
        return _health_status


async def get_server_status() -> Dict[str, Any]:
    """Get current server status."""
    return {
        "status": _health_status["status"],
        "uptime": time.time() - (_health_status.get("start_time", time.time())),
        "last_health_check": _health_status.get("last_check"),
        "environment": settings.environment,
        "version": "1.0.0",
    }
