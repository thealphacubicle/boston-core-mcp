# CI/CD Pipeline Guide

This guide explains the GitHub Actions CI/CD workflows for the Boston Core MCP project, focusing on production Terraform deployments.

## Overview

The project uses two main workflows:

1. **CI Workflow** (`ci.yml`) - Runs on PRs and feature branch pushes for validation
2. **Production Deployment** (`deploy-production.yml`) - Deploys infrastructure to AWS when code is merged to `main`

## Workflow Details

### CI Workflow (`.github/workflows/ci.yml`)

**Triggers:**

- Pull requests targeting `main` branch
- Pushes to `feature/*` branches

**Jobs:**

1. **`code-quality`**

   - Runs Python syntax checks
   - Validates code formatting with `black` (non-blocking)
   - Installs dependencies

2. **`terraform-validate`**

   - Validates Terraform syntax and configuration
   - Runs `terraform init -backend=false` and `terraform validate`
   - Working directory: `servers/boston_opendata_lambda/terraform`

3. **`terraform-plan`** (PRs only)
   - Generates Terraform execution plan
   - Uses `production` environment for AWS credentials
   - Posts plan output as a collapsible comment on the PR
   - Plan is saved to `plan_output.txt` for review

**Key Features:**

- Terraform plan comments are automatically posted to PRs
- Uses GitHub Environment `production` for AWS authentication
- Plan output is formatted in collapsible markdown for easy review

### Production Deployment (`.github/workflows/deploy-production.yml`)

**Triggers:**

- Push to `main` branch

**Concurrency:**

- Group: `terraform-production-deploy`
- `cancel-in-progress: false` - Ensures only one deployment runs at a time

**Jobs:**

1. **`lint-validate`**

   - Runs code quality checks (Python syntax, formatting)
   - Validates Terraform configuration
   - Must pass before proceeding to plan/apply

2. **`terraform-plan`**

   - Environment: `production` (uses AWS credentials from environment secrets)
   - Generates Terraform execution plan
   - Saves plan as artifact `tfplan` for use in apply job
   - Artifact retention: 1 day

3. **`terraform-apply`**
   - Environment: `production` (requires manual approval)
   - Downloads the plan artifact from previous job
   - Applies the Terraform plan
   - Captures and displays outputs:
     - `function_url` - Lambda Function URL endpoint
     - `lambda_function_name` - Name of the Lambda function
     - `ecr_repository_url` - ECR repository URL

**Deployment Flow:**

```
Push to main
  ↓
lint-validate (code quality + terraform validation)
  ↓
terraform-plan (generate plan, save as artifact)
  ↓
terraform-apply ⏸️ (manual approval required)
  ↓
✅ Deployment complete (outputs displayed)
```

## Setup Requirements

### GitHub Environment: `production`

**Required Secrets:**

- `AWS_ACCESS_KEY_ID` - AWS access key for Terraform operations
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (optional, defaults to `us-east-1`)

**Protection Rules:**

- **Required reviewers**: At least 1 reviewer must approve before `terraform-apply` runs
- **Deployment branches**: Only `main` branch can trigger deployments
- **Wait timer**: Optional delay before deployment (recommended: 0 minutes)

**Setup Steps:**

1. Go to repository Settings → Environments
2. Create new environment named `production`
3. Add required secrets:
   ```bash
   AWS_ACCESS_KEY_ID=<your-access-key>
   AWS_SECRET_ACCESS_KEY=<your-secret-key>
   AWS_REGION=us-east-1  # Optional
   ```
4. Configure protection rules:
   - Enable "Required reviewers" (add at least 1 reviewer)
   - Set "Deployment branches" to "Selected branches" → `main` only

### Terraform Backend

The Terraform configuration uses an S3 backend:

- **Bucket**: `boston-mcp-tf-state-prod`
- **Key**: `terraform.tfstate`
- **Region**: `us-east-1`

Ensure the AWS credentials have permissions to:

- Read/write to the S3 bucket
- Manage Lambda, ECR, IAM, CloudWatch resources
- Access ECR for Docker image pushes

## How to Use

### Making Changes

1. **Create a feature branch:**

   ```bash
   git checkout -b feature/my-changes
   ```

2. **Make your changes** to Terraform files or application code

3. **Push to trigger CI:**

   ```bash
   git push origin feature/my-changes
   ```

   - CI workflow runs: code-quality → terraform-validate

4. **Create a Pull Request** targeting `main`

   - CI workflow runs: code-quality → terraform-validate → terraform-plan
   - Terraform plan is posted as a PR comment
   - Review the plan output in the PR

5. **After PR approval and merge:**
   - Production deployment workflow automatically triggers
   - `lint-validate` runs first
   - `terraform-plan` generates the execution plan
   - `terraform-apply` waits for manual approval
   - **Approve the deployment** in the GitHub Actions UI
   - Deployment proceeds and outputs are displayed

