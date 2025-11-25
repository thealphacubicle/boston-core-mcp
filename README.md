# Boston Core MCP

Boston Core MCP is a Model Context Protocol (MCP) server created by the City of Boston Department of Innovation and Technology (DoIT). The server gives large language models and agentic tools safe, read-only access to Boston's open data portal so that staff, residents, and partners can explore civic information in conversational workflows.

## Overview

This repository includes the Boston Open Data MCP server, which wraps the City's CKAN instance (`https://data.boston.gov`) for dataset discovery and DataStore queries. The server provides safe, read-only access to Boston's open data portal through a set of well-defined tools.

The toolset is designed with clear contracts, conservative limits, and descriptive outputs to make integrations predictable for AI assistants.

Key characteristics:

- **Safety first** – read-only interactions with enforced timeouts and record limits.
- **LLM-friendly outputs** – responses formatted for natural-language assistants and autonomous agents.
- **Minimal dependencies** – lightweight Python stack keeps deployment straightforward.

## Included Server

| Server                           | Description                                                                                                                                                                                    | Deployment Options                                         |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `servers/boston_opendata_lambda` | Exposes Boston's CKAN portal (`https://data.boston.gov`) through MCP tools for dataset discovery and DataStore queries. Uses MCPEngine for HTTP-based communication and AWS Lambda deployment. | **AWS Lambda (production)**, Local testing via HTTP server |

### Available Tools

The Boston OpenData MCP server provides five tools:

1. **`search_datasets`** - Search for datasets using keywords (e.g., "311", "crime", "parking")
2. **`list_all_datasets`** - List all available datasets on the portal
3. **`get_dataset_info`** - Get detailed metadata and resources for a specific dataset
4. **`query_datastore`** - Query actual data records from DataStore resources with filtering, sorting, and pagination
5. **`get_datastore_schema`** - Get schema information (field names and data types) for DataStore resources

## Running Locally (Testing)

The server can be run locally for testing using the HTTP server mode:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the local HTTP server
python -m servers.boston_opendata_lambda.lambda_server
```

The server will start on `http://localhost:8000`. For connecting to Claude Desktop, use the MCPEngine proxy:

```bash
# In a separate terminal, start the proxy
mcpengine proxy boston-opendata-lambda http://localhost:8000/mcp --mode http --claude
```

**Notes:**

- Python 3.10+ is required
- Install MCPEngine: `pip install mcpengine`
- See [`servers/boston_opendata_lambda/README.md`](servers/boston_opendata_lambda/README.md) for detailed local testing instructions

## Deployment Options

### Local Development

The server can run locally using HTTP mode for testing and development. See the [Running Locally](#running-locally-testing) section above.

### AWS Lambda Deployment (Production)

The **Boston OpenData MCP server** includes a production-ready Lambda deployment option using [MCPEngine](https://www.featureform.com/post/deploy-mcp-on-aws-lambda-with-mcpengine):

- **Location**: `servers/boston_opendata_lambda/`
- **Infrastructure**: Fully automated Terraform scripts for AWS resources
- **Features**: HTTP-based, stateless, scalable, with built-in monitoring
- **Production URL**: `https://kdbjj7ebdewlcy24bt4wbf3uju0tjgdf.lambda-url.us-east-1.on.aws`
- **Documentation**: See [`docs/LAMBDA_DEPLOYMENT.md`](docs/LAMBDA_DEPLOYMENT.md) and [`docs/LAMBDA_QUICKSTART.md`](docs/LAMBDA_QUICKSTART.md)

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

### Production (Lambda Deployment)

Connect to the deployed Lambda server using MCPEngine proxy:

```bash
mcpengine proxy boston-opendata-lambda https://kdbjj7ebdewlcy24bt4wbf3uju0tjgdf.lambda-url.us-east-1.on.aws --mode http --claude
```

**Note:** Docker Desktop must be running for the proxy to work. See [`docs/LAMBDA_QUICKSTART.md`](docs/LAMBDA_QUICKSTART.md) for detailed setup instructions.

### Local Development

For local testing, run the server and proxy in separate terminals:

**Terminal 1:**

```bash
python -m servers.boston_opendata_lambda.lambda_server
```

**Terminal 2:**

```bash
mcpengine proxy boston-opendata-lambda http://localhost:8000/mcp --mode http --claude
```

After starting the proxy, restart Claude Desktop and ask it to list available tools. You should see the five Boston OpenData tools available.

## Repository Structure

```
servers/                      # MCP server package
  boston_opendata_lambda/     # Boston Open Data MCP server (Lambda/production)
    terraform/                 # Infrastructure as Code for AWS deployment
      main.tf                  # Terraform configuration (ECR, Lambda, IAM, etc.)
      variables.tf             # Input variables
      outputs.tf               # Deployment outputs
      AWS_PERMISSIONS.md       # Required AWS IAM permissions
      README.md                # Terraform deployment guide
    lambda_server.py          # MCPEngine-based Lambda handler and local HTTP server
    ckan.py                   # CKAN API client with retry logic and error handling
    config.py                 # Configuration management (Pydantic settings)
    Dockerfile                # Container image definition
    build.sh                  # Build script for Docker image
    utils/                    # Utility modules
      circuit_breaker.py      # Circuit breaker implementation
      exceptions.py           # Custom exception types
      formatters.py           # Response formatting utilities
      logger.py               # Structured logging setup
      rate_limiter.py         # Rate limiting implementation
      validators.py           # Input validation helpers
    tests/                    # Test suite
      test_date_range.py      # Date range filtering tests
      test_local.py           # Local server tests
    README.md                 # Server-specific documentation
    QUICKSTART.md             # Quick start guide for this server
docs/                         # Project documentation
  QUICKSTART.md              # Quick start guide (legacy)
  LAMBDA_QUICKSTART.md       # Lambda connection quick start
  LAMBDA_DEPLOYMENT.md       # Lambda deployment guide
  DEVELOPMENT.md             # Development notes
requirements.txt             # Python dependencies
pyproject.toml               # Project metadata and dependencies
LICENSE                      # Project license (MIT)
CONTRIBUTORS.md              # Acknowledgements and contribution guidelines
```

## Documentation

### Getting Started

- **Quick Start (Lambda):** [`docs/LAMBDA_QUICKSTART.md`](docs/LAMBDA_QUICKSTART.md) – Connect Claude Desktop to the deployed Lambda server in minutes
- **Server Documentation:** [`servers/boston_opendata_lambda/README.md`](servers/boston_opendata_lambda/README.md) – Detailed server documentation and local testing guide

### Deployment & Development

- **Lambda Deployment Guide:** [`docs/LAMBDA_DEPLOYMENT.md`](docs/LAMBDA_DEPLOYMENT.md) – Complete guide for Lambda deployment and local development
- **Terraform Infrastructure:** [`servers/boston_opendata_lambda/terraform/README.md`](servers/boston_opendata_lambda/terraform/README.md) – Step-by-step AWS infrastructure deployment
- **AWS Permissions:** [`servers/boston_opendata_lambda/terraform/AWS_PERMISSIONS.md`](servers/boston_opendata_lambda/terraform/AWS_PERMISSIONS.md) – Required IAM permissions for Terraform deployment

### Additional Resources

- **Development Notes:** [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) – Architecture, design decisions, and roadmap

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
