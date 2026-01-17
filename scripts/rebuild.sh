#!/bin/bash
# Container Rebuild - Proper DevOps Workflow
# Per RULE-054 (CONTAINER-MGMT-01-v1): Proper container cleanup and rebuild
#
# Usage: scripts/rebuild.sh [--quick]
#   --quick  Skip down, just rebuild running containers
#
# Per WORKFLOW-SHELL-01-v1: Shell wrappers for DevOps commands

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROFILES="--profile cpu --profile dashboard-dev"

cd "$PROJECT_DIR" || exit 1

# Check for orphan containers first
echo "[INFO] Checking for orphan containers..."
ORPHANS=$(podman ps -a --filter "status=exited" --format "{{.Names}}" | grep "^platform_" || true)
if [ -n "$ORPHANS" ]; then
    echo "[WARN] Found orphan containers, cleaning up:"
    echo "$ORPHANS"
    podman rm $ORPHANS 2>/dev/null || true
fi

if [ "$1" = "--quick" ]; then
    echo "[INFO] Quick rebuild (containers stay up)..."
    exec podman compose $PROFILES up -d --build
else
    echo "[INFO] Full rebuild (clean restart)..."
    podman compose $PROFILES down
    exec podman compose $PROFILES up -d --build
fi
