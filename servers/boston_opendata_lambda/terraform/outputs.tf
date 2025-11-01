output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.boston_opendata_mcp.repository_url
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.boston_opendata_mcp.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.boston_opendata_mcp.arn
}

output "function_url" {
  description = "Lambda Function URL endpoint"
  value       = aws_lambda_function_url.boston_opendata_mcp.function_url
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "aws_region" {
  description = "AWS region used for deployment"
  value       = var.aws_region
}

# Output for easy deployment commands
output "deployment_commands" {
  description = "Commands to build and deploy the Docker image"
  value = {
    login_ecr = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.boston_opendata_mcp.repository_url}"
    build_image = "docker build --platform=linux/${var.lambda_architecture == "arm64" ? "arm64" : "amd64"} --provenance=false -t ${var.ecr_repository_name}:latest -f servers/boston_opendata_lambda/Dockerfile ."
    tag_image = "docker tag ${var.ecr_repository_name}:latest ${aws_ecr_repository.boston_opendata_mcp.repository_url}:latest"
    push_image = "docker push ${aws_ecr_repository.boston_opendata_mcp.repository_url}:latest"
    update_function = "aws lambda update-function-code --function-name ${aws_lambda_function.boston_opendata_mcp.function_name} --image-uri ${aws_ecr_repository.boston_opendata_mcp.repository_url}:latest"
  }
}

