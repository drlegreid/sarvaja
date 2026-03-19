#!/usr/bin/env bash
# Restart the governance dashboard container after agent/ code changes.
# Trame has NO hot-reload — container restart is required for UI changes.
#
# Usage: scripts/restart-dashboard.sh

set -euo pipefail

CONTAINER="platform_governance-dashboard-dev_1"

echo "Restarting $CONTAINER..."
podman restart "$CONTAINER"

# Wait for health check to pass (up to 60s)
echo "Waiting for container to become healthy..."
for i in $(seq 1 30); do
    STATUS=$(podman inspect --format '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "healthy" ]; then
        echo "Dashboard is healthy (took ~$((i * 2))s)"
        exit 0
    fi
    sleep 2
done

echo "WARNING: Dashboard did not become healthy within 60s"
echo "Current status: $(podman inspect --format '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo 'unknown')"
exit 1
