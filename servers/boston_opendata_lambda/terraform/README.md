# Terraform Deployment for Boston OpenData MCP Lambda Server

This directory contains Terraform configuration files to deploy the Boston OpenData MCP server to AWS Lambda.

## Overview

Terraform automates the entire deployment process in a single command:

- **ECR Repository**: Stores Docker container images
- **Docker Build & Push**: Automatically builds and pushes your Docker image (no manual steps!)
- **Lambda Function**: Runs your serverless code
- **IAM Role**: Permissions for Lambda to execute and log
- **Function URL**: HTTPS endpoint to access the server
- **CloudWatch Logs**: Automatic logging for debugging

**One `terraform apply` does it all!** The Docker image is automatically built and pushed before the Lambda function is created.

## Prerequisites

Before you begin, ensure you have:

1. **AWS Account** with appropriate permissions

   - Ability to create ECR repositories
   - Ability to create Lambda functions
   - Ability to create IAM roles
   - Ability to create CloudWatch log groups

2. **AWS CLI** installed and configured

   ```bash
   # Install AWS CLI (if not already installed)
   # macOS: brew install awscli
   # Linux: sudo apt-get install awscli
   # Or download from: https://aws.amazon.com/cli/

   # Configure with your credentials
   aws configure
   # Enter your Access Key ID
   # Enter your Secret Access Key
   # Enter your preferred region (e.g., us-east-1)
   # Enter default output format: json
   ```

3. **Terraform** installed (version >= 1.0)

   ```bash
   # macOS
   brew install terraform

   # Or download from: https://www.terraform.io/downloads
   ```

4. **Docker** installed and running (required for automated builds)

   ```bash
   # Verify Docker is installed and running
   docker ps
   
   # Docker is used automatically by Terraform to build and push images
   # No manual Docker commands needed!
   ```

5. **Verify AWS Access**
   ```bash
   aws sts get-caller-identity
   # Should show your AWS account ID and user
   ```

## Quick Start

### Step 1: Configure Variables

Copy the example variables file and customize it:

```bash
cd servers/boston_opendata_lambda/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your preferences:

- Change `aws_region` if you want a different region
- Adjust `lambda_function_name` if you want a different name
- Add environment variables if needed
- Update tags with your information

### Step 2: Initialize Terraform

Download the AWS provider:

```bash
terraform init
```

Expected output:

```
Initializing provider plugins...
Terraform has been successfully initialized!
```

### Step 3: Review the Plan

See what Terraform will create (without creating anything yet):

```bash
terraform plan
```

Review the output:

- Should show resources being created (ECR, Lambda, IAM, etc.)
- Check the region and resource names are correct
- Look for any warnings

### Step 4: Deploy Everything (One Command!)

Deploy all resources including automatic Docker build and push:

```bash
terraform apply
```

Terraform will:

1. Show you the plan
2. Ask: "Do you want to perform these actions?"
3. Type `yes` and press Enter
4. Create ECR repository
5. **Automatically build and push Docker image** (this takes 2-5 minutes)
6. Create Lambda function with the image
7. Create Function URL
8. Set up IAM roles and CloudWatch logs

**Note**: The first `terraform apply` will take 2-5 minutes because it builds the Docker image. Subsequent applies are faster unless source code changes.

**Save the outputs!** Terraform will show:

- `ecr_repository_url` - Your ECR repository URL
- `lambda_function_name` - Name of your Lambda function
- `function_url` - Your HTTPS endpoint (ready to use!)

### Step 5: Get Function URL

```bash
cd servers/boston_opendata_lambda/terraform
terraform output function_url
```

You should see something like:

```
https://abc123xyz.lambda-url.us-east-1.on.aws/
```

### Step 6: Test the Deployment

```bash
# Get your Function URL
FUNCTION_URL=$(terraform output -raw function_url)
echo "Function URL: $FUNCTION_URL"

