# Use the official AWS Lambda Python runtime
FROM public.ecr.aws/lambda/python:3.12

# Set working directory in the container
WORKDIR /var/task

# Copy requirements first for better caching
COPY requirements.txt .


# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ["servers.boston_opendata_lambda.lambda_server.handler"]
