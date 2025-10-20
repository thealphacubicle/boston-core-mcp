"""Configuration values for the MBTA MCP server."""

from __future__ import annotations

from typing import Final

API_BASE_URL: Final[str] = "https://api-v3.mbta.com"
API_TIMEOUT: Final[float] = 15.0

MBTA_API_KEY_ENV: Final[str] = "MBTA_API_KEY"

DEFAULT_PREDICTION_LIMIT: Final[int] = 10
DEFAULT_ALERT_LIMIT: Final[int] = 10
DEFAULT_STOP_LIMIT: Final[int] = 10
DEFAULT_ROUTE_LIMIT: Final[int] = 25
DEFAULT_SCHEDULE_LIMIT: Final[int] = 10

MAX_LIMIT: Final[int] = 100

USER_AGENT: Final[str] = "boston-core-mcp-mbta/1.0"

ROUTE_TYPE_DESCRIPTIONS: Final[dict[int, str]] = {
    0: "Light rail / subway",
    1: "Heavy rail",
    2: "Commuter rail",
    3: "Bus",
    4: "Ferry",
}
