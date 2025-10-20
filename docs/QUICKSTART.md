# QUICKSTART

Audience

This guide is for running the Boston Open Data MCP server locally and connecting it to an MCP client (for example, Claude Desktop). It is Python‑only and based on this repository’s files.

Requirements

- Python 3.10+ recommended
- pip
- A terminal (macOS/Linux/Windows)
- Optional: a code editor

Install dependencies

1) Create and activate a virtual environment

- macOS/Linux:
  python3 -m venv .venv
  source .venv/bin/activate

- Windows (PowerShell):
  py -m venv .venv
  .\.venv\Scripts\Activate.ps1

2) Install packages

- From the repository root:
  pip install -r requirements.txt

The minimal dependencies for this server are:
- httpx>=0.27
- mcp>=1.2

Run the server (stdio)

- From the repository root:
  python -m servers.boston_opendata.main

What to expect

- The server prints a startup message to stderr and then appears idle. That’s correct: it is waiting for an MCP client to connect over stdio.

Repository structure (relevant files)

- servers/boston_opendata/main.py — entry point that starts the MCP server over stdio
- servers/boston_opendata/server.py — defines the MCP app and tools (search, list, schema, query)
- servers/boston_opendata/ckan.py — CKAN API calls
- servers/boston_opendata/formatters.py — result shaping for LLMs
- servers/boston_opendata/config.py — key settings (CKAN_BASE_URL, API_TIMEOUT, MAX_RECORDS)
- requirements.txt — runtime dependencies

Connect to Claude Desktop (example)

1) Locate your Claude Desktop config file and add an MCP server entry under mcpServers.

- macOS (typical):
  ~/Library/Application Support/Claude/claude_desktop_config.json

- Windows (typical):
  %AppData%\Claude\claude_desktop_config.json

2) Add or merge this entry, updating cwd to your local repo path:

{
  "mcpServers": {
    "boston-opendata": {
      "command": "python",
      "args": ["-m", "servers.boston_opendata.main"],
      "cwd": "<path-to-your-cloned-repo>"
    }
  }
}

3) Restart Claude Desktop. In a new chat, ask: “List available tools.” You should see the Boston Open Data tools.

Available tools (what you’ll see in clients)

- search_datasets(query, limit=10)
- list_all_datasets(limit=20)
- get_dataset_info(dataset_id)
- get_datastore_schema(resource_id)
- query_datastore(resource_id, limit=10, offset=0, search_text, filters, sort, fields)

Notes and tips

- Read‑only: This server does not write or modify CKAN data.
- Limits: MAX_RECORDS in config.py caps results for safety (default 1000).
- Timeouts: API_TIMEOUT in config.py (default 30s) keeps requests responsive.
- DataStore only: query_datastore works for resources with “DataStore active.”

Troubleshooting

- “ModuleNotFoundError: mcp” or “httpx not found”:
  - Ensure your virtual environment is activated and run pip install -r requirements.txt.

- Claude Desktop doesn’t show the tools:
  - Double‑check the claude_desktop_config.json path and that cwd points to this repo.
  - Restart Claude Desktop after editing the config.

- Using the wrong Python:
  - On macOS/Linux, verify python3 --version (or which python).
  - On Windows, verify py -V and that the venv is activated.

- Nothing happens when running main:
  - That’s expected until a client connects. The server is an MCP stdio process.

Customizing (optional)

- To target a different CKAN instance or adjust limits/timeouts, edit servers/boston_opendata/config.py:
  - CKAN_BASE_URL: base API endpoint (defaults to Boston’s portal).
  - API_TIMEOUT: per‑request timeout (seconds).
  - MAX_RECORDS: hard cap for returned rows.

That’s it — your Python MCP server should be ready to use with MCP‑compatible clients like Claude Desktop.
