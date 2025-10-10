# boston-core-mcp

Multi‑server MCP repository for the City of Boston DoIT team. It provides Model Context Protocol (MCP) servers that let LLMs and agentic tools safely access Boston’s open data and related municipal services.

The first included server is a Boston Open Data MCP server that exposes safe, read‑only access to Boston’s CKAN data portal for discovery and querying.

## Quick Start

- Requirements: Python 3.10+ recommended
- Create and activate a virtual environment
  - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
  - Windows (PowerShell): `py -m venv .venv; .\.venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`
- Run the server directly: `python -m servers.boston_opendata.main`

If the process prints a startup message to stderr and then waits, it’s running correctly as an MCP stdio server.

## Repository Structure

- `servers/` – MCP servers (one package per server)
  - `boston_opendata/` – CKAN/“Boston Open Data” server
    - `main.py` – entrypoint for stdio server
    - `server.py` – MCP app and tool handlers
    - `ckan.py` – CKAN API client helpers
    - `formatters.py` – presentation helpers for datasets/resources
    - `config.py` – server configuration constants
- `examples/` – optional example scripts for manual testing
- `requirements.txt` – minimal runtime dependencies
- `LICENSE` – licensing information

## Boston Open Data MCP Server

This server exposes safe, read‑only tools to browse datasets and query CKAN DataStore resources from `https://data.boston.gov`.

Available tools:
- `search_datasets(query, limit=10)` – keyword search across datasets
- `list_all_datasets(limit=20)` – list dataset IDs for browsing
- `get_dataset_info(dataset_id)` – full dataset metadata + resources
- `get_datastore_schema(resource_id)` – field names and data types
- `query_datastore(resource_id, limit=10, offset=0, search_text, filters, sort, fields)` – fetch tabular records

Notes:
- Only resources with “DataStore active” are queryable via `query_datastore`.
- `filters` should be an object mapping field names to exact values.
- Pagination uses `limit` and `offset`.

## Connect To LLMs (MCP Clients)

You can connect this server to any MCP‑compatible client. Two common options are outlined below.

### Claude Desktop (macOS/Windows)

1) Open your Claude Desktop config file and add a server entry under `mcpServers`.

On macOS, the config is typically at: `~/Library/Application Support/Claude/claude_desktop_config.json`

Example entry:

```
{
  "mcpServers": {
    "boston-opendata": {
      "command": "python",
      "args": ["-m", "servers.boston_opendata.main"],
      "cwd": "<path-to-your-cloned-repo>"
    }
  }
}
```

2) Restart Claude Desktop. In a new chat, ask Claude to “list available tools”. You should see the Boston Open Data tools.

### Generic MCP Clients / CLI

Any client that speaks MCP over stdio can launch the server as a subprocess using the same command:

- Command: `python`
- Args: `-m servers.boston_opendata.main`
- Working directory: repository root

## Example Interactions

- “Search for 311 datasets and show the top 5.” → `search_datasets { query: "311", limit: 5 }`
- “Show resources for dataset `311-service-requests`.” → `get_dataset_info { dataset_id: "311-service-requests" }`
- “What fields exist for resource `<uuid>`?” → `get_datastore_schema { resource_id: "<uuid>" }`
- “Query the last 20 records sorted by date desc.” → `query_datastore { resource_id: "<uuid>", limit: 20, sort: "date desc" }`

## Development

- Run locally: `python -m servers.boston_opendata.main`
- Linting/formatting: use your preferred tools; no enforced config yet.
- Example script: see `examples/ckan_request_demo.py` (optional extras).

## Troubleshooting

- “No queryable resources”: Some datasets expose files only (no DataStore). Use download links instead; they are not accessible via `query_datastore`.
- HTTP errors: The server returns detailed messages including API endpoints. Re‑run with a stable network connection.
- Long outputs: Use `limit` and `offset` to paginate results.

## Contributors

See `CONTRIBUTORS.md` for acknowledgements and contribution guidelines.

## License

Licensed under the terms in `LICENSE`.
