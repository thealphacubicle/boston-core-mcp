"""Configuration constants for the Census MCP server."""

from __future__ import annotations

from typing import Final

API_BASE_URL: Final[str] = "https://api.census.gov/data"
API_TIMEOUT: Final[float] = 15.0

CENSUS_API_KEY_ENV: Final[str] = "CENSUS_API_KEY"

LATEST_ACS_YEAR: Final[int] = 2022
LATEST_DECENNIAL_YEAR: Final[int] = 2020

DATASET_PATHS: Final[dict[str, str]] = {
    "acs5": "{year}/acs/acs5",
    "decennial_pl": "{year}/dec/pl",
}

VALID_GEOGRAPHIES: Final[dict[str, set[str]]] = {
    "state": {"state"},
    "county": {"state", "county"},
    "place": {"state", "place"},
    "tract": {"state", "county", "tract"},
    "block_group": {"state", "county", "tract", "block_group"},
    "us": set(),
}

GEOGRAPHY_ALIASES: Final[dict[str, str]] = {
    "block group": "block_group",
    "blockgroup": "block_group",
}

MAX_VARIABLES: Final[int] = 50
MAX_RESULTS: Final[int] = 100

USER_AGENT: Final[str] = "boston-core-mcp-census/1.0"
