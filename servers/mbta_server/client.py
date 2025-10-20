"""Async HTTP utilities for interacting with the MBTA V3 API."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

import httpx

from .config import (
    API_BASE_URL,
    API_TIMEOUT,
    MBTA_API_KEY_ENV,
    MAX_LIMIT,
    ROUTE_TYPE_DESCRIPTIONS,
    USER_AGENT,
)

ISO_FORMATS = ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S%f%z")


class MBTAConfigurationError(RuntimeError):
    """Raised when required configuration (e.g., API key) is missing."""


@dataclass(slots=True)
class MBTAApiResponse:
    data: List[Dict[str, Any]]
    included: List[Dict[str, Any]]


async def _http_get(path: str, params: MutableMapping[str, Any]) -> MBTAApiResponse:
    """Perform a GET request with standard headers and error handling."""

    api_key = os.getenv(MBTA_API_KEY_ENV)
    headers = {"User-Agent": USER_AGENT}
    if api_key:
        headers["X-API-Key"] = api_key
    else:
        print(
            "[WARN] Missing MBTA_API_KEY environment variable; some endpoints may be rate limited.",
            file=sys.stderr,
        )

    url = f"{API_BASE_URL}/{path.lstrip('/')}"

    async with httpx.AsyncClient(timeout=API_TIMEOUT, headers=headers) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    data = payload.get("data", []) if isinstance(payload, dict) else []
    included = payload.get("included", []) if isinstance(payload, dict) else []
    return MBTAApiResponse(data=data, included=included)


def clamp_limit(value: Optional[int], default: int) -> int:
    if value is None:
        return default
    return max(1, min(int(value), MAX_LIMIT))


def parse_iso_datetime(value: Optional[str]) -> str:
    if not value:
        return "Unknown"
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(value, fmt).astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return value


def summarize_prediction(prediction: Mapping[str, Any]) -> str:
    attrs = prediction.get("attributes", {})
    arrival = parse_iso_datetime(attrs.get("arrival_time"))
    departure = parse_iso_datetime(attrs.get("departure_time"))
    status = attrs.get("status") or "On time"
    direction = attrs.get("direction_id")
    stop_sequence = attrs.get("stop_sequence")
    delay = attrs.get("delay")

    lines = [
        f"• Trip `{prediction.get('relationships', {}).get('trip', {}).get('data', {}).get('id', 'unknown')}`",
        f"  Arrival: {arrival}",
        f"  Departure: {departure}",
        f"  Status: {status}",
    ]
    if delay:
        lines.append(f"  Delay: {delay // 60} min")
    if direction is not None:
        lines.append(f"  Direction ID: {direction}")
    if stop_sequence is not None:
        lines.append(f"  Stop sequence: {stop_sequence}")
    return "\n".join(lines)


def summarize_alert(alert: Mapping[str, Any]) -> str:
    attrs = alert.get("attributes", {})
    header = attrs.get("header") or "Unnamed alert"
    severity = attrs.get("severity")
    effect = attrs.get("effect")
    cause = attrs.get("cause")
    lifecycle = attrs.get("lifecycle")
    timeframe = attrs.get("timeframe")

    active_periods = attrs.get("active_period", [])
    if active_periods:
        active_strings = []
        for period in active_periods:
            start = parse_iso_datetime(period.get("start"))
            end = parse_iso_datetime(period.get("end")) if period.get("end") else "Ongoing"
            active_strings.append(f"{start} – {end}")
        period_text = ", ".join(active_strings)
    else:
        period_text = "Unknown schedule"

    lines = [f"• **{header}**"]
    if severity is not None:
        lines.append(f"  Severity: {severity}")
    if effect:
        lines.append(f"  Effect: {effect}")
    if cause:
        lines.append(f"  Cause: {cause}")
    if lifecycle:
        lines.append(f"  Lifecycle: {lifecycle}")
    if timeframe:
        lines.append(f"  Timeframe: {timeframe}")
    lines.append(f"  Active: {period_text}")
    return "\n".join(lines)


def summarize_stop(stop: Mapping[str, Any]) -> str:
    attrs = stop.get("attributes", {})
    name = attrs.get("name", "Unnamed stop")
    desc = attrs.get("description")
    municipality = attrs.get("municipality")
    lat = attrs.get("latitude")
    lon = attrs.get("longitude")
    zone = attrs.get("zone")

    lines = [f"• **{name}** (`{stop.get('id')}`)"]
    if desc:
        lines.append(f"  {desc}")
    if municipality:
        lines.append(f"  Municipality: {municipality}")
    if lat and lon:
        lines.append(f"  Location: {lat:.5f}, {lon:.5f}")
    if zone:
        lines.append(f"  Zone: {zone}")
    return "\n".join(lines)


def summarize_route(route: Mapping[str, Any]) -> str:
    attrs = route.get("attributes", {})
    long_name = attrs.get("long_name") or attrs.get("description") or "Unnamed route"
    short_name = attrs.get("short_name")
    route_type = attrs.get("type")

    lines = [f"• **{long_name}** (`{route.get('id')}`)"]
    if short_name:
        lines.append(f"  Short name: {short_name}")
    if route_type is not None:
        lines.append(f"  Mode: {ROUTE_TYPE_DESCRIPTIONS.get(route_type, route_type)}")
    if attrs.get("color"):
        lines.append(f"  Color: #{attrs['color']}")
    if attrs.get("text_color"):
        lines.append(f"  Text color: #{attrs['text_color']}")
    return "\n".join(lines)


def summarize_schedule(schedule: Mapping[str, Any]) -> str:
    attrs = schedule.get("attributes", {})
    arrival = parse_iso_datetime(attrs.get("arrival_time"))
    departure = parse_iso_datetime(attrs.get("departure_time"))
    stop_id = schedule.get("relationships", {}).get("stop", {}).get("data", {}).get("id")
    trip_id = schedule.get("relationships", {}).get("trip", {}).get("data", {}).get("id")

    lines = [
        f"• Trip `{trip_id or 'unknown'}`",
        f"  Stop: {stop_id or 'unknown'}",
        f"  Arrival: {arrival}",
        f"  Departure: {departure}",
    ]
    headsign = attrs.get("headsign")
    if headsign:
        lines.append(f"  Headsign: {headsign}")
    if attrs.get("stop_sequence") is not None:
        lines.append(f"  Stop sequence: {attrs['stop_sequence']}")
    return "\n".join(lines)


def render_json(data: Iterable[Mapping[str, Any]]) -> str:
    return json.dumps(list(data), indent=2)
