#!/bin/bash
# Build script for Boston OpenData Lambda Server Docker image
# Compatible with Mac M1 (ARM64) and Intel (AMD64)

set -e

IMAGE_NAME="boston-opendata-mcp"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default to ARM64 (faster on M1 Macs, and Lambda supports Graviton2)
PLATFORM="${PLATFORM:-linux/arm64}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building Boston OpenData Lambda Server Docker image...${NC}"
echo -e "${YELLOW}Platform: ${PLATFORM}${NC}"
echo ""

# Detect if we need to use buildx for cross-platform builds
ARCH=$(uname -m)
NEED_BUILDX=false

if [[ "$PLATFORM" == "linux/amd64" && "$ARCH" == "arm64" ]]; then
    NEED_BUILDX=true
    echo -e "${YELLOW}Cross-platform build detected. Using Docker buildx...${NC}"
    
    # Check if buildx is available
    if ! docker buildx version &> /dev/null; then
        echo -e "${YELLOW}Docker buildx not found. Installing...${NC}"
        # Buildx should be available in Docker Desktop, but just in case
        docker buildx create --use --name multiarch 2>/dev/null || true
    fi
fi

# Navigate to project root for context
cd "$PROJECT_ROOT"

# Build the Docker image
echo -e "${GREEN}Building Docker image: ${IMAGE_NAME}${NC}"

if [ "$NEED_BUILDX" = true ]; then
    # Use buildx for cross-platform builds
    docker buildx build \
      --platform "$PLATFORM" \
      -t "$IMAGE_NAME:latest" \
      -f "$SCRIPT_DIR/Dockerfile" \
      --load \
      "$PROJECT_ROOT"
else
    # Standard build (native platform)
    docker build \
      --platform "$PLATFORM" \
      -t "$IMAGE_NAME:latest" \
      -f "$SCRIPT_DIR/Dockerfile" \
      "$PROJECT_ROOT"
fi

echo ""
echo -e "${GREEN}✓ Build complete!${NC}"
echo ""
echo "Image: ${IMAGE_NAME}:latest"
echo "Platform: ${PLATFORM}"
echo ""
echo "Usage examples:"
echo "  # Build for ARM64 (default, faster on M1):"
echo "    ./build.sh"
echo ""
echo "  # Build for AMD64 (for standard Lambda):"
echo "    PLATFORM=linux/amd64 ./build.sh"
echo ""
echo "  # Test the image locally:"
echo "    docker run --rm -p 9000:8080 ${IMAGE_NAME}:latest"
echo ""

