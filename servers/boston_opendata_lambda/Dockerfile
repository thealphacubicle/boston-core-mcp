# Use the official AWS Lambda Python runtime
# Supports both ARM64 (Graviton2) and AMD64 architectures
# The platform will be specified during docker build with --platform flag
FROM public.ecr.aws/lambda/python:3.12

# Set working directory in the container
WORKDIR /var/task

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set the CMD to your handler
# Format: module.path.to.handler_function
# The Lambda runtime will import the module and call the handler function
CMD ["servers.boston_opendata_lambda.lambda_server.handler"]
