#!/bin/bash
# Build the CycleTLS Go shared library for the current host platform.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GOLANG_DIR="${ROOT_DIR}/golang"
DIST_DIR="${ROOT_DIR}/dist"

if ! command -v go >/dev/null 2>&1; then
    echo "error: Go toolchain not found. Please install Go before running this script." >&2
    exit 1
fi

mkdir -p "${DIST_DIR}"

HOST_OS="$(go env GOOS)"
HOST_ARCH="$(go env GOARCH)"

# Normalize architecture names
case "${HOST_ARCH}" in
    amd64)
        ARCH_NAME="x64"
        ;;
    arm64)
        ARCH_NAME="arm64"
        ;;
    *)
        ARCH_NAME="${HOST_ARCH}"
        ;;
esac

case "${HOST_OS}" in
    windows)
        OUTPUT_NAME="cycletls-win-${ARCH_NAME}.dll"
        ;;
    darwin)
        OUTPUT_NAME="libcycletls-darwin-${ARCH_NAME}.dylib"
        ;;
    linux)
        OUTPUT_NAME="libcycletls-linux-${ARCH_NAME}.so"
        ;;
    *)
        echo "warning: unsupported GOOS '${HOST_OS}'. Defaulting to Linux-style .so output." >&2
        OUTPUT_NAME="libcycletls-linux-${ARCH_NAME}.so"
        ;;
 esac

pushd "${GOLANG_DIR}" >/dev/null
export CGO_ENABLED=1

go build -buildmode=c-shared -o "${DIST_DIR}/${OUTPUT_NAME}" .

popd >/dev/null

echo "Shared library written to ${DIST_DIR}/${OUTPUT_NAME}"
if [ -f "${DIST_DIR}/libcycletls.h" ]; then
    echo "Header generated at ${DIST_DIR}/libcycletls.h"
fi
