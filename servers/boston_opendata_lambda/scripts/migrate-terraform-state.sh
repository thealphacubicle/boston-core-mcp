#!/bin/bash

# Script to help migrate existing Terraform state to S3 backend
# Run this from the repository root

set -e

TERRAFORM_DIR="servers/boston_opendata_lambda/terraform"

BUCKET_NAME="boston-mcp-tf-state-dev"
STATE_KEY="terraform.tfstate"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Change to repository root (three levels up from scripts/ directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

print_info "Terraform State Migration Guide"
echo ""
print_info "Repository root: $REPO_ROOT"
print_info "Terraform directory: $TERRAFORM_DIR"
echo ""

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed. Please install it first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "$TERRAFORM_DIR" ]; then
    print_error "Terraform directory not found: $TERRAFORM_DIR"
    print_error "Current directory: $(pwd)"
    print_error "Please run this script from the repository root."
    exit 1
fi

cd "$REPO_ROOT/$TERRAFORM_DIR" || cd "$TERRAFORM_DIR"

# Check for local state file
print_step "Checking for existing state files..."
if [ -f "terraform.tfstate" ]; then
    print_warning "Found local state file: terraform.tfstate"
    STATE_SIZE=$(du -h terraform.tfstate | cut -f1)
    print_info "State file size: $STATE_SIZE"
    echo ""
    print_info "You have a local state file. Here's what to do:"
    echo ""
    echo "1. Run: terraform init -backend-config=\"bucket=$BUCKET_NAME\""
    echo "   Terraform will detect the backend change and ask:"
    echo "   'Do you want to copy existing state to the new backend?'"
    echo "   Answer: yes"
    echo ""
    echo "2. Verify the migration:"
    echo "   aws s3 ls s3://$BUCKET_NAME/$STATE_KEY"
    echo ""
    echo "3. After successful migration, you can optionally backup the local state:"
    echo "   cp terraform.tfstate terraform.tfstate.backup"
    echo ""
elif [ -f "terraform.tfstate.backup" ]; then
    print_warning "Found backup state file: terraform.tfstate.backup"
    print_info "You may have already migrated. Checking S3..."
    echo ""
else
    print_info "No local state file found."
    echo ""
fi

# Check if state exists in S3
print_step "Checking S3 backend..."
if aws s3 ls "s3://$BUCKET_NAME/$STATE_KEY" &>/dev/null; then
    print_info "State file already exists in S3!"
    STATE_SIZE=$(aws s3 ls "s3://$BUCKET_NAME/$STATE_KEY" --human-readable --summarize | grep "Total Size" | awk '{print $3, $4}')
    print_info "S3 state file size: $STATE_SIZE"
    echo ""
    print_info "Your state is already in S3. You can proceed with:"
    echo "  terraform init -backend-config=\"bucket=$BUCKET_NAME\""
    echo ""
    print_warning "If you have local changes, Terraform will ask if you want to migrate."
    print_warning "Only answer 'yes' if you want to overwrite the S3 state with your local state."
else
    print_info "No state file found in S3 yet."
    echo ""
    if [ -f "terraform.tfstate" ]; then
        print_info "You need to migrate your local state to S3."
    else
        print_info "No existing state found. Running terraform init will create a new state."
    fi
fi

echo ""
print_step "Next steps:"
echo ""
echo "1. Navigate to Terraform directory:"
echo "   cd servers/boston_opendata_lambda/terraform"
echo ""
echo "2. Initialize Terraform (this will set up the S3 backend):"
echo "   terraform init -backend-config=\"bucket=$BUCKET_NAME\""
echo ""
echo "3. If prompted about migrating state, answer 'yes'"
echo ""
echo "4. Verify your state is in S3:"
echo "   aws s3 ls s3://$BUCKET_NAME/"
echo ""
echo "5. Plan your changes (to see what will change):"
echo "   terraform plan"
echo ""
echo "6. Apply your changes:"
echo "   terraform apply"
echo ""
