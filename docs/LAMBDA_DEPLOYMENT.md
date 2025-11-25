# Boston OpenData MCP Server - Lambda Deployment Guide

This guide covers deploying and developing with the Lambda-compatible version of the Boston OpenData MCP server using MCPEngine for production deployment on AWS Lambda.

## Overview

This server provides the same functionality as the stdio version but is designed for serverless deployment:

- **HTTP-based communication** instead of stdio
- **Stateless design** compatible with AWS Lambda
- **Built-in production features** (rate limiting, circuit breakers, monitoring)
- **Easy deployment** to AWS Lambda with container images

## Features

### Available Tools

1. **search_datasets** - Search for datasets using keywords
2. **list_all_datasets** - List all available datasets
3. **get_dataset_info** - Get detailed information about a specific dataset
4. **query_datastore** - Query actual data from DataStore resources
5. **get_datastore_schema** - Get schema information for DataStore resources

### Key Differences from stdio Version

| Feature         | stdio Version         | Lambda Version         |
| --------------- | --------------------- | ---------------------- |
| Communication   | stdio/SSE             | HTTP                   |
| Deployment      | Local process         | AWS Lambda             |
| State           | Persistent connection | Stateless              |
| Rate Limiting   | Custom implementation | MCPEngine built-in     |
| Circuit Breaker | Custom implementation | MCPEngine built-in     |
| Authentication  | None                  | Optional (future)      |
| Monitoring      | Custom logging        | MCPEngine + CloudWatch |

## Production Deployment

The server is currently deployed at:

```
https://kdbjj7ebdewlcy24bt4wbf3uju0tjgdf.lambda-url.us-east-1.on.aws
```

To connect to the deployed server, see [LAMBDA_QUICKSTART.md](./LAMBDA_QUICKSTART.md).

## Local Development

### Prerequisites

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install MCPEngine CLI:
   ```bash
   pip install mcpengine
   ```

### Running the Server Locally (Step-by-Step)

**Step 1:** Start the HTTP server in your first terminal:

