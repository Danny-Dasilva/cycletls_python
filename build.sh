#!/bin/bash
#
# CycleTLS Python - Multi-platform Build Script
#
# This script builds the Go binary for multiple platforms and architectures.
# The binaries are placed in the dist/ directory for packaging.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GOLANG_DIR="${PROJECT_ROOT}/golang"
DIST_DIR="${PROJECT_ROOT}/dist"

# Build information
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GO_VERSION=$(go version | awk '{print $3}')

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CycleTLS Python - Build Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Go Version: ${GO_VERSION}"
echo -e "Build Date: ${BUILD_DATE}"
echo ""

# Create dist directory
mkdir -p "${DIST_DIR}"

# Function to build for a specific platform
build_platform() {
    local GOOS=$1
    local GOARCH=$2
    local OUTPUT_NAME=$3

    echo -e "${YELLOW}Building for ${GOOS}/${GOARCH}...${NC}"

    cd "${GOLANG_DIR}"

    # Set environment variables
    export GOOS=${GOOS}
    export GOARCH=${GOARCH}
    export CGO_ENABLED=0

    # Build
    if go build -ldflags="-s -w" -o "${DIST_DIR}/${OUTPUT_NAME}" .; then
        local SIZE=$(du -h "${DIST_DIR}/${OUTPUT_NAME}" | cut -f1)
        echo -e "${GREEN}✓ Built ${OUTPUT_NAME} (${SIZE})${NC}"
    else
        echo -e "${RED}✗ Failed to build ${OUTPUT_NAME}${NC}"
        return 1
    fi
}

# Build for all platforms
echo -e "${BLUE}Building binaries for all platforms...${NC}"
echo ""

# Linux AMD64
build_platform "linux" "amd64" "cycletls-linux-amd64"

# Linux ARM64
build_platform "linux" "arm64" "cycletls-linux-arm64"

# macOS AMD64 (Intel)
build_platform "darwin" "amd64" "cycletls-darwin-amd64"

# macOS ARM64 (Apple Silicon)
build_platform "darwin" "arm64" "cycletls-darwin-arm64"

# Windows AMD64
build_platform "windows" "amd64" "cycletls-windows-amd64.exe"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Binaries location: ${DIST_DIR}"
echo ""
ls -lh "${DIST_DIR}"
echo ""

# Calculate total size
TOTAL_SIZE=$(du -sh "${DIST_DIR}" | cut -f1)
echo -e "Total size: ${TOTAL_SIZE}"
echo ""

# Create a generic symlink for the current platform
CURRENT_OS=$(uname -s | tr '[:upper:]' '[:lower:]')
CURRENT_ARCH=$(uname -m)

# Map architecture names
case ${CURRENT_ARCH} in
    x86_64)
        CURRENT_ARCH="amd64"
        ;;
    aarch64)
        CURRENT_ARCH="arm64"
        ;;
    arm64)
        CURRENT_ARCH="arm64"
        ;;
esac

if [ "${CURRENT_OS}" = "darwin" ]; then
    CURRENT_BINARY="cycletls-darwin-${CURRENT_ARCH}"
elif [ "${CURRENT_OS}" = "linux" ]; then
    CURRENT_BINARY="cycletls-linux-${CURRENT_ARCH}"
fi

if [ -n "${CURRENT_BINARY}" ] && [ -f "${DIST_DIR}/${CURRENT_BINARY}" ]; then
    ln -sf "${CURRENT_BINARY}" "${DIST_DIR}/cycletls"
    chmod +x "${DIST_DIR}/cycletls"
    echo -e "${GREEN}Created symlink: dist/cycletls -> ${CURRENT_BINARY}${NC}"
fi

echo ""
echo -e "${GREEN}Ready for packaging!${NC}"
