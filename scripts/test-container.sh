#!/bin/bash
# Containerized Test Runner
# Per GAP-TEST-PROFILES: Full containerization option (Option B)
#
# Usage:
#   ./scripts/test-container.sh                    # Run all tests (except browser)
#   ./scripts/test-container.sh tests/integration  # Run specific tests
#   ./scripts/test-container.sh -m "unit"          # Run with markers
#   ./scripts/test-container.sh --build            # Rebuild container first
#
# Prerequisites:
#   - Services running: podman compose --profile dev up -d

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if --build flag is present
BUILD_FLAG=""
PYTEST_ARGS=()

for arg in "$@"; do
    if [ "$arg" = "--build" ]; then
        BUILD_FLAG="--build"
    else
        PYTEST_ARGS+=("$arg")
    fi
done

# Default to running all non-browser tests if no args provided
if [ ${#PYTEST_ARGS[@]} -eq 0 ]; then
    PYTEST_ARGS=("tests/" "-v" "--tb=short" "-m" "not browser")
fi

echo "=== Containerized Test Runner ==="
echo "Project: $PROJECT_DIR"
echo "Args: ${PYTEST_ARGS[*]}"

# Check if services are running
if ! podman compose --profile dev ps 2>/dev/null | grep -q "typedb"; then
    echo "⚠️  TypeDB not running. Starting services..."
    podman compose --profile dev up -d typedb chromadb governance-dashboard-dev
    echo "Waiting for services to be healthy..."
    sleep 10
fi

# Build if requested or if image doesn't exist
if [ -n "$BUILD_FLAG" ]; then
    echo "Building test-runner image..."
    podman compose --profile dev build test-runner
fi

# Run tests in container
echo "Running tests in container..."
podman compose --profile dev run --rm test-runner \
    python3 -m pytest "${PYTEST_ARGS[@]}"

echo "=== Test Run Complete ==="
