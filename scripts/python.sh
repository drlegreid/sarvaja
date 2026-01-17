#!/bin/bash
# Python Runner - Enterprise DevOps Pattern
# Usage: scripts/python.sh [python args...]
# Example: scripts/python.sh -m governance.loader
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

# Run python in container
exec podman exec -it "$CONTAINER" python "$@"
