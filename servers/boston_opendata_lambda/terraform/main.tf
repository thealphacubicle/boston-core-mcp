terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data source for current AWS account and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ECR Repository for storing Docker images
resource "aws_ecr_repository" "boston_opendata_mcp" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = var.tags
}

# ECR Lifecycle Policy - keeps only last 10 images to save storage costs
resource "aws_ecr_lifecycle_policy" "boston_opendata_mcp" {
  repository = aws_ecr_repository.boston_opendata_mcp.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Build and push Docker image to ECR
resource "null_resource" "docker_build_and_push" {
  # Wait for ECR repository and lifecycle policy to be created
  depends_on = [
    aws_ecr_repository.boston_opendata_mcp,
    aws_ecr_lifecycle_policy.boston_opendata_mcp
  ]

  # Trigger rebuild when source files change
  triggers = {
    dockerfile_hash     = filemd5("${path.module}/../Dockerfile")
    lambda_server_hash  = filemd5("${path.module}/../lambda_server.py")
    requirements_hash   = filemd5("${path.module}/../../../requirements.txt")
    repository_url      = aws_ecr_repository.boston_opendata_mcp.repository_url
    architecture        = var.lambda_architecture
  }

  # Build and push Docker image
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      REPO_URL="${aws_ecr_repository.boston_opendata_mcp.repository_url}"
      AWS_REGION="${var.aws_region}"
      ARCH="${var.lambda_architecture == "arm64" ? "arm64" : "amd64"}"
      
      echo "Logging into ECR..."
      aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $REPO_URL
      
      echo "Building Docker image for platform linux/$ARCH..."
      cd ${path.module}/../../..
      docker build \
        --platform linux/$ARCH \
        --provenance=false \
        -t ${var.ecr_repository_name}:latest \
        -f servers/boston_opendata_lambda/Dockerfile .
      
      echo "Tagging image for ECR..."
      docker tag ${var.ecr_repository_name}:latest $REPO_URL:latest
      
      echo "Pushing image to ECR..."
      docker push $REPO_URL:latest
      echo "Docker image pushed successfully!"
    EOT
  }
}

# IAM Role for Lambda execution
resource "aws_iam_role" "lambda_execution" {
  name = "${var.lambda_function_name}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Logs permissions (more permissive)
resource "aws_iam_role_policy" "lambda_logs" {
  name = "${var.lambda_function_name}-logs-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.lambda_function_name}:*"
      }
    ]
  })
}

# X-Ray tracing permissions (conditional)
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  count      = var.enable_xray_tracing ? 1 : 0
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Lambda Function
resource "aws_lambda_function" "boston_opendata_mcp" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.boston_opendata_mcp.repository_url}:latest"

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  # Use ARM64 architecture (Graviton2) for cost savings
  architectures = [var.lambda_architecture]

  environment {
    variables = var.lambda_environment_variables
  }

  # Enable X-Ray tracing if needed
  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  tags = var.tags

  depends_on = [
    null_resource.docker_build_and_push,  # Wait for Docker image to be pushed
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_logs,
    aws_iam_role_policy_attachment.lambda_xray
  ]
}

# Lambda Function URL (for HTTP access)
resource "aws_lambda_function_url" "boston_opendata_mcp" {
  function_name      = aws_lambda_function.boston_opendata_mcp.function_name
  authorization_type = var.function_url_auth_type

  cors {
    allow_credentials = false
    allow_origins     = length(var.function_url_cors_origins) == 1 && var.function_url_cors_origins[0] == "*" ? ["*"] : var.function_url_cors_origins
    allow_methods     = ["*"]  # Lambda Function URL requires "*" for all methods or specific list
    allow_headers     = length(var.function_url_cors_headers) == 1 && var.function_url_cors_headers[0] == "*" ? ["*"] : var.function_url_cors_headers
    expose_headers    = []
    max_age           = 86400
  }
}

# Note: Lambda Function URL with authorization_type = "NONE" automatically allows public access
# No separate permission resource is needed (and actually causes errors)

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

