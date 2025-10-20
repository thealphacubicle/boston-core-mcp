# MBTA MCP Server

This MCP server integrates the Massachusetts Bay Transportation Authority (MBTA) v3 API, mirroring the structure of the repository's Boston Open Data server. It is implemented in Python and exposes the most commonly used MBTA endpoints as MCP tools.

## Features

- Real-time predictions for any MBTA stop
- Current service alerts with filtering by route, stop, or severity
- Stop search by name or geographic proximity
- Route metadata lookup with mode filtering
- Scheduled arrivals/departures by route and stop
- Human-readable summaries with optional raw JSON payloads for downstream processing

## Requirements

1. **Python 3.11**
2. **MBTA API Key** (free)
   - Register for a key at <https://api-v3.mbta.com/>
   - Export it before launching the server:

     ```bash
     export MBTA_API_KEY="your-key-here"
     ```

   The MBTA API enforces rate limits (typically 20 requests per second per IP). Requests without a key are heavily throttled, so using a key is strongly recommended.

## Running the server

```bash
python -m servers.mbta_server.main
```

## Available Tools

### `get_predictions`
Fetch live arrivals/departures for a stop.

```json
{
  "stop_id": "place-sstat",
  "route_id": "CR-Fairmount",
  "limit": 5,
  "include_json": true
}
```

### `get_alerts`
List current service alerts.

```json
{
  "route_id": "Orange",
  "severity": 5
}
```

### `get_stops`
Search MBTA stops.

```json
{
  "name": "Airport",
  "route_type": 0
}
```

### `get_routes`
Retrieve route metadata.

```json
{
  "route_type": 1,
  "limit": 10
}
```

### `get_schedules`
View scheduled service.

```json
{
  "route_id": "Green-B",
  "stop_id": "70265",
  "date": "2024-05-01"
}
```

## Filtering tips

- **Route types** – use integers per MBTA docs (0 light rail, 1 heavy rail, 2 commuter rail, 3 bus, 4 ferry).
- **Location search** – supply `latitude`, `longitude`, and optionally `radius` (meters) to find nearby stops.
- **Predictions vs. schedules** – predictions are real-time; schedules return the published timetable.

## Troubleshooting

- **429 errors** – indicate rate limiting. Reduce frequency or ensure your API key is configured.
- **Empty results** – the API often returns an empty list when filters are too narrow. Try removing filters or verifying IDs via `get_routes`/`get_stops` first.
- **Direction IDs** – the MBTA uses `0` and `1` to represent outbound/inbound depending on the route. Consult `get_routes` descriptions or MBTA docs for specifics.

## License

This server inherits the repository's MIT license. See the root `LICENSE` file for details.
