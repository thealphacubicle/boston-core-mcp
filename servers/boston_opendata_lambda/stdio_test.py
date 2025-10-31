#!/usr/bin/env python3
"""Temporary stdio server using MCPEngine tools for testing with Claude."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions

# Import the MCPEngine tools
from servers.boston_opendata_lambda.lambda_server import (
    search_datasets,
    list_all_datasets,
    get_dataset_info,
    query_datastore,
    get_datastore_schema,
)

app = Server("boston-opendata-lambda-test")


@app.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="search_datasets",
            description="Search for datasets on Boston's Open Data portal. Use keywords like '311', 'crime', 'permits', 'parking', etc. Returns matching datasets with descriptions and IDs.",
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
            description="List all available datasets on Boston's Open Data portal. Returns dataset names/IDs. Use this to browse what's available.",
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
            description="Get detailed information about a specific dataset, including all its resources. Use the dataset ID (name) from search results. This shows you resource IDs needed to query the actual data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "Dataset ID or name (e.g., '311-service-requests', 'crime-incident-reports'). Get this from search_datasets results.",
                    },
                },
                "required": ["dataset_id"],
            },
        ),
        Tool(
            name="query_datastore",
            description="Query actual data from a DataStore resource. You must have the resource_id from get_dataset_info. Supports filtering, searching, sorting, and limiting results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_id": {
                        "type": "string",
                        "description": "Resource ID (UUID format) from get_dataset_info. Only resources with DataStore active can be queried.",
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
                        "description": "Filter by specific field values (optional). Example: {'status': 'Open', 'type': 'Pothole'}",
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort by field name. Use 'field_name asc' or 'field_name desc'. Example: 'date desc'",
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
            description="Get the schema/structure of a DataStore resource. Shows field names, data types, and descriptions. Useful before querying to understand available fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_id": {
                        "type": "string",
                        "description": "Resource ID to get schema for",
                    },
                },
                "required": ["resource_id"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    try:
        if name == "search_datasets":
            result = await search_datasets(
                arguments.get("query", ""), arguments.get("limit", 10)
            )
        elif name == "list_all_datasets":
            result = await list_all_datasets(arguments.get("limit", 20))
        elif name == "get_dataset_info":
            result = await get_dataset_info(arguments.get("dataset_id", ""))
        elif name == "query_datastore":
            result = await query_datastore(
                arguments.get("resource_id", ""),
                arguments.get("limit", 10),
                arguments.get("offset", 0),
                arguments.get("search_text"),
                arguments.get("filters"),
                arguments.get("sort"),
                arguments.get("fields"),
            )
        elif name == "get_datastore_schema":
            result = await get_datastore_schema(arguments.get("resource_id", ""))
        else:
            result = f"Unknown tool: {name}"

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="boston-opendata-lambda-test",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
