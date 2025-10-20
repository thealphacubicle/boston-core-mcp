# Quickstart

This guide walks through installing and running the Boston Open Data MCP server locally, then connecting it to an MCP-compatible client such as Claude Desktop.

## Audience

Use this document if you are comfortable with a terminal and want to stand up the server for testing or integration work. All instructions assume Python 3.10 or newer.

## Prerequisites

- Python 3.10+
- `pip`
- A terminal on macOS, Linux, or Windows
- (Optional) A code editor for inspecting the source

## 1. Create and Activate a Virtual Environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Install Dependencies

From the repository root, install the required packages:

```bash
pip install -r requirements.txt
```

The core dependencies are:

- `httpx>=0.27`
- `mcp>=1.2`

## 3. Run the MCP Server (stdio)

Launch the Boston Open Data MCP server from the repository root:

```bash
python -m servers.boston_opendata.main
```

Expected behavior:

- The process prints a startup message to stderr.
- The terminal appears idle afterward because the server is waiting for an MCP client connection over stdio.

## Repository Landmarks

- `servers/boston_opendata/main.py` – stdio entry point that launches the MCP server
- `servers/boston_opendata/server.py` – MCP app and tool definitions
- `servers/boston_opendata/ckan.py` – CKAN HTTP client helpers
- `servers/boston_opendata/formatters.py` – response shaping utilities
- `servers/boston_opendata/config.py` – CKAN base URL, timeouts, and safety limits

## Connect to Claude Desktop (Example Client)

1. Locate the Claude Desktop configuration file and add an MCP server entry under `mcpServers`.
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%AppData%\Claude\claude_desktop_config.json`
2. Add (or merge) the following snippet, updating `cwd` to point to your local clone:

```json
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

3. Restart Claude Desktop and start a new conversation. Ask the assistant to "list available tools" to confirm the connection.

## Available Tools

- `search_datasets(query, limit=10)`
- `list_all_datasets(limit=20)`
- `get_dataset_info(dataset_id)`
- `get_datastore_schema(resource_id)`
- `query_datastore(resource_id, limit=10, offset=0, search_text, filters, sort, fields)`

These tools are read-only and honor configuration limits defined in `config.py`.

## Troubleshooting

- **Missing packages (`ModuleNotFoundError`)** – Ensure your virtual environment is activated and rerun `pip install -r requirements.txt`.
- **Claude Desktop does not list the tools** – Verify the configuration path, confirm that `cwd` points to the repository, and restart the application.
- **Python version mismatch** – Check `python3 --version` (macOS/Linux) or `py -V` (Windows) to ensure Python 3.10+ is being used.
- **Server appears idle** – The stdio server waits for clients; this is expected until a connection is made.

## Optional Customization

Adjust the following settings in `servers/boston_opendata/config.py` to tailor the server to your environment:

- `CKAN_BASE_URL` – Target CKAN instance (defaults to Boston's portal)
- `API_TIMEOUT` – Maximum seconds to wait for CKAN responses
- `MAX_RECORDS` – Hard cap on returned rows for safety

You're ready to connect the Boston Core MCP server to any MCP-compatible client.
