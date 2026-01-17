#!/bin/bash
# Pytest Runner - Enterprise DevOps Pattern
# Usage: scripts/pytest.sh [pytest args...]
# Example: scripts/pytest.sh tests/test_governance.py -v
#
# Per WORKFLOW-SHELL-01-v1: Shell wrappers for Python commands
# Avoids Python environment confusion in Claude Code sessions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTAINER="platform_governance-dashboard-dev_1"

# Check if container is running
if ! podman ps --format "{{.Names}}" | grep -q "^${CONTAINER}$"; then
    echo "[ERROR] Container not running: $CONTAINER" >&2
    echo "Start with: podman compose --profile cpu --profile dashboard-dev up -d" >&2
    exit 1
fi

# Run pytest in container with tests directory mounted
exec podman exec -w /app \
    -e PYTHONPATH=/app \
    -e TYPEDB_HOST=localhost \
    -e CHROMADB_HOST=localhost \
    "$CONTAINER" \
    sh -c "cd /app && python -m pytest $*"
