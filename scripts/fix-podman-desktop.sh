#!/bin/bash
# fix-podman-desktop.sh - Force healthcheck transitions for Podman Desktop sync
#
# Podman Desktop 1.24.x has a bug where containers show "CREATED" when
# healthchecks are in "starting" state. This script forces the transition.
#
# Usage: ./scripts/fix-podman-desktop.sh
#
# Per GAP-INFRA-PODMAN-DESKTOP: Known issue with healthcheck state sync

set -e

echo "=== Podman Desktop Healthcheck Fix ==="
echo ""

# Get compose containers
CONTAINERS=$(podman compose --profile cpu ps --format "{{.Names}}" 2>/dev/null | grep -v "^$" || true)

if [ -z "$CONTAINERS" ]; then
    echo "No compose containers found. Run: podman compose --profile cpu up -d"
    exit 1
fi

echo "Found containers:"
echo "$CONTAINERS"
echo ""

# Run healthcheck for each container
for container in $CONTAINERS; do
    echo -n "Checking $container... "

    # Check if container has healthcheck
    has_healthcheck=$(podman inspect "$container" --format '{{.Config.Healthcheck}}' 2>/dev/null || echo "")

    if [ -z "$has_healthcheck" ] || [ "$has_healthcheck" = "<nil>" ]; then
        echo "no healthcheck defined, skipping"
        continue
    fi

    # Get current health status
    health=$(podman inspect "$container" --format '{{.State.Health.Status}}' 2>/dev/null || echo "none")

    if [ "$health" = "healthy" ]; then
        echo "already healthy ✓"
        continue
    fi

    # Force healthcheck run
    if podman healthcheck run "$container" >/dev/null 2>&1; then
        echo "healthy ✓"
    else
        echo "unhealthy ✗"
    fi
done

echo ""
echo "=== Final Status ==="
podman compose --profile cpu ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null

echo ""
echo "Refresh Podman Desktop (↻ button) to see updated status."
