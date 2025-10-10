#!/usr/bin/env python3
import json
import sys
from typing import Any, Dict, List

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

from .ckan import ckan_api_call
from .formatters import format_dataset_summary, format_resource_info
from .config import MAX_RECORDS


# ============================================================================
# Server Setup
# ============================================================================

app = Server("boston-opendata-server")


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
    """Handle tool execution requests from clients"""

    try:
        if name == "search_datasets":
            query = arguments["query"]
            limit = arguments.get("limit", 10)

            result = await ckan_api_call("package_search", {"q": query, "rows": limit})
            datasets = result.get("results", [])
            total_count = result.get("count", 0)

            if not datasets:
                return [TextContent(type="text", text=f"🔍 No datasets found matching '{query}'")]

            output = f"🔍 Found {total_count} dataset(s) matching '{query}' (showing {len(datasets)}):\n\n"
            for i, dataset in enumerate(datasets, 1):
                output += format_dataset_summary(dataset, i) + "\n"

            output += "\n💡 **Next steps:**\n"
            output += "• Use `get_dataset_info` with a dataset ID to see resources\n"
            output += "• Use `query_datastore` with a resource ID to get actual data"

            return [TextContent(type="text", text=output)]

        elif name == "list_all_datasets":
            limit = arguments.get("limit", 20)
            dataset_names = await ckan_api_call("package_list", {"limit": limit})

            if not dataset_names:
                return [TextContent(type="text", text="No datasets found on Boston's Open Data portal.")]

            output = f"📚 Boston Open Data Datasets (showing {len(dataset_names)}):\n\n"
            for i, dn in enumerate(dataset_names, 1):
                output += f"{i}. `{dn}`\n"
            output += "\n💡 Use `get_dataset_info` with a dataset ID to see details."
            return [TextContent(type="text", text=output)]

        elif name == "get_dataset_info":
            dataset_id = arguments["dataset_id"]
            dataset = await ckan_api_call("package_show", {"id": dataset_id})

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

            return [TextContent(type="text", text=output)]

        elif name == "query_datastore":
            resource_id = arguments["resource_id"]
            limit = min(arguments.get("limit", 10), MAX_RECORDS)
            offset = arguments.get("offset", 0)
            search_text = arguments.get("search_text")
            filters = arguments.get("filters", {})
            sort = arguments.get("sort")
            fields = arguments.get("fields")

            params = {"resource_id": resource_id, "limit": limit, "offset": offset}
            if search_text:
                params["q"] = search_text
            if filters:
                params["filters"] = json.dumps(filters)
            if sort:
                params["sort"] = sort
            if fields:
                params["fields"] = ",".join(fields)

            result = await ckan_api_call("datastore_search", params)
            records = result.get("records", [])
            total = result.get("total", 0)
            fields_info = result.get("fields", [])

            if not records:
                return [TextContent(type="text", text="No records found matching your query.")]

            output = f"📊 **Query Results**\n\n"
            output += f"📈 Total records available: {total}\n"
            output += f"📄 Showing: {len(records)} records (offset: {offset})\n\n"

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
            if total > (offset + limit):
                output += f"\n📄 **Pagination:** Use offset={offset + limit} to see next page."

            return [TextContent(type="text", text=output)]

        elif name == "get_datastore_schema":
            resource_id = arguments["resource_id"]
            result = await ckan_api_call("datastore_search", {"resource_id": resource_id, "limit": 0})
            fields = result.get("fields", [])
            if not fields:
                return [TextContent(type="text", text="No schema information available for this resource.")]

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
            return [TextContent(type="text", text=output)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except httpx.HTTPStatusError as e:
        error_msg = f"❌ **HTTP Error {e.response.status_code}**\n\n"
        error_msg += "Failed to access Boston Open Data API.\n"
        error_msg += f"Endpoint: {e.request.url}\n"
        try:
            error_detail = e.response.json()
            error_msg += f"\nDetails: {json.dumps(error_detail, indent=2)}"
        except Exception:
            error_msg += f"\nResponse: {e.response.text[:500]}"
        return [TextContent(type="text", text=error_msg)]

    except ValueError as e:
        return [TextContent(type="text", text=f"❌ **API Error**\n\n{str(e)}")]

    except Exception as e:
        error_msg = f"❌ **Unexpected Error**\n\n"
        error_msg += f"Type: {type(e).__name__}\n"
        error_msg += f"Message: {str(e)}\n"
        print(f"[ERROR] {type(e).__name__}: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return [TextContent(type="text", text=error_msg)]
