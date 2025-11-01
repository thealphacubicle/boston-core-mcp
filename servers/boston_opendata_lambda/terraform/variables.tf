variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "boston-opendata-mcp"
}

variable "ecr_repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "boston-opendata-mcp"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "lambda_architecture" {
  description = "Lambda function architecture (x86_64 or arm64)"
  type        = string
  default     = "arm64"
  
  validation {
    condition     = contains(["x86_64", "arm64"], var.lambda_architecture)
    error_message = "Lambda architecture must be either 'x86_64' or 'arm64'."
  }
}

variable "function_url_auth_type" {
  description = "Lambda Function URL authorization type (NONE or AWS_IAM)"
  type        = string
  default     = "NONE"
  
  validation {
    condition     = contains(["NONE", "AWS_IAM"], var.function_url_auth_type)
    error_message = "Function URL auth type must be either 'NONE' or 'AWS_IAM'."
  }
}

variable "function_url_cors_origins" {
  description = "CORS allowed origins for Function URL"
  type        = list(string)
  default     = ["*"]
}

variable "function_url_cors_methods" {
  description = "CORS allowed methods for Function URL"
  type        = list(string)
  default     = ["GET", "POST", "OPTIONS"]
}

variable "function_url_cors_headers" {
  description = "CORS allowed headers for Function URL"
  type        = list(string)
  default     = ["*"]
}

variable "lambda_environment_variables" {
  description = "Environment variables for Lambda function"
  type        = map(string)
  default     = {}
}

variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing for Lambda"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "Boston-Core-MCP"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}

