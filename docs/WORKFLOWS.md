# GitHub Actions Workflows - Quick Reference

## Workflows Overview

| Workflow                | Trigger                              | Purpose                                                     |
| ----------------------- | ------------------------------------ | ----------------------------------------------------------- |
| `ci.yml`                | PRs to `main`, pushes to `feature/*` | Code quality checks, Terraform validation, PR plan comments |
| `deploy-production.yml` | Push to `main`                       | Production infrastructure deployment                        |

## CI Workflow (`ci.yml`)

**Runs on:** Pull requests targeting `main`, pushes to `feature/*` branches

**Jobs:**

1. `code-quality` - Python syntax & formatting
2. `terraform-validate` - Terraform syntax validation
3. `terraform-plan` - **PRs only** - Posts plan as PR comment

## Production Deployment (`deploy-production.yml`)

**Runs on:** Push to `main` branch

**Concurrency:** `terraform-production-deploy` (one deployment at a time)

**Jobs:**

1. `lint-validate` - Code quality + Terraform validation
2. `terraform-plan` - Generate execution plan (saved as artifact)
3. `terraform-apply` - **Requires manual approval** - Deploy to production

**Outputs:**

- `function_url` - Lambda Function URL endpoint
- `lambda_function_name` - Lambda function name
- `ecr_repository_url` - ECR repository URL

## Quick Commands

### Test Locally Before Pushing

```bash
# Python checks
python -m compileall -q servers/
black --check --diff servers/

# Terraform validation
cd servers/boston_opendata_lambda/terraform
terraform init -backend=false
terraform validate
terraform plan
```

### Check Workflow Status

```bash
# View recent workflow runs
gh run list

# View specific workflow run
gh run view <run-id>

# Watch workflow in real-time
gh run watch <run-id>
```

## Required Setup

### GitHub Environment: `production`

**Secrets Required:**

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (optional, defaults to `us-east-1`)

**Protection Rules:**

- Required reviewers (at least 1)
- Deployment branches: `main` only

**Setup Location:** Repository Settings → Environments → `production`

## Workflow Behavior

```
Feature Branch Push
  └─> CI: code-quality → terraform-validate

Pull Request (to main)
  └─> CI: code-quality → terraform-validate → terraform-plan (PR comment)

Merge to Main
  ├─> CI: code-quality → terraform-validate → terraform-plan (PR comment)
  └─> Deploy: lint-validate → terraform-plan → terraform-apply ⏸️ (approval) → ✅ deploy
```

## Common Issues

| Issue                   | Solution                                           |
| ----------------------- | -------------------------------------------------- |
| Plan job fails          | Check AWS credentials in `production` environment  |
| PR comment missing      | Verify `pull-requests: write` permission           |
| Approval not showing    | Check `production` environment protection rules    |
| Apply fails             | Review plan output, check AWS permissions/quotas   |
| Plan artifact not found | Ensure `terraform-plan` job completed successfully |

## Workflow Details

### CI Workflow Features

- **Terraform Plan Comments**: Automatically posted to PRs as collapsible markdown
- **Environment**: Uses `production` environment for AWS credentials in plan job
- **Permissions**: `pull-requests: write` for PR comments

### Deployment Workflow Features

- **Concurrency Control**: Only one deployment runs at a time
- **Manual Approval**: `terraform-apply` requires approval from protected reviewers
- **Artifact Passing**: Plan is saved and passed between jobs using GitHub Actions artifacts
- **Output Display**: Deployment outputs shown in job summary and logs

## Terraform Configuration

- **Working Directory**: `servers/boston_opendata_lambda/terraform`
- **Terraform Version**: 1.0.0
- **Backend**: S3 (`boston-mcp-tf-state-prod`)
- **Docker Build**: Handled automatically by Terraform (no extra Docker setup needed)

## See Also

- [Full CI/CD Guide](CI_CD_GUIDE.md) - Comprehensive workflow documentation
- [Lambda Deployment](LAMBDA_DEPLOYMENT.md) - Lambda-specific deployment guide
- [Terraform Deployment](TERRAFORM_DEPLOYMENT.md) - Terraform configuration details
