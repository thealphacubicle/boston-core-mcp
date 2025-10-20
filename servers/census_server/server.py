#!/usr/bin/env python3
"""MCP server exposing select U.S. Census Bureau APIs."""

from __future__ import annotations

import json
import sys
from typing import Any, List, Mapping, Sequence

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

from .client import (
    CensusConfigurationError,
    CensusQueryError,
    fetch_geographies,
    fetch_tabular_data,
    fetch_variables,
    render_records_json,
    summarize_geographies,
    summarize_records,
    summarize_variables,
)
from .config import LATEST_ACS_YEAR, LATEST_DECENNIAL_YEAR, MAX_RESULTS

app = Server("census-bureau-server")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Describe available MCP tools."""

    return [
        Tool(
            name="get_acs_data",
            description=(
                "Query American Community Survey (ACS) 5-year estimates for a given "
                "set of variables and geography. Returns both a table preview and "
                "machine-readable JSON payload."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "variables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ACS variable IDs (e.g., 'B01003_001E').",
                    },
                    "geography": {
                        "type": "object",
                        "description": (
                            "Geography definition with a 'level' field and the required FIPS codes. "
                            "Levels supported: us, state, county, place, tract, block_group."
                        ),
                    },
                    "year": {
                        "type": "integer",
                        "description": "ACS vintage (default: latest supported year).",
                        "default": LATEST_ACS_YEAR,
                        "minimum": 2010,
                    },
                    "predicates": {
                        "type": "object",
                        "description": (
                            "Optional additional predicates supported by the dataset (e.g., racial categories)."
                        ),
                    },
                    "return_json": {
                        "type": "boolean",
                        "description": "Return the raw JSON records in addition to the table preview.",
                        "default": False,
                    },
                },
                "required": ["variables", "geography"],
            },
        ),
        Tool(
            name="get_decennial_data",
            description=(
                "Query Decennial Census tables (default: 2020 PL) for selected variables "
                "and geography."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "variables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of decennial variable IDs (e.g., 'P1_001N').",
                    },
                    "geography": {
                        "type": "object",
                        "description": (
                            "Geography definition with a 'level' field and required FIPS codes."
                        ),
                    },
                    "year": {
                        "type": "integer",
                        "description": "Decennial dataset year (default 2020).",
                        "default": LATEST_DECENNIAL_YEAR,
                        "minimum": 2000,
                    },
                    "predicates": {
                        "type": "object",
                        "description": "Optional additional predicate filters supported by the dataset.",
                    },
                    "return_json": {
                        "type": "boolean",
                        "description": "Return the raw JSON records in addition to the table preview.",
                        "default": False,
                    },
                },
                "required": ["variables", "geography"],
            },
        ),
        Tool(
            name="search_variables",
            description=(
                "Search available variables for ACS or Decennial datasets by keyword "
                "and review their descriptions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "string",
                        "description": "Dataset key: 'acs5' or 'decennial_pl'.",
                        "default": "acs5",
                        "enum": ["acs5", "decennial_pl"],
                    },
                    "year": {
                        "type": "integer",
                        "description": "Dataset vintage (defaults based on dataset).",
                        "minimum": 2000,
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to filter variable labels/concepts.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum variables to include in the summary (<= MAX_RESULTS).",
                        "minimum": 1,
                        "maximum": MAX_RESULTS,
                    },
                },
            },
        ),
        Tool(
            name="get_geographies",
            description=(
                "List the geography summary levels available for a dataset, including "
                "which FIPS codes are required."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "string",
                        "description": "Dataset key: 'acs5' or 'decennial_pl'.",
                        "default": "acs5",
                        "enum": ["acs5", "decennial_pl"],
                    },
                    "year": {
                        "type": "integer",
                        "description": "Dataset vintage (defaults based on dataset).",
                        "minimum": 2000,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Mapping[str, Any]) -> List[TextContent]:
    """Dispatch Census Bureau tool calls."""

    try:
        if name == "get_acs_data":
            return await _handle_tabular_query("acs5", arguments)
        if name == "get_decennial_data":
            return await _handle_tabular_query("decennial_pl", arguments)
        if name == "search_variables":
            return await _handle_search_variables(arguments)
        if name == "get_geographies":
            return await _handle_geographies(arguments)

        raise ValueError(f"Unknown tool: {name}")

    except httpx.HTTPStatusError as exc:
        error_msg = [
            "❌ **HTTP Error while contacting the Census API**",
            f"Status: {exc.response.status_code}",
            f"URL: {exc.request.url}",
        ]
        try:
            payload = exc.response.json()
            error_msg.append("Response: " + json.dumps(payload, indent=2))
        except Exception:
            error_msg.append(f"Response text: {exc.response.text[:500]}")
        return [TextContent(type="text", text="\n\n".join(error_msg))]

    except (CensusConfigurationError, CensusQueryError, ValueError) as exc:
        return [
            TextContent(
                type="text",
                text=f"❌ **Census query error**\n\n{exc}",
            )
        ]

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


async def _handle_tabular_query(dataset_key: str, arguments: Mapping[str, Any]) -> List[TextContent]:
    variables: Sequence[str] = arguments.get("variables", [])
    geography: Mapping[str, Any] = arguments.get("geography", {})
    year: int = int(arguments.get("year") or (
        LATEST_ACS_YEAR if dataset_key == "acs5" else LATEST_DECENNIAL_YEAR
    ))
    predicates: Mapping[str, Any] = arguments.get("predicates", {})
    return_json: bool = bool(arguments.get("return_json", False))

    response = await fetch_tabular_data(dataset_key, year, variables, geography, predicates)
    records = response.to_records()

    human_summary = [
        f"📊 **Census data preview**",
        f"Dataset: {dataset_key} ({year})",
        f"Rows returned: {len(records)} (showing up to {min(len(records), 20)})",
        "",
        summarize_records(records),
    ]

    outputs = [TextContent(type="text", text="\n".join(human_summary))]

    if return_json:
        outputs.append(
            TextContent(type="text", text="```json\n" + render_records_json(records) + "\n```")
        )

    return outputs


async def _handle_search_variables(arguments: Mapping[str, Any]) -> List[TextContent]:
    dataset_key: str = arguments.get("dataset", "acs5")
    year: int = int(
        arguments.get("year")
        or (LATEST_ACS_YEAR if dataset_key == "acs5" else LATEST_DECENNIAL_YEAR)
    )
    keyword: str | None = arguments.get("keyword")
    limit = arguments.get("limit")

    variables = await fetch_variables(dataset_key, year)
    summary = summarize_variables(variables, keyword=keyword, limit=limit)

    return [TextContent(type="text", text=summary)]


async def _handle_geographies(arguments: Mapping[str, Any]) -> List[TextContent]:
    dataset_key: str = arguments.get("dataset", "acs5")
    year: int = int(
        arguments.get("year")
        or (LATEST_ACS_YEAR if dataset_key == "acs5" else LATEST_DECENNIAL_YEAR)
    )

    geos = await fetch_geographies(dataset_key, year)
    summary = summarize_geographies(geos)
    return [TextContent(type="text", text=summary)]
