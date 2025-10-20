# Development Notes

The Boston Core MCP project was created by the City of Boston Department of Innovation and Technology (DoIT) to deliver Model Context Protocol (MCP) servers that unlock conversational access to municipal open data. This document explains how the codebase was developed, the decisions that shaped the architecture, and the benefits the MCP server provides to the City.

## How the Code Was Developed

1. **Discovery and requirements gathering** – Product, data, and AI specialists reviewed common workflows for staff and residents who rely on Boston's open data portal. The team defined guardrails (read-only, predictable response sizes, explicit timeouts) to keep interactions safe for automated agents.
2. **Tool surface design** – Engineers mapped each user goal to a discrete MCP tool (e.g., search datasets, inspect metadata, query DataStore tables). Tool names, input schemas, and descriptions were refined to be self-explanatory for LLM clients.
3. **Service implementation** – The server was built in Python with a lightweight dependency set. Network access to CKAN is encapsulated in `ckan.py`, while tool orchestration lives in `server.py`. Configuration parameters are centralized in `config.py` so environments can tune limits without code changes.
4. **Formatting and UX polish** – Response formatting in `formatters.py` focuses on clarity for conversational agents: summaries highlight the most relevant metadata, schemas are presented in readable tables, and record payloads are capped for safety.
5. **Validation with MCP clients** – The team exercised the stdio entry point (`main.py`) with MCP-compatible clients such as Claude Desktop, iterating on tool descriptions, error messaging, and performance safeguards until the integration felt reliable.
6. **Documentation and maintenance** – Quickstart and reference materials were added to support city staff and contributors. Version control practices and dependency pinning make future updates auditable and straightforward.

## Architecture Overview

- **`servers/boston_opendata/main.py`** – Launches the stdio MCP server and registers the application with connected clients.
- **`servers/boston_opendata/server.py`** – Defines the MCP app, available tools, and high-level control flow for requests.
- **`servers/boston_opendata/ckan.py`** – Handles HTTP interactions with Boston's CKAN API, including retries and response validation.
- **`servers/boston_opendata/formatters.py`** – Shapes dataset metadata and query results into concise structures suitable for AI consumption.
- **`servers/boston_opendata/config.py`** – Centralizes configuration constants such as the CKAN base URL, timeouts, and maximum record counts.

This modular layout separates concerns so developers can evolve networking, tooling, or presentation layers independently.

## Impacts and Benefits for the City of Boston

- **Faster insight for staff** – City employees can ask natural-language questions and receive curated data summaries without navigating the portal manually.
- **Improved public transparency** – Residents and partners gain easier, conversational access to authoritative data, strengthening trust in municipal services.
- **Safer automation for AI agents** – Read-only tooling, conservative limits, and descriptive outputs enable responsible use of Boston's data within emerging AI ecosystems.
- **Reusable foundation for future servers** – The MCP patterns established here can be replicated for additional civic data sources, accelerating future digital services.

## Design Principles

- **Safety and governance** – Default limits (`MAX_RECORDS`, `API_TIMEOUT`) and explicit tool scopes prevent runaway queries and protect infrastructure.
- **Clarity for AI clients** – Each tool advertises precise inputs and outputs, enabling LLMs to reason about capabilities without guesswork.
- **Extensibility** – New tools or entire servers can be added alongside the existing package structure with minimal coupling.

## Future Enhancements

- Introduce caching layers for popular datasets to improve responsiveness.
- Expand analytics hooks (with privacy safeguards) to observe usage patterns and prioritize improvements.
- Provide richer result previews such as basic statistics or geographic summaries.
- Explore additional MCP servers that surface other city services, reusing shared utilities from this codebase.

The Boston Core MCP project demonstrates how civic technology teams can pair responsible AI practices with open data stewardship, delivering tangible benefits to residents, partners, and internal stakeholders.
