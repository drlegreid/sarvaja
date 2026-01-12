#!/bin/bash
# MCP Runner Script - Enterprise DevOps Pattern
# Usage: mcp-runner.sh <module-name>
# Example: mcp-runner.sh governance.mcp_server_core
#
# Modes:
#   MCP_MODE=container (default) - Run in Python 3.12 container
#   MCP_MODE=venv               - Run in local venv (legacy)
#
# Per GAP-MCP-002: Sandboxed, version-controlled runtime

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MCP_MODE="${MCP_MODE:-container}"
MCP_IMAGE="${MCP_IMAGE:-sim-ai-mcp:latest}"

# Container mode (Enterprise DevOps - sandboxed Python 3.12)
if [ "$MCP_MODE" = "container" ]; then
    # Check if image exists, build if not
    if ! podman image exists "$MCP_IMAGE" 2>/dev/null; then
        echo "Building MCP container image..." >&2
        podman build -t "$MCP_IMAGE" -f "$PROJECT_DIR/Dockerfile.mcp" "$PROJECT_DIR" >&2
    fi

    # Run MCP server in container with stdio passthrough
    # --network=host: Access TypeDB/ChromaDB on localhost ports
    # -i: Interactive mode for MCP stdio protocol
    exec podman run --rm -i \
        --network=host \
        -e TYPEDB_HOST="${TYPEDB_HOST:-localhost}" \
        -e TYPEDB_PORT="${TYPEDB_PORT:-1729}" \
        -e CHROMADB_HOST="${CHROMADB_HOST:-localhost}" \
        -e CHROMADB_PORT="${CHROMADB_PORT:-8001}" \
        -v "$PROJECT_DIR/governance:/app/governance:ro" \
        -v "$PROJECT_DIR/claude_mem:/app/claude_mem:ro" \
        -v "$PROJECT_DIR/docs:/app/docs:ro" \
        -v "$PROJECT_DIR/evidence:/app/evidence:rw" \
        "$MCP_IMAGE" \
        python -m "$1"
fi

# Venv mode (Legacy - requires Python 3.12 on host)
if [ -f "$HOME/.venv/sim-ai/bin/activate" ]; then
    source "$HOME/.venv/sim-ai/bin/activate"
fi

export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
exec python -m "$1"
