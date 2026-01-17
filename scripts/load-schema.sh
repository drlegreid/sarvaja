#!/bin/bash
# TypeDB Schema Loader - Enterprise DevOps Pattern
# Usage: scripts/load-schema.sh [--modular]
#
# Options:
#   --modular  Load from governance/schema/ modules instead of schema.tql
#
# Per EPIC-DR-012: Modular schema loading
# Per WORKFLOW-SHELL-01-v1: Shell wrappers for Python commands

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTAINER="platform_governance-dashboard-dev_1"

# Check for --modular flag
if [ "$1" = "--modular" ]; then
    export USE_MODULAR_SCHEMA=true
    shift
fi

# Check if container is running
if ! podman ps --format "{{.Names}}" | grep -q "^${CONTAINER}$"; then
    echo "[ERROR] Container not running: $CONTAINER" >&2
    echo "Start with: podman compose --profile cpu --profile dashboard-dev up -d" >&2
    exit 1
fi

# Run schema loader in container
if [ -n "$USE_MODULAR_SCHEMA" ]; then
    echo "[INFO] Loading modular schema from governance/schema/"
    exec podman exec -e USE_MODULAR_SCHEMA=true "$CONTAINER" python -m governance.loader
else
    echo "[INFO] Loading monolithic schema from governance/schema.tql"
    exec podman exec "$CONTAINER" python -m governance.loader
fi