```bash
cd /path/to/boston-core-mcp
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

**Step 2:** In a **second terminal**, start the MCPEngine proxy:

```bash
mcpengine proxy boston-opendata-lambda http://localhost:8000/mcp --mode http --claude
```

This connects the MCP server to Claude Desktop.

**Step 3:** Open Claude Desktop. The Boston OpenData tools should now be available!

### Verification

Once both are running, you should see requests being processed in the server terminal:

```
INFO: Processing request of type ListToolsRequest
INFO: Tool execution started: search_datasets
INFO: Tool executed successfully: search_datasets
```

## Local Testing Methods

### Method 1: MCPEngine Proxy (Recommended for Development)

This is the main workflow for testing with Claude Desktop:

1. Start the server:

   ```bash
   python -m servers.boston_opendata_lambda.lambda_server
   ```

2. In another terminal, start the proxy:

   ```bash
   mcpengine proxy boston-opendata-lambda http://localhost:8000/mcp --mode http --claude
   ```

3. Use Claude Desktop to test the tools

### Method 2: Direct Function Testing

Run the test script to verify tools work correctly:

```bash
python servers/boston_opendata_lambda/tests/test_local.py
```

### Method 3: Direct HTTP Testing

You can also test the server directly via HTTP using MCP protocol:

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

## Environment Variables

The server uses the same configuration as the stdio version. Key environment variables:

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

## Architecture

### Shared Components

The Lambda version reuses several components from the stdio server:

- `ckan.py` - CKAN API client with retry logic
- `config.py` - Configuration management
- `formatters.py` - Output formatting
- `exceptions.py` - Custom exception types
- `validators.py` - Input validation

### MCPEngine Integration

- **Tool Registration**: Uses `@engine.tool()` decorators
- **Context Management**: HTTP client lifecycle via `app_lifespan()`
- **Error Handling**: Returns formatted error strings instead of TextContent
- **Lambda Handler**: Generated via `engine.get_lambda_handler()`
- **Endpoint**: MCP protocol messages are served at `/mcp` path

## Deployment to AWS Lambda

For detailed deployment instructions using Terraform, see:

- [Terraform Deployment Guide](../servers/boston_opendata_lambda/terraform/README.md)
- [AWS Permissions Required](../servers/boston_opendata_lambda/terraform/AWS_PERMISSIONS.md)

### Quick Deployment Overview

1. **Build Docker Image**:

   **For Mac M1 (ARM64) - Recommended:**

   ```bash
   cd servers/boston_opendata_lambda
   ./build.sh
   ```

   This will build an ARM64 image (faster on M1 Macs). AWS Lambda supports ARM64 (Graviton2), so this works perfectly.

   **For AMD64 (Standard Lambda):**

   ```bash
   cd servers/boston_opendata_lambda
   PLATFORM=linux/amd64 ./build.sh
   ```

   **Manual build:**

   ```bash
   # From project root
   docker build --platform=linux/arm64 -t boston-opendata-mcp -f servers/boston_opendata_lambda/Dockerfile .
   ```

2. **Push to ECR**:

   ```bash
   docker tag boston-opendata-mcp <ecr-url>:latest
   docker push <ecr-url>:latest
   ```

3. **Deploy Lambda Function**:

   ```bash
   aws lambda create-function \
     --function-name boston-opendata-mcp \
     --package-type Image \
     --code ImageUri=<ecr-url>:latest \
     --role <lambda-role-arn>
   ```

4. **Create Function URL**:
   ```bash
   aws lambda create-function-url-config \
     --function-name boston-opendata-mcp \
     --auth-type NONE
   ```

## Development

### Adding New Tools

1. Add the tool function with `@engine.tool()` decorator in `lambda_server.py`
2. Include proper docstring for LLM tool selection
3. Return formatted string (not TextContent)
4. Handle errors with try/except and return error strings
5. Tools are automatically discovered via `tools/list` endpoint - no manual registration needed!

### Testing Changes

1. Run local tests: `python servers/boston_opendata_lambda/tests/test_local.py`
2. Test with MCPEngine proxy locally
3. Verify tool outputs match expected format
4. Test dynamic tool discovery works correctly

## Troubleshooting

### Common Issues

1. **Server won't start**:

   - Ensure you're in the project root directory when running the command
   - Check that all dependencies are installed: `pip install -r requirements.txt`
   - Verify Python 3.10+ is being used

2. **Proxy connection fails**:

   - Make sure the server is running on port 8000 before starting the proxy
   - Check that `http://localhost:8000/mcp` is accessible (note the `/mcp` path)
   - Verify MCPEngine CLI is installed: `pip install mcpengine`

3. **Tools not appearing in Claude Desktop**:

   - Ensure both the server AND proxy are running (you need two terminals)
   - Restart Claude Desktop after starting the proxy
   - Check the server terminal for error messages

4. **404 errors when calling endpoints**:

   - Make sure you're using the `/mcp` path in your requests
   - Example: `http://localhost:8000/mcp` not `http://localhost:8000/`

5. **Connection Issues**: Check CKAN API availability
6. **Tool Not Found**: Verify tool registration and docstring format
7. **Timeout Errors**: Adjust timeout settings in config

### Stopping the Servers

To stop the servers:

- Press `CTRL+C` in the terminal running the server
- Press `CTRL+C` in the terminal running the proxy
- Restart both when making code changes

### Debug Mode

Enable debug logging:

```bash
export BOSTON_OPENDATA_LOG_LEVEL=DEBUG
export BOSTON_OPENDATA_DEBUG=true
```

## Future Enhancements

- [ ] Add authentication support (OIDC/Google SSO)
- [ ] Add monitoring and alerting
- [ ] Support for multiple CKAN instances
- [ ] Caching layer for frequently accessed data
- [ ] Rate limiting per user/IP
