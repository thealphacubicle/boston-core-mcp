#!/usr/bin/env python3
"""Safe formatters for the Boston OpenData MCP server."""

import html
from typing import Any, Dict, Optional

from .validators import sanitize_string


def format_dataset_summary(dataset: Dict[str, Any], index: Optional[int] = None) -> str:
    """Format dataset summary with safe string handling.

    Args:
        dataset: Dataset dictionary from CKAN API
        index: Optional index number for the dataset

    Returns:
        Formatted string representation of the dataset
    """
    if not isinstance(dataset, dict):
        return f"{index}. Invalid dataset data"

    prefix = f"{index}. " if index else ""

    # Safely extract and sanitize fields
    title = sanitize_string(str(dataset.get("title", "Untitled Dataset")), 100)
    name = sanitize_string(str(dataset.get("name", "N/A")), 50)
    notes = dataset.get("notes", "No description available")

    # Handle notes safely
    if isinstance(notes, str):
        notes = sanitize_string(notes, 200)
        if len(notes) > 200:
            notes = notes[:200] + "..."
        notes = " ".join(notes.split())
    else:
        notes = "No description available"

    # Count resources safely
    resources = dataset.get("resources", [])
    if isinstance(resources, list):
        num_resources = len(resources)
    else:
        num_resources = 0

    # Build output safely
    output = f"{prefix}**{title}**\n"
    output += f"   📝 {notes}\n"
    output += f"   🆔 ID: `{name}`\n"
    output += f"   📊 Resources: {num_resources}\n"
    output += f"   🔗 https://data.boston.gov/dataset/{name}\n"

    return output


def format_resource_info(resource: Dict[str, Any], index: Optional[int] = None) -> str:
    """Format resource info with safe string handling.

    Args:
        resource: Resource dictionary from CKAN API
        index: Optional index number for the resource

    Returns:
        Formatted string representation of the resource
    """
    if not isinstance(resource, dict):
        return f"{index}. Invalid resource data"

    prefix = f"{index}. " if index else ""

    # Safely extract and sanitize fields
    name = sanitize_string(str(resource.get("name", "Unnamed Resource")), 100)
    res_id = sanitize_string(str(resource.get("id", "N/A")), 50)
    fmt = sanitize_string(str(resource.get("format", "Unknown")), 20)
    desc = resource.get("description", "")
    has_datastore = bool(resource.get("datastore_active", False))

    # Handle description safely
    if isinstance(desc, str):
        desc = sanitize_string(desc, 100)
        desc_short = desc[:100] + "..." if len(desc) > 100 else desc
    else:
        desc_short = ""

    # Build output safely
    output = f"{prefix}{name}\n"
    output += f"   🆔 Resource ID: `{res_id}`\n"
    output += f"   📄 Format: {fmt}\n"
    output += f"   🗄️  DataStore: {'✅ Yes (Queryable)' if has_datastore else '❌ No'}\n"

    if desc_short:
        output += f"   📝 {desc_short}\n"

    return output


def format_error_message(
    error_type: str, message: str, details: Optional[Dict[str, Any]] = None
) -> str:
    """Format error message with safe string handling.

    Args:
        error_type: Type of error
        message: Error message
        details: Optional error details

    Returns:
        Formatted error message
    """
    safe_type = sanitize_string(error_type, 50)
    safe_message = sanitize_string(message, 500)

    output = f"❌ **{safe_type}**\n\n{safe_message}\n"

    if details:
        output += "\n**Details:**\n"
        for key, value in details.items():
            safe_key = sanitize_string(str(key), 30)
            safe_value = sanitize_string(str(value), 200)
            output += f"• **{safe_key}:** {safe_value}\n"

    return output


def format_health_status(status: str, details: Optional[Dict[str, Any]] = None) -> str:
    """Format health check status.

    Args:
        status: Health status (healthy/unhealthy)
        details: Optional status details

    Returns:
        Formatted health status message
    """
    if status.lower() == "healthy":
        emoji = "✅"
        status_text = "Healthy"
    else:
        emoji = "❌"
        status_text = "Unhealthy"

    output = f"{emoji} **Server Status: {status_text}**\n\n"

    if details:
        for key, value in details.items():
            safe_key = sanitize_string(str(key), 30)
            safe_value = sanitize_string(str(value), 200)
            output += f"• **{safe_key}:** {safe_value}\n"

    return output


def format_api_response_summary(
    total_count: int, returned_count: int, offset: int = 0, has_more: bool = False
) -> str:
    """Format API response summary.

    Args:
        total_count: Total number of items available
        returned_count: Number of items returned
        offset: Number of items skipped
        has_more: Whether there are more items available

    Returns:
        Formatted summary string
    """
    output = f"📊 **Query Results**\n\n"
    output += f"📈 Total records available: {total_count}\n"
    output += f"📄 Showing: {returned_count} records"

    if offset > 0:
        output += f" (offset: {offset})"

    output += "\n\n"

    if has_more:
        next_offset = offset + returned_count
        output += f"📄 **Pagination:** Use offset={next_offset} to see next page.\n"

    return output
