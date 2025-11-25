# GitHub Actions Workflows - Quick Reference

## Workflows Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | PRs, feature branch pushes | Code quality checks, Terraform validation, PR plan comments |
| `deploy-production.yml` | Push to `main` | Production infrastructure deployment |

## CI Workflow (`ci.yml`)

**Runs on:** Pull requests and pushes to `main`, `develop`, `feature/*`

**Jobs:**
1. `code-quality` - Python syntax & formatting
2. `terraform-validate` - Terraform syntax validation
3. `terraform-plan` - **PRs only** - Posts plan as PR comment

## Production Deployment (`deploy-production.yml`)

**Runs on:** Push to `main` branch

**Jobs:**
1. `lint-validate` - Code quality + Terraform validation
2. `terraform-plan` - Generate execution plan (saved as artifact)
3. `terraform-apply` - **Requires manual approval** - Deploy to production

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

## Workflow Behavior

```
Feature Branch Push
  └─> CI: code-quality → terraform-validate

Pull Request
  └─> CI: code-quality → terraform-validate → terraform-plan (PR comment)

Merge to Main
  ├─> CI: code-quality → terraform-validate → terraform-plan (PR comment)
  └─> Deploy: lint-validate → terraform-plan → terraform-apply ⏸️ (approval) → ✅ deploy
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Plan job fails | Check AWS credentials in `production` environment |
| PR comment missing | Verify `pull-requests: write` permission |
| Approval not showing | Check `production` environment protection rules |
| Apply fails | Review plan output, check AWS permissions/quotas |

## See Also

- [Full CI/CD Guide](../../docs/CI_CD_GUIDE.md)
- [Lambda Deployment](../../docs/LAMBDA_DEPLOYMENT.md)
