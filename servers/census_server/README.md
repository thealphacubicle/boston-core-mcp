# Census Bureau MCP Server

This server provides access to the U.S. Census Bureau's developer APIs through the Model Context Protocol (MCP). It mirrors the architecture of the existing Boston Open Data server in this repository and is implemented in Python using `httpx` and `mcp-server` helpers.

## Features

- Query ACS 5-year estimates and 2020 Decennial (PL) tables by geography
- Retrieve detailed variable metadata with keyword search support
- Inspect available geography summary levels for each dataset
- Structured, LLM-friendly output with optional JSON payloads
- Graceful error handling and rate-limit awareness

## Requirements

1. **Python 3.11** (matches repository baseline)
2. **API Key (recommended)**
   - Sign up for a free key at <https://api.census.gov/data/key_signup.html>
   - Set the environment variable before launching the server:

     ```bash
     export CENSUS_API_KEY="your-key-here"
     ```

   The server can operate without a key for light usage, but the Census API enforces strict rate limits (typically 500 requests per day and 10 per second). With a key you receive higher throughput and clearer error messages when throttled.

## Running the server

```bash
python -m servers.census_server.main
```

The server communicates over stdio, so it can be registered with any MCP-compatible client that supports Python servers.

## Available Tools

### `get_acs_data`
Query ACS 5-year estimates (default year: 2022). Example arguments:

```json
{
  "variables": ["B01003_001E", "B19013_001E"],
  "geography": {
    "level": "tract",
    "state": "25",
    "county": "025",
    "tract": "021400"
  },
  "year": 2022,
  "return_json": true
}
```

### `get_decennial_data`
Retrieve decennial census values (default 2020 PL dataset).

```json
{
  "variables": ["P1_001N"],
  "geography": {
    "level": "block_group",
    "state": "25",
    "county": "025",
    "tract": "021400",
    "block_group": "1"
  }
}
```

### `search_variables`
Search dataset metadata for variables that match a keyword.

```json
{
  "dataset": "acs5",
  "keyword": "median income"
}
```

### `get_geographies`
List available geography levels and required FIPS codes.

```json
{
  "dataset": "decennial_pl",
  "year": 2020
}
```

## Geography helpers

| Level         | Required fields                                                                  |
| ------------- | --------------------------------------------------------------------------------- |
| `us`          | *(none)*                                                                          |
| `state`       | `state` (2-digit FIPS)                                                            |
| `county`      | `state`, `county`                                                                 |
| `place`       | `state`, `place`                                                                  |
| `tract`       | `state`, `county`, `tract`                                                        |
| `block_group` | `state`, `county`, `tract`, `block_group`                                         |

Remember that Massachusetts has state FIPS code `25`, Suffolk County is `025`, and Boston-area tracts/block groups follow Census definitions.

## Troubleshooting

- **Rate limiting** – The Census API may return HTTP 429 or 503 errors when requests are too frequent. The server surfaces these as clear error messages. Retry after waiting or reduce request volume.
- **Variable errors** – If a variable ID is invalid for the selected dataset/year, the API will respond with an informative message. Use `search_variables` to double-check available fields.
- **Geography mismatch** – Ensure that geography fields match the requested level; for example, tracts require both `state` and `county` codes.

## License

This server follows the repository's overall licensing (MIT). See `LICENSE` at the project root for details.
