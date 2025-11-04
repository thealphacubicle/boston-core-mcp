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

| Server | Description | Deployment Options |
| --- | --- | --- |
| `servers/boston_opendata` | Exposes Boston's CKAN portal (`https://data.boston.gov`) through MCP tools for dataset discovery and DataStore queries. | stdio (local), **Lambda (production)** |
| `servers/boston_opendata_lambda` | Lambda-compatible version using MCPEngine for serverless AWS deployment. Same functionality as stdio version. | **AWS Lambda only** |
| `servers/mbta_server` | MBTA v3 API: predictions, service alerts, stop search, routes, and schedules. Optional `MBTA_API_KEY` for higher rate limits. | stdio (local) |
| `servers/census_server` | U.S. Census Bureau APIs: ACS 5-year and 2020 Decennial PL tables, variable search, and geography listings. | stdio (local) |

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

## Deployment Options

### Local Development (stdio)

All servers can run locally using stdio communication, ideal for development and testing.

### AWS Lambda Deployment (Production)

The **Boston OpenData MCP server** includes a production-ready Lambda deployment option using [MCPEngine](https://www.featureform.com/post/deploy-mcp-on-aws-lambda-with-mcpengine):

- **Location**: `servers/boston_opendata_lambda/`
- **Infrastructure**: Fully automated Terraform scripts for AWS resources
- **Features**: HTTP-based, stateless, scalable, with built-in monitoring
- **Documentation**: See [`servers/boston_opendata_lambda/README.md`](servers/boston_opendata_lambda/README.md) and [`servers/boston_opendata_lambda/terraform/README.md`](servers/boston_opendata_lambda/terraform/README.md)

#### Quick Lambda Deployment

```bash
cd servers/boston_opendata_lambda/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your configuration
terraform init
terraform apply
# Build and push Docker image
# Update Lambda function code
```

**Required AWS Permissions**: See [`servers/boston_opendata_lambda/terraform/AWS_PERMISSIONS.md`](servers/boston_opendata_lambda/terraform/AWS_PERMISSIONS.md) for detailed IAM permissions needed.

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
    "boston-opendata-lambda": {
      "command": "mcpengine",
      "args": ["proxy", "boston-opendata-lambda", "https://your-lambda-url.lambda-url.us-east-1.on.aws/", "--mode", "http", "--claude"],
      "env": {}
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

After editing, fully restart Claude Desktop and ask it to list available tools. You should see tools from all servers.

## Repository Structure

```
servers/                      # MCP server packages (one per service)
  boston_opendata/            # Boston Open Data MCP server (stdio version)
  boston_opendata_lambda/     # Boston Open Data MCP server (Lambda/production)
    terraform/                 # Infrastructure as Code for AWS deployment
      main.tf                  # Terraform configuration (ECR, Lambda, IAM, etc.)
      variables.tf             # Input variables
      outputs.tf               # Deployment outputs
      AWS_PERMISSIONS.md       # Required AWS IAM permissions
      README.md                # Terraform deployment guide
    lambda_server.py          # MCPEngine-based Lambda handler
    Dockerfile                # Container image definition
  mbta_server/                # MBTA MCP server implementation
  census_server/              # Census MCP server implementation
docs/                         # Project documentation
  QUICKSTART.md              # Quick start guide
  DEVELOPMENT.md             # Development notes
requirements.txt             # Python dependencies shared across servers
LICENSE                      # Project license (MIT)
CONTRIBUTORS.md              # Acknowledgements and contribution guidelines
```

## Documentation

- **Quickstart:** [`docs/QUICKSTART.md`](docs/QUICKSTART.md) – install, run, and client integration steps (Boston Open Data focused; patterns apply to all).
- **Development notes:** [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) – architecture, design decisions, and roadmap.
- **Lambda Deployment:** [`servers/boston_opendata_lambda/README.md`](servers/boston_opendata_lambda/README.md) – Lambda-specific setup and usage.
- **Terraform Guide:** [`servers/boston_opendata_lambda/terraform/README.md`](servers/boston_opendata_lambda/terraform/README.md) – step-by-step AWS infrastructure deployment.
- **AWS Permissions:** [`servers/boston_opendata_lambda/terraform/AWS_PERMISSIONS.md`](servers/boston_opendata_lambda/terraform/AWS_PERMISSIONS.md) – required IAM permissions for Terraform deployment.

## Infrastructure & DevOps

### Terraform Configuration

The Boston OpenData Lambda server includes production-ready Terraform scripts that create:

- **ECR Repository**: Container image storage with lifecycle policies
- **Lambda Function**: Serverless compute with configurable timeout, memory, and architecture (ARM64/x86_64)
- **Lambda Function URL**: HTTPS endpoint for HTTP-based MCP communication
- **IAM Roles & Policies**: Least-privilege permissions for execution, logging, and optional X-Ray tracing
- **CloudWatch Log Groups**: Centralized logging with configurable retention

**Key Features:**
- ✅ Validated and tested Terraform configuration
- ✅ Supports both ARM64 (cost-effective) and x86_64 architectures
- ✅ Optional X-Ray tracing for distributed debugging
- ✅ Automatic image lifecycle management (keeps last 10 images)
- ✅ Comprehensive security with IAM best practices

**Recent Improvements:**
- Fixed ECR lifecycle policy configuration for AWS provider v5.0+
- Added conditional X-Ray permissions when tracing is enabled
- Added Lambda Function URL invoke permissions for public access
- Created detailed AWS permissions documentation

## Community & Contributions

This project is maintained by the City of Boston DoIT team. Issues and pull requests that strengthen the reliability, safety, or usability of the MCP servers are welcome. Please review [`CONTRIBUTORS.md`](CONTRIBUTORS.md) before contributing.

## License

Distributed under the terms described in [`LICENSE`](LICENSE).