# Test the endpoint (should return "Not Found" - this is normal for MCP endpoints)
curl $FUNCTION_URL

# Check CloudWatch logs
aws logs tail /aws/lambda/boston-opendata-mcp --follow
```

### Step 7: Connect from Claude Desktop

Use MCPEngine proxy to connect:

```bash
# Get the function URL first
FUNCTION_URL=$(cd servers/boston_opendata_lambda/terraform && terraform output -raw function_url)

# Start the proxy
mcpengine proxy boston-opendata-lambda $FUNCTION_URL --mode http --claude
```

Then open Claude Desktop - your tools should be available!

## File Structure

```
terraform/
├── main.tf                      # Main infrastructure definitions
├── variables.tf                 # Input variables (what you can customize)
├── outputs.tf                  # What Terraform shows after creation
├── terraform.tfvars.example    # Template for your configuration
├── terraform.tfvars            # YOUR configuration (not in git)
└── README.md                   # This file
```

## Manual Deployment (Alternative to Quick Start)

If you prefer step-by-step manual control:

### 1. Configure

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
```

### 2. Initialize

```bash
terraform init
```

### 3. Plan

```bash
terraform plan
# Review what will be created
```

### 4. Apply

```bash
terraform apply
# Type 'yes' when prompted
```

### 5. Get Outputs

```bash
terraform output
# Shows: ecr_repository_url, lambda_function_name, function_url
```

**Note**: The Docker image is automatically built and pushed during `terraform apply`. No manual steps needed!

## Updating After Code Changes

When you make changes to your Python code:

1. **Run `terraform apply`** - Terraform automatically detects code changes and rebuilds the Docker image
   
   ```bash
   terraform apply
   ```
   
   The Docker image will be rebuilt if any of these files change:
   - `Dockerfile`
   - `lambda_server.py`
   - `requirements.txt`

2. **That's it!** Terraform automatically:
   - Rebuilds the Docker image
   - Pushes it to ECR
   - Updates the Lambda function with the new image

You do NOT need to manually build or push Docker images anymore.

### Updating Infrastructure (Timeout, Memory, Environment Variables)

If you change infrastructure settings in `terraform.tfvars`:

```bash
terraform plan    # See what will change
terraform apply   # Apply the changes
```

**Note**: Changing infrastructure settings (timeout, memory, environment variables) will NOT trigger a Docker rebuild unless source files also changed.

## Configuration Options

### Lambda Settings

In `terraform.tfvars`:

- `lambda_timeout`: Maximum execution time (seconds)
- `lambda_memory_size`: Memory allocation (MB)
- `lambda_architecture`: `arm64` (cheaper, recommended) or `x86_64`

### Environment Variables

Add application settings:

```hcl
lambda_environment_variables = {
  BOSTON_OPENDATA_ENVIRONMENT = "production"
  BOSTON_OPENDATA_LOG_LEVEL   = "INFO"
  BOSTON_OPENDATA_LOG_FORMAT  = "json"
}
```

See `servers/boston_opendata_lambda/config.py` for all available environment variables.

### Function URL Authentication

By default, Function URL is public (`auth_type = "NONE"`).

For production, consider:

```hcl
function_url_auth_type = "AWS_IAM"
```

This requires AWS IAM authentication for all requests.

### CORS Configuration

Adjust if you need specific origins:

```hcl
function_url_cors_origins = ["https://yourdomain.com"]
function_url_cors_methods = ["GET", "POST", "OPTIONS"]
function_url_cors_headers = ["Content-Type", "Authorization"]
```

## Viewing Logs

### CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/boston-opendata-mcp --follow

# View recent logs
aws logs tail /aws/lambda/boston-opendata-mcp

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/boston-opendata-mcp \
  --filter-pattern "ERROR"
