#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

TAG=$(python -c 'from cycletls import __version__; print("v" + __version__)')

# Function to run benchmarks
run_benchmarks() {
    echo "========================================"
    echo "Running CycleTLS Python Benchmarks"
    echo "========================================"

    # Check if Go is available
    if ! command -v go &> /dev/null; then
        echo "Warning: Go is not installed. Skipping benchmarks."
        return 0
    fi

    # Start bench_server.go in background
    echo "Starting benchmark server..."
    cd "$PROJECT_DIR"
    go run bench_server.go &
    BENCH_SERVER_PID=$!

    # Wait for server to be ready with retry logic
    echo "Waiting for benchmark server to be ready..."
    MAX_RETRIES=10
    RETRY_COUNT=0
    SERVER_READY=false

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        sleep 1
        if curl -s http://localhost:5001/ >/dev/null 2>&1; then
            SERVER_READY=true
            echo "Benchmark server is ready on port 5001 (PID: $BENCH_SERVER_PID)"
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "  Retry $RETRY_COUNT/$MAX_RETRIES..."
    done

    # Check if server is running and ready
    if ! $SERVER_READY; then
        echo "Warning: Benchmark server failed to become ready. Skipping benchmarks."
        kill $BENCH_SERVER_PID 2>/dev/null || true
        return 0
    fi

    # Run Python benchmarks
    echo ""
    echo "Running Python benchmarks (100 repetitions per test)..."
    python "$PROJECT_DIR/benchmarks/benchmark_python.py" \
        --url "http://localhost:5001/" \
        --repetitions 100 \
        --output "$PROJECT_DIR/benchmark_python_results.csv"

    BENCH_EXIT_CODE=$?

    # Stop bench_server.go
    echo ""
    echo "Stopping benchmark server..."
    kill $BENCH_SERVER_PID 2>/dev/null || true
    wait $BENCH_SERVER_PID 2>/dev/null || true

    if [ $BENCH_EXIT_CODE -eq 0 ]; then
        echo "Benchmarks completed successfully."
        echo "Results saved to: benchmark_python_results.csv"
    else
        echo "Warning: Benchmarks completed with errors (exit code: $BENCH_EXIT_CODE)"
    fi
    echo ""

    return $BENCH_EXIT_CODE
}

read -p "Creating new release for $TAG. Do you want to continue? [Y/n] " prompt

if [[ $prompt == "y" || $prompt == "Y" || $prompt == "yes" || $prompt == "Yes" ]]; then
    # Run benchmarks before release (optional)
    read -p "Run benchmarks before release? [y/N] " bench_prompt
    if [[ $bench_prompt == "y" || $bench_prompt == "Y" || $bench_prompt == "yes" || $bench_prompt == "Yes" ]]; then
        run_benchmarks
    fi

    python scripts/prepare_changelog.py
    git add -A
    git commit -m "Bump version to $TAG for release" || true && git push
    echo "Creating new git tag $TAG"
    git tag "$TAG" -m "$TAG"
    git push --tags
else
    echo "Cancelled"
    exit 1
fi
