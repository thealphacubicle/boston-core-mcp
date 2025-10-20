#!/usr/bin/env python3
"""MCP server for interacting with the MBTA v3 API."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Mapping

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

from .client import (
    MBTAApiResponse,
    render_json,
    summarize_alert,
    summarize_prediction,
    summarize_route,
    summarize_schedule,
    summarize_stop,
    clamp_limit,
)
from .config import (
    DEFAULT_ALERT_LIMIT,
    DEFAULT_PREDICTION_LIMIT,
    DEFAULT_ROUTE_LIMIT,
    DEFAULT_SCHEDULE_LIMIT,
    DEFAULT_STOP_LIMIT,
)

app = Server("mbta-api-server")


@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_predictions",
            description=(
                "Retrieve real-time arrival and departure predictions for a stop. "
                "Supports filtering by route, direction, and time windows."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stop_id": {
                        "type": "string",
                        "description": "Stop ID to fetch predictions for (e.g., 'place-sstat').",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Optional route filter (e.g., 'Red', '1').",
                    },
                    "direction_id": {
                        "type": "integer",
                        "description": "Direction ID filter (0 or 1).",
                    },
                    "min_time": {
                        "type": "string",
                        "description": "ISO8601 min arrival time filter.",
                    },
                    "max_time": {
                        "type": "string",
                        "description": "ISO8601 max arrival time filter.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of predictions to return.",
                        "default": DEFAULT_PREDICTION_LIMIT,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "include_json": {
                        "type": "boolean",
                        "description": "Include the raw JSON payload in the response.",
                        "default": False,
                    },
                },
                "required": ["stop_id"],
            },
        ),
        Tool(
            name="get_alerts",
            description=(
                "List current MBTA service alerts with optional filtering by route, stop, or severity."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "route_id": {
                        "type": "string",
                        "description": "Filter alerts affecting a specific route.",
                    },
                    "stop_id": {
                        "type": "string",
                        "description": "Filter alerts affecting a specific stop.",
                    },
                    "severity": {
                        "type": "integer",
                        "description": "Minimum severity (0-10).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of alerts to return.",
                        "default": DEFAULT_ALERT_LIMIT,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "include_json": {
                        "type": "boolean",
                        "description": "Include raw JSON payload for downstream parsing.",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="get_stops",
            description=(
                "Search for MBTA stops by name or geographic proximity. Returns basic metadata including coordinates."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Match stop names containing this text.",
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Latitude for proximity search.",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude for proximity search.",
                    },
                    "radius": {
                        "type": "number",
                        "description": "Radius in meters for geographic search.",
                    },
                    "route_type": {
                        "type": "integer",
                        "description": "Filter stops that serve a route type (0-4).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum stops to return.",
                        "default": DEFAULT_STOP_LIMIT,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "include_json": {
                        "type": "boolean",
                        "description": "Include raw JSON payload in the response.",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="get_routes",
            description=(
                "Retrieve MBTA route metadata with optional filters for mode or specific IDs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "route_id": {
                        "type": "string",
                        "description": "Return information for a specific route ID.",
                    },
                    "route_type": {
                        "type": "integer",
                        "description": "Filter by route type (0 light rail, 1 heavy rail, 2 commuter rail, 3 bus, 4 ferry).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum routes to return.",
                        "default": DEFAULT_ROUTE_LIMIT,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "include_json": {
                        "type": "boolean",
                        "description": "Include raw JSON payload in the response.",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="get_schedules",
            description=(
                "Retrieve scheduled arrivals/departures for a route and/or stop. Useful for planned service times."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "route_id": {
                        "type": "string",
                        "description": "Route ID to filter schedules (optional).",
                    },
                    "stop_id": {
                        "type": "string",
                        "description": "Stop ID to filter schedules (optional).",
                    },
                    "direction_id": {
                        "type": "integer",
                        "description": "Direction filter (0 or 1).",
                    },
                    "date": {
                        "type": "string",
                        "description": "Service date in YYYY-MM-DD format (optional).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum schedule entries to return.",
                        "default": DEFAULT_SCHEDULE_LIMIT,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "include_json": {
                        "type": "boolean",
                        "description": "Include raw JSON payload in the response.",
                        "default": False,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Mapping[str, Any]) -> List[TextContent]:
    try:
        if name == "get_predictions":
            return await _handle_predictions(arguments)
        if name == "get_alerts":
            return await _handle_alerts(arguments)
        if name == "get_stops":
            return await _handle_stops(arguments)
        if name == "get_routes":
            return await _handle_routes(arguments)
        if name == "get_schedules":
            return await _handle_schedules(arguments)

        raise ValueError(f"Unknown tool: {name}")

    except httpx.HTTPStatusError as exc:
        error_lines = [
            "❌ **HTTP error from MBTA API**",
            f"Status: {exc.response.status_code}",
            f"URL: {exc.request.url}",
        ]
        try:
            payload = exc.response.json()
            error_lines.append("Response: " + json.dumps(payload, indent=2))
        except Exception:
            error_lines.append(f"Response text: {exc.response.text[:500]}")
        return [TextContent(type="text", text="\n\n".join(error_lines))]

    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return [
            TextContent(
                type="text",
                text=(
                    "❌ **Unexpected error**\n\n"
                    f"Type: {type(exc).__name__}\n"
                    f"Message: {exc}"
                ),
            )
        ]


async def _handle_predictions(arguments: Mapping[str, Any]) -> List[TextContent]:
    params: Dict[str, Any] = {
        "filter[stop]": arguments["stop_id"],
        "page[limit]": clamp_limit(arguments.get("limit"), DEFAULT_PREDICTION_LIMIT),
        "sort": "arrival_time",
    }
    if arguments.get("route_id"):
        params["filter[route]"] = arguments["route_id"]
    if arguments.get("direction_id") is not None:
        params["filter[direction_id]"] = arguments["direction_id"]
    if arguments.get("min_time"):
        params["filter[min_time]"] = arguments["min_time"]
    if arguments.get("max_time"):
        params["filter[max_time]"] = arguments["max_time"]

    response = await _http_request("predictions", params)
    if not response.data:
        return [TextContent(type="text", text="No predictions available for the requested filters.")]

    body_lines = ["🚉 **Predictions**", ""]
    for prediction in response.data:
        body_lines.append(summarize_prediction(prediction))
        body_lines.append("")

    outputs = [TextContent(type="text", text="\n".join(body_lines).strip())]

    if arguments.get("include_json"):
        outputs.append(TextContent(type="text", text="```json\n" + render_json(response.data) + "\n```"))

    return outputs


async def _handle_alerts(arguments: Mapping[str, Any]) -> List[TextContent]:
    params: Dict[str, Any] = {
        "page[limit]": clamp_limit(arguments.get("limit"), DEFAULT_ALERT_LIMIT),
        "sort": "-updated_at",
    }
    if arguments.get("route_id"):
        params["filter[route]"] = arguments["route_id"]
    if arguments.get("stop_id"):
        params["filter[stop]"] = arguments["stop_id"]
    if arguments.get("severity") is not None:
        params["filter[min_severity]"] = arguments["severity"]

    response = await _http_request("alerts", params)
    if not response.data:
        return [TextContent(type="text", text="No active alerts for the requested filters.")]

    body_lines = ["⚠️ **Service alerts**", ""]
    for alert in response.data:
        body_lines.append(summarize_alert(alert))
        body_lines.append("")

    outputs = [TextContent(type="text", text="\n".join(body_lines).strip())]

    if arguments.get("include_json"):
        outputs.append(TextContent(type="text", text="```json\n" + render_json(response.data) + "\n```"))

    return outputs


async def _handle_stops(arguments: Mapping[str, Any]) -> List[TextContent]:
    params: Dict[str, Any] = {
        "page[limit]": clamp_limit(arguments.get("limit"), DEFAULT_STOP_LIMIT),
        "sort": "name",
    }
    if arguments.get("name"):
        params["filter[name]"] = arguments["name"]
    if arguments.get("latitude") is not None and arguments.get("longitude") is not None:
        params["filter[latitude]"] = arguments["latitude"]
        params["filter[longitude]"] = arguments["longitude"]
        if arguments.get("radius") is not None:
            params["filter[radius]"] = arguments["radius"]
    if arguments.get("route_type") is not None:
        params["filter[route_type]"] = arguments["route_type"]

    response = await _http_request("stops", params)
    if not response.data:
        return [TextContent(type="text", text="No stops matched your filters.")]

    body_lines = ["🛑 **Stops**", ""]
    for stop in response.data:
        body_lines.append(summarize_stop(stop))
        body_lines.append("")

    outputs = [TextContent(type="text", text="\n".join(body_lines).strip())]

    if arguments.get("include_json"):
        outputs.append(TextContent(type="text", text="```json\n" + render_json(response.data) + "\n```"))

    return outputs


async def _handle_routes(arguments: Mapping[str, Any]) -> List[TextContent]:
    params: Dict[str, Any] = {
        "page[limit]": clamp_limit(arguments.get("limit"), DEFAULT_ROUTE_LIMIT),
        "sort": "long_name",
    }
    if arguments.get("route_id"):
        params["filter[id]"] = arguments["route_id"]
    if arguments.get("route_type") is not None:
        params["filter[type]"] = arguments["route_type"]

    response = await _http_request("routes", params)
    if not response.data:
        return [TextContent(type="text", text="No routes matched your filters.")]

    body_lines = ["🚌 **Routes**", ""]
    for route in response.data:
        body_lines.append(summarize_route(route))
        body_lines.append("")

    outputs = [TextContent(type="text", text="\n".join(body_lines).strip())]

    if arguments.get("include_json"):
        outputs.append(TextContent(type="text", text="```json\n" + render_json(response.data) + "\n```"))

    return outputs


async def _handle_schedules(arguments: Mapping[str, Any]) -> List[TextContent]:
    params: Dict[str, Any] = {
        "page[limit]": clamp_limit(arguments.get("limit"), DEFAULT_SCHEDULE_LIMIT),
        "sort": "arrival_time",
    }
    if arguments.get("route_id"):
        params["filter[route]"] = arguments["route_id"]
    if arguments.get("stop_id"):
        params["filter[stop]"] = arguments["stop_id"]
    if arguments.get("direction_id") is not None:
        params["filter[direction_id]"] = arguments["direction_id"]
    if arguments.get("date"):
        params["filter[date]"] = arguments["date"]

    response = await _http_request("schedules", params)
    if not response.data:
        return [TextContent(type="text", text="No schedules matched your filters.")]

    body_lines = ["🕒 **Schedules**", ""]
    for schedule in response.data:
        body_lines.append(summarize_schedule(schedule))
        body_lines.append("")

    outputs = [TextContent(type="text", text="\n".join(body_lines).strip())]

    if arguments.get("include_json"):
        outputs.append(TextContent(type="text", text="```json\n" + render_json(response.data) + "\n```"))

    return outputs


async def _http_request(endpoint: str, params: Mapping[str, Any]) -> MBTAApiResponse:
    from .client import _http_get  # Local import to keep namespace tidy

    return await _http_get(endpoint, dict(params))
