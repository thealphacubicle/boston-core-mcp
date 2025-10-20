# Boston Core MCP

Boston Core MCP is a collection of Model Context Protocol (MCP) servers created by the City of Boston Department of Innovation and Technology (DoIT). These servers give large language models and agentic tools safe, read-only access to trusted data so that staff, residents, and partners can explore civic information in conversational workflows.

## Overview

This repository now includes three MCP servers:

- Boston Open Data – wraps the City's CKAN instance for dataset discovery and DataStore queries.
- MBTA – integrates the MBTA v3 API for real-time transit data and metadata.
- U.S. Census – exposes selected Census Bureau endpoints (ACS and 2020 Decennial PL).

Each toolset is designed with clear contracts, conservative limits, and descriptive outputs to make integrations predictable for AI assistants.

Key characteristics:

- **Safety first** – read-only interactions with enforced timeouts and record limits.
- **LLM-friendly outputs** – responses formatted for natural-language assistants and autonomous agents.
- **Minimal dependencies** – lightweight Python stack keeps deployment straightforward.

## Included Servers

| Server | Description |
| --- | --- |
| `servers/boston_opendata` | Exposes Boston's CKAN portal (`https://data.boston.gov`) through MCP tools for dataset discovery and DataStore queries. |
| `servers/mbta_server` | MBTA v3 API: predictions, service alerts, stop search, routes, and schedules. Optional `MBTA_API_KEY` for higher rate limits. |
| `servers/census_server` | U.S. Census Bureau APIs: ACS 5-year and 2020 Decennial PL tables, variable search, and geography listings. |

## Running Locally (stdio)

From the repository root, run any server as a Python module:

```
python -m servers.boston_opendata.main
python -m servers.mbta_server.main
python -m servers.census_server.main
```

Notes:

- Python 3.10+ is recommended. Install dependencies with `pip install -r requirements.txt`.
- For the MBTA server, set an API key (optional but recommended): `export MBTA_API_KEY="your-key"`.

## Connect to Claude Desktop

Claude Desktop can launch multiple MCP servers. Use module execution (`-m`) to avoid relative import issues and set `PYTHONPATH` to your repo root.

Example `claude_desktop_config.json` snippet:

```
{
  "mcpServers": {
    "boston-opendata": {
      "command": "python",
      "args": ["-m", "servers.boston_opendata.main"],
      "env": { "PYTHONPATH": "/absolute/path/to/your/boston-core-mcp" }
    },
    "mbta-server": {
      "command": "python",
      "args": ["-m", "servers.mbta_server.main"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/your/boston-core-mcp",
        "MBTA_API_KEY": "your-key-if-available"
      }
    },
    "census-server": {
      "command": "python",
      "args": ["-m", "servers.census_server.main"],
      "env": { "PYTHONPATH": "/absolute/path/to/your/boston-core-mcp" }
    }
  }
}
```

After editing, fully restart Claude Desktop and ask it to list available tools. You should see tools from all three servers.

## Repository Structure

```
servers/              # MCP server packages (one per service)
  boston_opendata/    # Boston Open Data MCP server implementation
  mbta_server/        # MBTA MCP server implementation
  census_server/      # Census MCP server implementation
examples/             # Optional example scripts for manual testing
requirements.txt      # Python dependencies shared across servers
LICENSE               # Project license (MIT)
CONTRIBUTORS.md       # Acknowledgements and contribution guidelines
```

## Documentation

- **Quickstart:** [`docs/QUICKSTART.md`](docs/QUICKSTART.md) – install, run, and client integration steps (Boston Open Data focused; patterns apply to all).
- **Development notes:** [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) – architecture, design decisions, and roadmap.

## Community & Contributions

This project is maintained by the City of Boston DoIT team. Issues and pull requests that strengthen the reliability, safety, or usability of the MCP servers are welcome. Please review [`CONTRIBUTORS.md`](CONTRIBUTORS.md) before contributing.

## License

Distributed under the terms described in [`LICENSE`](LICENSE).
