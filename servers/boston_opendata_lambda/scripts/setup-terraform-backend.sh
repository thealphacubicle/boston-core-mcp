#!/bin/bash

# Script to set up S3 bucket for Terraform state storage
# This script is idempotent - safe to run multiple times

set -e  # Exit on error

# Configuration
BUCKET_NAME="boston-mcp-tf-state-dev"
REGION="us-east-1"
MAX_RETRIES=5
RETRY_DELAY=10  # seconds (increased initial delay)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to create bucket with retry logic
create_bucket_with_retry() {
    local retry_count=0
    local current_delay=$RETRY_DELAY
    local success=false
    local error_output=""
    local exit_code=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        # Try to create the bucket and capture both output and exit code
        if [ "$REGION" = "us-east-1" ]; then
            error_output=$(aws s3api create-bucket \
                --bucket "$BUCKET_NAME" \
                --region "$REGION" 2>&1) || exit_code=$?
        else
            error_output=$(aws s3api create-bucket \
                --bucket "$BUCKET_NAME" \
                --region "$REGION" \
                --create-bucket-configuration LocationConstraint="$REGION" 2>&1) || exit_code=$?
        fi
        
        # Check if the command succeeded (exit code 0)
        if [ $exit_code -eq 0 ]; then
            success=true
            break
        fi
        
        # Check if error is OperationAborted (conflicting operation)
        if echo "$error_output" | grep -q "OperationAborted"; then
            # Check if bucket was actually created (sometimes AWS returns this error even on success)
            if aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
                print_info "Bucket was created successfully (despite OperationAborted error)."
                success=true
                break
            fi
            
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $MAX_RETRIES ]; then
                print_warning "Bucket creation in progress or conflicting operation detected. Waiting ${current_delay}s before retry ($retry_count/$MAX_RETRIES)..."
                sleep $current_delay
                current_delay=$((current_delay * 2))  # Exponential backoff
            fi
            exit_code=0  # Reset exit code for next iteration
        else
            # Different error, exit
            print_error "Failed to create bucket: $error_output"
            return 1
        fi
    done
    
    if [ "$success" = false ]; then
        print_error "Failed to create bucket after $MAX_RETRIES attempts."
        echo ""
        print_info "This usually means AWS is still processing a previous operation."
        echo ""
        print_info "Options to resolve:"
        echo "  1. Wait 2-5 minutes and run the script again (recommended)"
        echo "  2. Check if the bucket exists:"
        echo "     aws s3api head-bucket --bucket $BUCKET_NAME --region $REGION"
        echo ""
        print_info "If the bucket exists, you can skip creation and just configure it:"
        echo "  The script will automatically detect and configure an existing bucket."
        echo ""
        print_info "To manually create the bucket (if needed):"
        echo "  aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION"
        return 1
    fi
    
    return 0
}

# Check if AWS CLI is installed
print_info "Checking for AWS CLI..."
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first:"
    echo "  https://aws.amazon.com/cli/"
    exit 1
fi
print_info "AWS CLI found: $(aws --version)"

# Verify AWS credentials are configured
print_info "Verifying AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials are not configured or invalid."
    echo "Please configure your credentials using one of:"
    echo "  - aws configure"
    echo "  - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)"
    echo "  - IAM role (if running on EC2)"
    exit 1
fi

# Get AWS account ID for verification
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_info "AWS credentials verified. Account ID: $AWS_ACCOUNT_ID"
print_info "Target region: $REGION"

# Check if bucket already exists
print_info "Checking if bucket '$BUCKET_NAME' already exists..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
    print_warning "Bucket '$BUCKET_NAME' already exists. Verifying configuration..."
    
    # Verify versioning is enabled
    VERSIONING_STATUS=$(aws s3api get-bucket-versioning --bucket "$BUCKET_NAME" --region "$REGION" --query 'Status' --output text 2>/dev/null || echo "None")
    if [ "$VERSIONING_STATUS" != "Enabled" ]; then
        print_info "Enabling versioning on existing bucket..."
        aws s3api put-bucket-versioning \
            --bucket "$BUCKET_NAME" \
            --versioning-configuration Status=Enabled \
            --region "$REGION"
        print_info "Versioning enabled."
    else
        print_info "Versioning is already enabled."
    fi
    
    # Verify encryption is enabled
    ENCRYPTION_STATUS=$(aws s3api get-bucket-encryption --bucket "$BUCKET_NAME" --region "$REGION" --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' --output text 2>/dev/null || echo "None")
    if [ "$ENCRYPTION_STATUS" != "AES256" ]; then
        print_info "Enabling server-side encryption (AES256) on existing bucket..."
        aws s3api put-bucket-encryption \
            --bucket "$BUCKET_NAME" \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }' \
            --region "$REGION"
        print_info "Server-side encryption enabled."
    else
        print_info "Server-side encryption (AES256) is already enabled."
    fi
    
    # Verify public access is blocked
    print_info "Verifying public access block settings..."
    PUBLIC_ACCESS_BLOCK=$(aws s3api get-public-access-block --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null || echo "NotConfigured")
    if [ "$PUBLIC_ACCESS_BLOCK" = "NotConfigured" ]; then
        print_info "Blocking public access on existing bucket..."
        aws s3api put-public-access-block \
            --bucket "$BUCKET_NAME" \
            --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
            --region "$REGION"
        print_info "Public access blocked."
    else
        print_info "Public access is already blocked."
    fi
    
    print_info "Bucket '$BUCKET_NAME' is configured correctly!"
else
    print_info "Bucket '$BUCKET_NAME' does not exist. Creating it..."
    
    # Create the bucket with retry logic
    if create_bucket_with_retry; then
        print_info "Bucket created successfully!"
    else
        exit 1
    fi
    
    # Enable versioning
    print_info "Enabling versioning..."
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled \
        --region "$REGION"
    print_info "Versioning enabled."
    
    # Enable server-side encryption
    print_info "Enabling server-side encryption (AES256)..."
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }' \
        --region "$REGION"
    print_info "Server-side encryption enabled."
    
    # Block public access
    print_info "Blocking public access..."
    aws s3api put-public-access-block \
        --bucket "$BUCKET_NAME" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
        --region "$REGION"
    print_info "Public access blocked."
fi

# Verify the setup
print_info "Verifying bucket configuration..."
echo ""
echo "Bucket Details:"
echo "  Name: $BUCKET_NAME"
echo "  Region: $REGION"
echo "  Versioning: $(aws s3api get-bucket-versioning --bucket "$BUCKET_NAME" --region "$REGION" --query 'Status' --output text 2>/dev/null || echo 'Not Enabled')"
echo "  Encryption: $(aws s3api get-bucket-encryption --bucket "$BUCKET_NAME" --region "$REGION" --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' --output text 2>/dev/null || echo 'Not Configured')"
echo ""

# Success message
print_info "✓ S3 bucket setup completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Update your Terraform backend configuration to use this bucket"
echo "  2. Run 'terraform init' to initialize the backend"
echo "  3. The backend configuration should reference:"
echo "     - bucket: $BUCKET_NAME"
echo "     - key: terraform.tfstate (or your preferred state file path)"
echo "     - region: $REGION"
echo ""