### Reviewing Terraform Plans

**In PR Comments:**

- Plans are posted automatically as collapsible markdown
- Click "Show Plan" to expand and review changes
- Plans show what resources will be created, modified, or destroyed

**Before Merging:**

- Always review the plan output in the PR comment
- Verify no unexpected changes
- Check resource counts and types

### Approving Production Deployments

1. Go to the Actions tab in GitHub
2. Find the running workflow for your commit
3. Click on the `terraform-apply` job
4. Review the plan output (shown in job logs)
5. Click "Review deployments" button
6. Select "Approve and deploy" or "Reject"

**Important:** Only approved reviewers can approve deployments. The deployment will not proceed without approval.

## Workflow Outputs

After a successful deployment, the workflow displays:

- **Lambda Function URL**: Public endpoint for the Lambda function
- **Lambda Function Name**: Name of the deployed function
- **ECR Repository URL**: Docker image repository URL

These outputs are shown in:

- GitHub Actions job summary
- Workflow run logs

## Troubleshooting

### CI Workflow Issues

**Problem: `terraform-plan` fails with AWS authentication error**

- **Solution**: Verify `production` environment secrets are configured correctly
- Check that `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set
- Ensure AWS credentials have necessary permissions

**Problem: PR comment not appearing**

- **Solution**: Verify `pull-requests: write` permission is set in workflow
- Check GitHub Actions logs for errors in the "Comment PR" step
- Ensure the workflow has access to the repository

**Problem: Terraform validation fails**

- **Solution**: Run `terraform validate` locally to identify syntax errors
- Check Terraform version compatibility (requires >= 1.0)
- Verify all required variables are defined

### Deployment Workflow Issues

**Problem: Manual approval not showing**

- **Solution**:
  - Verify `production` environment protection rules are enabled
  - Check that required reviewers are configured
  - Ensure you're viewing the correct workflow run

**Problem: `terraform-apply` fails**

- **Solution**:
  - Review the plan output in the `terraform-plan` job logs
  - Check AWS permissions for the credentials
  - Verify Terraform state is accessible (S3 backend)
  - Check for resource conflicts or quota limits

**Problem: Plan artifact not found**

- **Solution**:
  - Ensure `terraform-plan` job completed successfully
  - Check artifact upload step in plan job logs
  - Verify artifact name matches (`tfplan`)

**Problem: Docker build fails during Terraform apply**

- **Solution**:
  - Terraform automatically builds Docker images via `null_resource`
  - Check AWS ECR permissions
  - Verify Dockerfile exists and is valid
  - Check AWS region matches ECR repository region

### Common AWS Permission Issues

The AWS credentials need permissions for:

- **S3**: Read/write to `boston-mcp-tf-state-prod` bucket
- **Lambda**: Create, update, delete functions and function URLs
- **ECR**: Create repositories, push/pull images
- **IAM**: Create roles and policies for Lambda execution
- **CloudWatch**: Create log groups

**IAM Policy Example:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "lambda:*",
        "ecr:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutRolePolicy",
        "logs:CreateLogGroup",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

## Best Practices

1. **Always review Terraform plans** before merging PRs
2. **Test changes locally** before pushing:
   ```bash
   cd servers/boston_opendata_lambda/terraform
   terraform init -backend=false
   terraform validate
   terraform plan
   ```
3. **Use feature branches** for all changes
4. **Keep PRs focused** - one logical change per PR
5. **Monitor deployments** - Check outputs after successful deployment
6. **Review AWS costs** - Terraform creates real AWS resources

## Local Testing

Before pushing changes, test locally:

```bash
# Python checks
python -m compileall -q servers/
black --check --diff servers/

# Terraform validation
cd servers/boston_opendata_lambda/terraform
terraform init -backend=false
terraform validate
terraform plan  # Review plan locally
```

## Workflow Dependencies

- **Terraform**: Version 1.0.0 (configured in workflows)
- **Python**: Version 3.10
- **AWS CLI**: Available in GitHub Actions runners
- **Docker**: Available in GitHub Actions runners (for Terraform Docker builds)

## Related Documentation

- [Lambda Deployment Guide](./LAMBDA_DEPLOYMENT.md) - Detailed Lambda deployment instructions
- [Terraform README](../servers/boston_opendata_lambda/terraform/README.md) - Terraform-specific documentation
- [Workflows Quick Reference](../.github/workflows/README.md) - Quick workflow reference

## Support

For issues or questions:

1. Check workflow logs in GitHub Actions
2. Review Terraform plan outputs
3. Verify AWS credentials and permissions
4. Consult Terraform documentation for specific errors
