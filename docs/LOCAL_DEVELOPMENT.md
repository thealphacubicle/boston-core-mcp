# Local Development Guide

This guide covers running and developing the Boston OpenData MCP server locally.

## Overview

The Boston OpenData MCP server can run locally using HTTP mode for testing and development. This allows you to:

- Test changes before deploying
- Develop new features
- Debug issues locally
- Test with Claude Desktop

## Prerequisites

1. **Python 3.10+** installed
2. **Docker Desktop** installed and running (for MCPEngine proxy)
3. **MCPEngine CLI** installed

## Installation

### Step 1: Install Dependencies

```bash
# From project root
pip install -r requirements.txt
pip install -e ".[dev]"  # Optional: for development tools
```

### Step 2: Install MCPEngine CLI

```bash
# Using pipx (recommended)
pipx install 'mcpengine[cli]'

# Or using pip
pip install 'mcpengine[cli]'
```

## Running the Server

### Method 1: MCPEngine Proxy (Recommended for Development)

This is the main workflow for testing with Claude Desktop:

**Terminal 1 - Start the server:**

```bash
# From project root
python -m servers.boston_opendata_lambda.lambda_server
```

You should see output like:

```
INFO: MCPEngine initialized successfully
INFO: Lambda handler created successfully
INFO: Starting Boston OpenData MCP Server (Lambda version) for local testing
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The server is now running on `http://localhost:8000`.

**Terminal 2 - Start the proxy:**

```bash
mcpengine proxy boston-opendata-lambda http://localhost:8000/mcp --mode http --claude
```

**Terminal 3 - Open Claude Desktop:**

1. Open Claude Desktop
2. Restart Claude Desktop if it was already open
3. Start a new conversation
4. The Boston OpenData tools should now be available!

### Method 2: Direct Function Testing

Run the test script to verify tools work correctly:

```bash
python servers/boston_opendata_lambda/tests/test_local.py
```

### Method 3: Direct HTTP Testing

Test the server directly via HTTP using MCP protocol:

```bash
# Initialize the MCP session
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'

# List available tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Call a tool
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search_datasets",
      "arguments": {"query": "311", "limit": 5}
    }
  }'
```

## Available Tools

The server provides five tools:

1. **`search_datasets`** - Search for datasets using keywords

   - Example: `search_datasets(query="311", limit=10)`

2. **`list_all_datasets`** - List all available datasets

   - Example: `list_all_datasets(limit=20)`

3. **`get_dataset_info`** - Get detailed information about a specific dataset

   - Example: `get_dataset_info(dataset_id="crime-incident-reports")`

4. **`query_datastore`** - Query actual data from DataStore resources

   - Example: `query_datastore(resource_id="abc123", limit=100)`

5. **`get_datastore_schema`** - Get schema information for DataStore resources
   - Example: `get_datastore_schema(resource_id="abc123")`

## Environment Variables

The server uses environment variables for configuration. Key variables:

```bash
# CKAN API Configuration
BOSTON_OPENDATA_CKAN_BASE_URL=https://data.boston.gov/api/3/action

# Timeout Configuration
BOSTON_OPENDATA_API_TIMEOUT=30.0
BOSTON_OPENDATA_CONNECT_TIMEOUT=10.0
BOSTON_OPENDATA_READ_TIMEOUT=30.0

# Rate Limiting
BOSTON_OPENDATA_RATE_LIMIT_CAPACITY=100
BOSTON_OPENDATA_RATE_LIMIT_REFILL_RATE=1.67

# Logging
BOSTON_OPENDATA_LOG_LEVEL=INFO
BOSTON_OPENDATA_LOG_FORMAT=json
BOSTON_OPENDATA_ENVIRONMENT=development
```

See `servers/boston_opendata_lambda/config.py` for all available configuration options.

## Development Workflow

### Making Changes

1. **Edit code** in `servers/boston_opendata_lambda/`
2. **Restart the server** (Ctrl+C and restart)
3. **Restart the proxy** if needed
4. **Test in Claude Desktop** or with test scripts

### Adding New Tools

