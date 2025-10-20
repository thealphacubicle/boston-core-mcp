# Boston Core MCP

Boston Core MCP is a collection of Model Context Protocol (MCP) servers created by the City of Boston Department of Innovation and Technology (DoIT). These servers give large language models and agentic tools safe, read-only access to Boston's open data portal so that staff, residents, and partners can explore trusted civic information in conversational workflows.

## Overview

The repository currently includes the Boston Open Data MCP server. It wraps the City's CKAN instance and presents a curated toolset for searching datasets, inspecting metadata, and querying DataStore-backed resources. Each tool is designed with clear contracts, conservative limits, and descriptive outputs to make integrations predictable for AI assistants.

Key characteristics:

- **Safety first** – all interactions are read-only with enforced timeouts and record limits.
- **LLM-friendly outputs** – responses are formatted for natural-language assistants and autonomous agents.
- **Minimal dependencies** – lightweight Python stack keeps deployment straightforward.

## Included Server

| Server | Description |
| --- | --- |
| `servers/boston_opendata` | Exposes Boston's CKAN portal (`https://data.boston.gov`) through MCP tools for dataset discovery and DataStore queries. |

## Repository Structure

```
servers/              # MCP server packages (one per service)
  boston_opendata/    # Boston Open Data MCP server implementation
examples/             # Optional example scripts for manual testing
requirements.txt      # Python dependencies shared across servers
LICENSE               # Project license (MIT)
CONTRIBUTORS.md       # Acknowledgements and contribution guidelines
```

## Documentation

- **Quickstart guide:** See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) for installation, configuration, and client integration steps.
- **Development notes:** See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for architectural context, design decisions, and future roadmap ideas.

## Community & Contributions

This project is maintained by the City of Boston DoIT team. Issues and pull requests that strengthen the reliability, safety, or usability of the MCP servers are welcome. Please review [`CONTRIBUTORS.md`](CONTRIBUTORS.md) before contributing.

## License

Distributed under the terms described in [`LICENSE`](LICENSE).
