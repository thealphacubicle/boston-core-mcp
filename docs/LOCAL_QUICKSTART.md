# Quick Start: Run Boston OpenData MCP Locally

Connect Claude Desktop to a local instance of the Boston OpenData MCP server — no Docker, no AWS, no proxy required.

## What You'll Need

1. **Python 3.10+** — check with `python --version`
2. **Claude Desktop** — download from [claude.ai/download](https://claude.ai/download)

## Setup

### Step 1: Clone the repo and install dependencies

```bash
git clone https://github.com/thealphacubicle/boston-core-mcp.git
cd boston-core-mcp
pip install -r requirements.txt
```

Or with [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
uv sync
```

### Step 2: Add the server to Claude Desktop

Open your Claude Desktop config file:

- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the following inside `"mcpServers"` (replace the path with your actual clone location):

**Using pip (Mac/Linux):**
```json
"boston-opendata-lambda": {
  "command": "python",
  "args": ["-m", "servers.boston_opendata_lambda.lambda_server", "--stdio"],
  "cwd": "/path/to/boston-core-mcp"
}
```

**Using pip (Windows):**
```json
"boston-opendata-lambda": {
  "command": "python",
  "args": ["-m", "servers.boston_opendata_lambda.lambda_server", "--stdio"],
  "cwd": "C:\\path\\to\\boston-core-mcp"
}
```

**Using uv (Mac/Linux):**
```json
"boston-opendata-lambda": {
  "command": "uv",
  "args": ["run", "--directory", "/path/to/boston-core-mcp", "python", "-m", "servers.boston_opendata_lambda.lambda_server", "--stdio"]
}
```

**Using uv (Windows):**
```json
"boston-opendata-lambda": {
  "command": "uv",
  "args": ["run", "--directory", "C:\\path\\to\\boston-core-mcp", "python", "-m", "servers.boston_opendata_lambda.lambda_server", "--stdio"]
}
```

### Step 3: Restart Claude Desktop

Fully quit and reopen Claude Desktop. The Boston OpenData tools will appear automatically — no terminal to keep open.

## Test It

Try asking Claude:

- "Search for 311 datasets in Boston"
- "What parking data is available?"
- "Show me recent crime incidents"

## How It Works

Claude Desktop spawns the server as a subprocess and communicates via stdin/stdout (stdio). This means:

- No separate terminal to keep open
- No Docker required
- No proxy required
- Claude Desktop manages the server lifecycle automatically

## Troubleshooting

### Tools don't appear in Claude Desktop

1. Make sure you fully quit and relaunched Claude Desktop (not just closed the window)
2. Verify the path in the config is correct and absolute
3. Test the server manually:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | uv run python -m servers.boston_opendata_lambda.lambda_server --stdio
   ```
   You should see a JSON response. If you see an error, check that `uv sync` completed successfully.

### "Module not found" error

Make sure `--directory` in the config points to the project root (where `pyproject.toml` lives), not a subdirectory.

### Debug logging

Set environment variables in the Claude Desktop config to enable debug output:

```json
"boston-opendata-lambda": {
  "command": "uv",
  "args": ["run", "--directory", "/path/to/boston-core-mcp", "python", "-m", "servers.boston_opendata_lambda.lambda_server", "--stdio"],
  "env": {
    "BOSTON_OPENDATA_LOG_LEVEL": "DEBUG"
  }
}
```

## Available Tools

| Tool | Description |
|---|---|
| `search_datasets` | Search by keyword (e.g. "311", "parking", "crime") |
| `list_all_datasets` | Browse all available datasets |
| `get_dataset_info` | Get resources and metadata for a dataset |
| `get_datastore_schema` | See field names and types for a resource |
| `query_datastore` | Fetch actual data records |

## Next Steps

- **Use the deployed Lambda instead**: See [LAMBDA_QUICKSTART.md](LAMBDA_QUICKSTART.md) to connect to the hosted server (requires Docker)
- **Deploy your own Lambda**: See [LAMBDA_DEPLOYMENT.md](LAMBDA_DEPLOYMENT.md)
