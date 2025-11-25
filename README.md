# Boston Core MCP

**Safe, conversational access to Boston's open data.**

Boston Core MCP is a Model Context Protocol (MCP) server created by the City of Boston Department of Innovation and Technology (DoIT). It gives AI assistants and agentic tools safe, read-only access to Boston's open data portal, enabling staff, residents, and partners to explore civic information through natural conversation.

## Why Boston Core MCP?

### For City Staff

- **Ask questions naturally** - "What datasets do we have about 311 requests?" or "Show me crime data from last month"
- **No technical barriers** - Works directly with Claude Desktop and other MCP-compatible tools
- **Always up-to-date** - Connects directly to Boston's live open data portal
- **Save time** - Get answers instantly without navigating complex data portals

### For Residents & Partners

- **Explore Boston's data** through conversation instead of navigating complex portals
- **Discover datasets** you didn't know existed
- **Get answers quickly** without learning database queries or API syntax
- **Trustworthy source** - Direct connection to official City of Boston data

### For Developers

- **Production-ready** - Deployed on AWS Lambda with automated CI/CD
- **Well-documented** - Comprehensive guides for deployment and development
- **Open source** - MIT licensed, built with modern Python and best practices
- **Extensible** - Easy to adapt for other cities or data sources

## What It Does

Boston Core MCP provides five powerful tools that let AI assistants interact with Boston's open data:

1. **Search Datasets** - Find datasets by keywords (e.g., "311", "crime", "parking")
2. **List All Datasets** - Browse everything available on the portal
3. **Get Dataset Info** - Detailed metadata and resources for any dataset
4. **Query Data** - Get actual data records with filtering, sorting, and pagination
5. **Get Schema** - Understand the structure of any dataset

## Quick Start

### Connect Claude Desktop (2 minutes)

The server is already deployed and ready to use:

```bash
# Install mcpengine
pipx install 'mcpengine[cli]'

# Connect Claude to Boston OpenData
mcpengine proxy boston-opendata-lambda \
  https://kdbjj7ebdewlcy24bt4wbf3uju0tjgdf.lambda-url.us-east-1.on.aws \
  --mode http --claude
```

Then open Claude Desktop and start asking questions about Boston's data!

📖 **Full setup guide**: [docs/LAMBDA_QUICKSTART.md](docs/LAMBDA_QUICKSTART.md)

## Key Features

### Safety First

- **Read-only access** - No modifications to Boston's data
- **Enforced limits** - Timeouts and record limits prevent abuse
- **Input validation** - All queries validated before execution
- **Error handling** - Comprehensive error handling and retry logic

### Production Ready

- **Deployed on AWS Lambda** - Scalable, serverless infrastructure
- **Automated CI/CD** - GitHub Actions for testing and deployment
- **Monitoring** - CloudWatch logs and structured logging
- **Cost-effective** - Typically $2-8/month for moderate usage

### Developer Friendly

- **Well-documented** - Guides for every use case
- **Type-safe** - Built with Python type hints and Pydantic
- **Tested** - Test suite included
- **Modern stack** - Python 3.10+, MCPEngine, Terraform

## Use Cases

### City Staff

- **Policy Research**: "What datasets track housing permits in the last year?"
- **Data Analysis**: "Show me 311 service requests about potholes from this month"
- **Quick Lookups**: "What's the structure of the crime incident reports dataset?"

### Residents

- **Civic Engagement**: "What data is available about public transportation?"
- **Research**: "Find datasets related to city budget and spending"
- **Exploration**: "What open data does Boston publish?"

### Developers & Researchers

- **API Discovery**: "What resources are available in the 311 dataset?"
- **Data Exploration**: "Query the first 100 records from crime incidents"
- **Schema Understanding**: "Show me the schema for parking violations"

## Documentation

### Getting Started

- **[Quick Start Guide](docs/LAMBDA_QUICKSTART.md)** - Connect Claude Desktop in minutes
- **[Local Development](docs/LOCAL_DEVELOPMENT.md)** - Run and develop locally

### Deployment & Operations

- **[Lambda Deployment](docs/LAMBDA_DEPLOYMENT.md)** - Complete deployment guide
- **[Terraform Infrastructure](docs/TERRAFORM_DEPLOYMENT.md)** - Infrastructure as code
- **[CI/CD Pipeline](docs/CI_CD_GUIDE.md)** - Automated testing and deployment
- **[Workflows Reference](docs/WORKFLOWS.md)** - GitHub Actions quick reference

### Architecture & Development

- **[Development Guide](docs/DEVELOPMENT.md)** - Architecture and design decisions

## Technology Stack

- **Python 3.10+** - Modern Python with type hints
- **MCPEngine** - HTTP-based MCP server framework
- **AWS Lambda** - Serverless compute
- **Terraform** - Infrastructure as code
- **GitHub Actions** - CI/CD automation

## Community & Support

This project is maintained by the City of Boston Department of Innovation and Technology (DoIT).

- **Issues**: Open an issue for bugs or feature requests
- **Contributions**: See [CONTRIBUTORS.md](CONTRIBUTORS.md) for guidelines
- **License**: MIT License - see [LICENSE](LICENSE)

## Learn More

- **Boston Open Data Portal**: [data.boston.gov](https://data.boston.gov)
- **Model Context Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **MCPEngine**: [Featureform MCPEngine](https://www.featureform.com/post/deploy-mcp-on-aws-lambda-with-mcpengine)

---

**Built with ❤️ by the City of Boston DoIT team**