```

Or view in AWS Console:

1. Go to CloudWatch → Log groups
2. Find `/aws/lambda/boston-opendata-mcp`
3. Click on a log stream

## Troubleshooting

### Terraform Errors

**Error: "No valid credential sources found"**

- Run `aws configure` to set up credentials
- Verify with `aws sts get-caller-identity`

**Error: "Access Denied"**

- Check IAM permissions
- Ensure you can create Lambda, ECR, IAM resources

**Error: "Resource already exists"**

- Check if resources were partially created
- Use `terraform import` or delete manually in AWS Console

### Docker Build Errors

**Error: "Cannot connect to Docker daemon"**

- Start Docker Desktop
- Verify with `docker ps`
- Terraform's automated build requires Docker to be running

**Error: "platform linux/arm64 not supported"**

- Change architecture in `terraform.tfvars`: `lambda_architecture = "x86_64"`
- Re-run `terraform apply`
- Terraform will automatically use the correct platform

**Error: "failed to build: resolve : lstat servers: no such file or directory"**

- Ensure you're running `terraform apply` from the `terraform/` directory
- The build script needs to find the project root relative to the terraform directory

### Lambda Function Errors

**Function URL returns error**

- Check CloudWatch logs for details
- Verify Docker image was built and pushed (check Terraform output during apply)
- The image is automatically built/pushed during `terraform apply`, so if it succeeded, the image should be available

**Error: "Source image does not exist"**

- This shouldn't happen with automated builds
- If it occurs, re-run `terraform apply` - it will rebuild and push the image

**Timeout errors**

- Increase `lambda_timeout` in terraform.tfvars
- Re-run `terraform apply`

**Out of memory errors**

- Increase `lambda_memory_size` in terraform.tfvars
- Re-run `terraform apply`

### MCPEngine Proxy Errors

**Cannot connect to Function URL**

- Verify Function URL is correct (from `terraform output`)
- Check Function URL is enabled (should be automatic)
- Test with `curl` first

**Tools not appearing in Claude Desktop**

- Ensure proxy is running
- Restart Claude Desktop
- Check proxy terminal for errors

## Cleanup (Destroying Resources)

⚠️ **Warning**: This permanently deletes all resources!

To remove everything:

```bash
terraform destroy
```

This will:

- Delete the Lambda function
- Delete the ECR repository (and all images)
- Delete the Function URL
- Delete CloudWatch log groups
- Delete IAM role and policies

Type `yes` when prompted. This action cannot be undone.

## Cost Considerations

### Expected Monthly Costs

For typical usage (moderate traffic):

- **Lambda**: ~$1-5/month

  - First 1M requests free
  - $0.20 per 1M requests after
  - Compute: $0.0000166667 per GB-second (ARM64 is cheaper)

- **ECR Storage**: ~$0.50-1/month

  - First 500MB free
  - $0.10 per GB/month after
  - One image is typically 200-500MB

- **CloudWatch Logs**: ~$0.50-2/month

  - First 5GB free
  - $0.50 per GB/month after

- **Function URL**: Included with Lambda (free)

**Total: Typically $2-8/month** for moderate usage

### Cost Optimization Tips

1. **Use ARM64 architecture** (Graviton2)

   - 20% cheaper than x86_64
   - Better performance for most workloads

2. **Reduce log retention**

   - Change `log_retention_days` to 7 instead of 14
   - Saves CloudWatch costs

3. **Optimize memory/timeout**

   - Right-size memory for your workload
   - Lower timeout if requests complete faster

4. **ECR lifecycle policy**
   - Already configured to keep only last 10 images
   - Prevents storage bloat

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [MCPEngine Documentation](https://www.featureform.com/post/deploy-mcp-on-aws-lambda-with-mcpengine)

## Getting Help

1. Check CloudWatch logs for error messages
2. Review Terraform plan output for configuration issues
3. Verify AWS permissions and credentials
4. Test with `curl` before using MCPEngine proxy

## Next Steps

After successful deployment:

- Monitor CloudWatch logs
- Set up CloudWatch alarms for errors
- Consider adding authentication (AWS_IAM) for production
- Document your Function URL for team members
