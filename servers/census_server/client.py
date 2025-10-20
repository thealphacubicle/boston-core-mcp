"""Async HTTP client helpers for interacting with the Census Bureau APIs."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

import httpx

from .config import (
    API_BASE_URL,
    API_TIMEOUT,
    CENSUS_API_KEY_ENV,
    DATASET_PATHS,
    GEOGRAPHY_ALIASES,
    MAX_RESULTS,
    MAX_VARIABLES,
    USER_AGENT,
    VALID_GEOGRAPHIES,
)


class CensusConfigurationError(RuntimeError):
    """Raised when the server is misconfigured (e.g., missing API key)."""


class CensusQueryError(RuntimeError):
    """Raised when a query cannot be constructed or executed."""


@dataclass(slots=True)
class CensusResponse:
    """Structured response for a Census API query."""

    headers: List[str]
    rows: List[List[str]]

    def to_records(self) -> List[Dict[str, Any]]:
        """Return the response rows as a list of dictionaries."""

        records: List[Dict[str, Any]] = []
        for row in self.rows:
            record = {header: value for header, value in zip(self.headers, row)}
            records.append(record)
        return records


async def _http_get(path: str, params: MutableMapping[str, Any]) -> Any:
    """Perform an HTTP GET request against the Census API."""

    api_key = os.getenv(CENSUS_API_KEY_ENV)
    if api_key:
        params.setdefault("key", api_key)
    else:
        print(
            "[WARN] Missing CENSUS_API_KEY environment variable; proceeding without it",
            file=sys.stderr,
        )

    url = f"{API_BASE_URL}/{path.strip('/')}"
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=API_TIMEOUT, headers=headers) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def resolve_dataset(dataset: str, year: int) -> str:
    """Resolve a dataset key + year into an API path."""

    if dataset not in DATASET_PATHS:
        raise CensusConfigurationError(f"Unsupported dataset '{dataset}'.")
    return DATASET_PATHS[dataset].format(year=year)


def normalize_geography_level(level: str) -> str:
    """Normalize geography level aliases to canonical values."""

    normalized = level.lower().strip()
    normalized = GEOGRAPHY_ALIASES.get(normalized, normalized)
    if normalized not in VALID_GEOGRAPHIES:
        raise CensusQueryError(
            f"Unsupported geography level '{level}'. Supported levels: "
            + ", ".join(sorted(VALID_GEOGRAPHIES.keys()))
        )
    return normalized


def build_geo_params(geography: Mapping[str, Any]) -> Dict[str, str]:
    """Construct `for` and `in` parameters for Census geography queries."""

    if "level" not in geography:
        raise CensusQueryError("Geography must include a 'level' field.")

    level = normalize_geography_level(str(geography["level"]))
    required_fields = VALID_GEOGRAPHIES[level]

    missing = [field for field in required_fields if field not in geography]
    if missing:
        raise CensusQueryError(
            f"Missing required geography fields for level '{level}': {', '.join(missing)}"
        )

    in_value_parts: List[str] = []

    if level == "us":
        return {"for": "us:1"}

    if level == "state":
        return {"for": f"state:{geography['state']}"}

    if level == "county":
        return {
            "for": f"county:{geography['county']}",
            "in": f"state:{geography['state']}",
        }

    if level == "place":
        return {
            "for": f"place:{geography['place']}",
            "in": f"state:{geography['state']}",
        }

    if level == "tract":
        in_value_parts.append(f"state:{geography['state']}")
        in_value_parts.append(f"county:{geography['county']}")
        return {
            "for": f"tract:{geography['tract']}",
            "in": " ".join(in_value_parts),
        }

    if level == "block_group":
        in_value_parts.append(f"state:{geography['state']}")
        in_value_parts.append(f"county:{geography['county']}")
        in_value_parts.append(f"tract:{geography['tract']}")
        return {
            "for": f"block group:{geography['block_group']}",
            "in": " ".join(in_value_parts),
        }

    raise CensusQueryError(f"Unsupported geography level '{level}'.")


async def fetch_tabular_data(
    dataset_key: str,
    year: int,
    variables: Iterable[str],
    geography: Mapping[str, Any],
    predicates: Optional[Mapping[str, Any]] = None,
) -> CensusResponse:
    """Fetch tabular data (e.g., ACS, Decennial) and return structured records."""

    vars_list = [var.strip() for var in variables if var.strip()]
    if not vars_list:
        raise CensusQueryError("At least one variable must be provided.")
    if len(vars_list) > MAX_VARIABLES:
        raise CensusQueryError(
            f"Too many variables requested ({len(vars_list)}). Maximum is {MAX_VARIABLES}."
        )

    dataset_path = resolve_dataset(dataset_key, year)
    params: Dict[str, Any] = {"get": ",".join(["NAME", *vars_list])}
    params.update(build_geo_params(geography))

    if predicates:
        for key, value in predicates.items():
            params[f"{key}"] = value

    data = await _http_get(dataset_path, params)

    if not isinstance(data, list) or not data:
        raise CensusQueryError("Unexpected response format from Census API.")

    headers = data[0]
    rows = data[1:MAX_RESULTS + 1]
    return CensusResponse(headers=headers, rows=rows)


async def fetch_variables(dataset_key: str, year: int) -> Dict[str, Any]:
    dataset_path = resolve_dataset(dataset_key, year)
    raw = await _http_get(f"{dataset_path}/variables.json", {})
    if not isinstance(raw, dict) or "variables" not in raw:
        raise CensusQueryError("Unexpected variable metadata response.")
    return raw["variables"]


async def fetch_geographies(dataset_key: str, year: int) -> Dict[str, Any]:
    dataset_path = resolve_dataset(dataset_key, year)
    raw = await _http_get(f"{dataset_path}/geography.json", {})
    if not isinstance(raw, dict) or "fips" not in raw:
        raise CensusQueryError("Unexpected geography metadata response.")
    return raw["fips"]


def summarize_records(records: List[Dict[str, Any]], limit: int = 20) -> str:
    """Render a human-readable table summary of Census records."""

    if not records:
        return "No data returned for the given parameters."

    headers = list(records[0].keys())
    preview_rows = records[:limit]

    column_widths = {header: max(len(header), 4) for header in headers}
    for record in preview_rows:
        for header in headers:
            column_widths[header] = min(
                max(column_widths[header], len(str(record.get(header, "")))),
                60,
            )

    separator = " | ".join("-" * column_widths[h] for h in headers)
    header_row = " | ".join(f"{h:<{column_widths[h]}}" for h in headers)

    body_rows = []
    for record in preview_rows:
        body_rows.append(
            " | ".join(f"{str(record.get(h, '')):<{column_widths[h]}}" for h in headers)
        )

    table = [header_row, separator, *body_rows]
    if len(records) > limit:
        table.append(f"... (+{len(records) - limit} more rows)")
    return "\n".join(table)


def summarize_variables(
    variables: Mapping[str, Any],
    keyword: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """Filter and format variable metadata."""

    max_results = MAX_RESULTS if limit is None else min(limit, MAX_RESULTS)
    results: List[str] = []
    for var_name, metadata in variables.items():
        label = metadata.get("label", "")
        concept = metadata.get("concept", "")
        predicate_type = metadata.get("predicateType", "")
        group = metadata.get("group", "")

        if keyword:
            needle = keyword.lower()
            haystack = " ".join([var_name, label, concept]).lower()
            if needle not in haystack:
                continue

        description = metadata.get("description")
        parts = [f"**{var_name}**"]
        if label:
            parts.append(label)
        if concept:
            parts.append(f"Concept: {concept}")
        if predicate_type:
            parts.append(f"Type: {predicate_type}")
        if group:
            parts.append(f"Group: {group}")
        if description:
            parts.append(f"Description: {description}")
        results.append("\n".join(parts))

        if len(results) >= max_results:
            break

    if not results:
        return "No variables matched your search keywords."

    if keyword:
        header = f"🔎 Variables matching '{keyword}':\n\n"
    else:
        header = "🔎 Available variables:\n\n"
    body = "\n\n".join(results)
    return header + body


def summarize_geographies(geographies: Mapping[str, Any]) -> str:
    """Format geography metadata into a human-readable list."""

    lines = ["🗺️ Available geographies:"]
    for geo_id, metadata in sorted(geographies.items()):
        name = metadata.get("name", geo_id)
        requires = metadata.get("requires", [])
        sumlevel = metadata.get("sumlevel")
        lines.append(f"• **{name}** (`{geo_id}`)")
        if sumlevel:
            lines.append(f"  Summary level: {sumlevel}")
        if requires:
            lines.append(f"  Requires: {', '.join(requires)}")
    return "\n".join(lines)


def render_records_json(records: List[Dict[str, Any]]) -> str:
    """Return records as pretty-printed JSON string."""

    return json.dumps(records, indent=2)