1. Add the tool function with `@engine.tool()` decorator in `lambda_server.py`
2. Include proper docstring for LLM tool selection
3. Return formatted string (not TextContent)
4. Handle errors with try/except and return error strings
5. Tools are automatically discovered via `tools/list` endpoint

Example:

```python
@engine.tool()
async def my_new_tool(param: str) -> str:
    """Description of what this tool does.

    Use this when the user wants to...

    Args:
        param: Description of parameter

    Returns:
        Description of return value
    """
    try:
        # Your implementation
        result = await some_async_operation(param)
        return format_result(result)
    except Exception as e:
        logger.error(f"Error in my_new_tool: {e}")
        return format_error_message("Error", str(e))
```

### Testing Changes

1. **Run local tests:**

   ```bash
   python servers/boston_opendata_lambda/tests/test_local.py
   ```

2. **Test with MCPEngine proxy** - Use Claude Desktop to test tools

3. **Verify tool outputs** match expected format

4. **Check logs** for errors or warnings

## Architecture

### Server Components

- **`lambda_server.py`** - Main server code with tool definitions
- **`ckan.py`** - CKAN API client with retry logic
- **`config.py`** - Configuration management (Pydantic settings)
- **`utils/`** - Utility modules:
  - `formatters.py` - Response formatting utilities
  - `exceptions.py` - Custom exception types
  - `validators.py` - Input validation helpers
  - `logger.py` - Structured logging setup
  - `rate_limiter.py` - Rate limiting implementation
  - `circuit_breaker.py` - Circuit breaker implementation

### MCPEngine Integration

- **Tool Registration**: Uses `@engine.tool()` decorators
- **Context Management**: HTTP client lifecycle via `app_lifespan()`
- **Error Handling**: Returns formatted error strings
- **Lambda Handler**: Generated via `engine.get_lambda_handler()`
- **Endpoint**: MCP protocol messages are served at `/mcp` path

## Troubleshooting

### Server Won't Start

- Ensure you're in the project root directory when running the command
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Python 3.10+ is being used: `python --version`

### Proxy Connection Fails

- Make sure the server is running on port 8000 before starting the proxy
- Check that `http://localhost:8000/mcp` is accessible (note the `/mcp` path)
- Verify MCPEngine CLI is installed: `pipx list` or `pip list | grep mcpengine`
- Ensure Docker Desktop is running (required for proxy)

### Tools Not Appearing in Claude Desktop

- Ensure both the server AND proxy are running (you need two terminals)
- Restart Claude Desktop after starting the proxy
- Check the server terminal for error messages
- Verify the proxy is connected: Check Docker containers with `docker ps`

### Connection Issues

- **CKAN API unavailable**: Check `https://data.boston.gov` is accessible
- **Tool Not Found**: Verify tool registration and docstring format
- **Timeout Errors**: Adjust timeout settings in config or environment variables

### Debug Mode

Enable debug logging:

```bash
export BOSTON_OPENDATA_LOG_LEVEL=DEBUG
export BOSTON_OPENDATA_DEBUG=true
python -m servers.boston_opendata_lambda.lambda_server
```

### Stopping the Servers

To stop the servers:

- Press `CTRL+C` in the terminal running the server
- Press `CTRL+C` in the terminal running the proxy
- Restart both when making code changes

## Code Quality

### Formatting

The project uses `black` for code formatting:

```bash
# Check formatting
black --check --diff servers/

# Format code
black servers/
```

### Type Checking

The code uses Python type hints. Consider using `mypy` for type checking:

```bash
pip install mypy
mypy servers/boston_opendata_lambda/
```

### Testing

Run the test suite:

```bash
# Run all tests
python -m pytest servers/boston_opendata_lambda/tests/

# Run specific test file
python servers/boston_opendata_lambda/tests/test_local.py
```

## Next Steps

- **Deploy to Lambda**: See [Lambda Deployment Guide](LAMBDA_DEPLOYMENT.md)
- **Set up CI/CD**: See [CI/CD Guide](CI_CD_GUIDE.md)
- **Learn Architecture**: See [Development Guide](DEVELOPMENT.md)
