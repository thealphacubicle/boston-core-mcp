# DEVELOPMENT

Purpose

The Boston Core MCP project provides Model Context Protocol (MCP) servers that let large language models (LLMs) and agentic tools safely explore and query Boston’s open data portal. The primary server in this repository makes read‑only requests to Boston’s CKAN instance at https://data.boston.gov and returns helpful, structured results that are easy for AI systems to use responsibly.

What is MCP (in plain language)

- MCP is a simple way for tools (like Claude Desktop) to talk to “servers” that provide capabilities.
- An MCP server describes the tools it offers (for example, “search datasets” or “query a table”) and the shape of inputs/outputs.
- Clients (like an AI assistant) can call those tools safely and predictably. Communication typically happens over stdio (the server is launched as a subprocess and talks via standard input/output).

What this server does

- Focus: Safe, read‑only access to Boston’s CKAN portal. No data is modified.
- Tooling surface (plain language):
  - search_datasets: Find datasets by keyword (e.g., “311”, “permits”, “snow”).
  - list_all_datasets: Browse dataset IDs when you’re not sure what to search for.
  - get_dataset_info: See detailed metadata for a dataset and its resources.
  - get_datastore_schema: Inspect fields and data types for a given resource.
  - query_datastore: Retrieve tabular records from a CKAN “DataStore active” resource, with optional filters, search, sorting, and pagination.
- Safety defaults:
  - Read‑only by design.
  - Record limit cap (MAX_RECORDS) to prevent large, accidental pulls.
  - Request timeouts to avoid long‑running or stuck requests.

How it works (conceptual flow)

1) A client (for example, Claude Desktop) starts the MCP server.
2) The client asks the server “What tools do you offer?” and receives the tool list plus their input shapes.
3) The client calls a tool with specific inputs (like a dataset ID or a resource ID).
4) The server makes an HTTP call to CKAN’s API endpoints at https://data.boston.gov/api/3/action (as configured).
5) The server formats and returns results to the client, staying within safety limits (record caps, timeouts).
6) The client displays the results to the user or uses them to perform follow‑up actions.

Key design choices (mapped to files)

- servers/boston_opendata/server.py: Defines the MCP application and the tool catalog (what’s available and how each tool’s inputs/outputs are shaped). This is where user‑facing capabilities are described for the client.
- servers/boston_opendata/main.py: Starts the MCP server using stdio. This is the “entry point” that clients launch.
- servers/boston_opendata/config.py: Centralizes important runtime settings:
  - CKAN_BASE_URL: Where requests are sent (Boston’s CKAN API).
  - API_TIMEOUT: How long to wait for CKAN before giving up.
  - MAX_RECORDS: Upper bound on records returned to keep interactions fast and safe.
- servers/boston_opendata/ckan.py: Handles CKAN HTTP requests (how we talk to the portal).
- servers/boston_opendata/formatters.py: Shapes responses so they are useful and readable for LLMs.

Why the server is structured this way

- Clarity for AI clients: Tools are narrowly scoped and well‑named, so an assistant can “decide” what to call.
- Safety: Hard limits and timeouts guard against runaway queries and oversized responses.
- Reliability: Separating configuration, network access, tool definitions, and presentation keeps failures localized and easier to debug.
- Extensibility: New tools can be added alongside existing ones without disrupting clients.

Benefits for different audiences

- City staff and the public:
  - Faster discovery of relevant datasets without manually browsing the portal.
  - Natural‑language querying of tabular data for exploration and triage.
- Developers and data practitioners:
  - A consistent, machine‑readable tool interface for the CKAN API.
  - Predictable outputs and guardrails for embedding into agents and workflows.
- AI/agent platforms:
  - A well‑documented, minimal‑dependency server with clear contracts.
  - Read‑only, capped responses reduce the risk of runaway costs or timeouts.

Development process (high‑level)

1) Identify user goals and constraints
   - Use cases: find datasets, inspect schemas, and query records.
   - Constraints: read‑only, capped result sizes, reasonable timeouts.

2) Design the tool surface
   - Choose intuitive tool names and input shapes.
   - Define limits (like MAX_RECORDS) and sensible defaults (like pagination).

3) Implement against CKAN
   - Use a small HTTP client to call CKAN endpoints consistently.
   - Centralize configuration (base URL, timeout) for maintainability.

4) Add formatting and helpful summaries
   - Present outputs with enough context to be useful (dataset summaries, field names, types).
   - Keep results concise so they are easy to read and safe to pass to LLMs.

5) Integrate with MCP stdio
   - Expose the tools to MCP clients via the stdio entry point.
   - Ensure the server identifies itself and lists capabilities clearly on startup.

6) Validate with real workflows
   - Verify tool behavior in a client like Claude Desktop.
   - Iterate on descriptions and result formatting to improve usefulness.

7) Document and version
   - Keep a clear Quickstart and README.
   - Note interface changes (new tools, parameters, or limits).

Core concepts and terminology

- Dataset: A collection in CKAN that may contain one or more resources.
- Resource: An individual file or table within a dataset; tabular resources can be “DataStore active.”
- DataStore active: CKAN’s tabular store that supports schema introspection and queries.
- Filters: Exact match constraints on fields (e.g., { "neighborhood": "South End" }).
- Pagination: limit and offset control how many rows you get and from where to continue.

Roadmap ideas

- Add caching for common requests to improve responsiveness.
- Provide richer result previews (column sampling, basic stats).
- Offer cross‑dataset helpers (e.g., “find datasets with compatible schemas”).
- Optional usage logging with privacy safeguards for operational insight.

Integration in one sentence (for orientation)

An MCP‑compatible client launches the stdio server, asks it what tools it offers, and then calls those tools to search and query Boston’s open data—always read‑only and within pre‑set limits.
