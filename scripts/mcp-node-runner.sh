#!/bin/bash
# Node MCP Runner Script - Direct node invocation (bypasses npx overhead)
# Usage: mcp-node-runner.sh <package-name> [args...]
# Example: mcp-node-runner.sh dkmaker-mcp-rest-api
# Example: mcp-node-runner.sh @playwright/mcp --browser chromium
#
# Why: npx adds 3-30s+ overhead (registry checks, package resolution).
#      Direct node invocation starts in ~300ms from pre-installed packages.
# Per WORKFLOW-SHELL-01-v1: Pinned versions, no @latest tags.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NODE_DIR="$PROJECT_DIR/node_modules"
NODE="/home/oderid/.config/nvm/versions/node/v20.19.6/bin/node"

PACKAGE="$1"
shift

if [ -z "$PACKAGE" ]; then
    echo "Usage: mcp-node-runner.sh <package-name> [args...]" >&2
    exit 1
fi

# Resolve entry point from package.json "bin" field
PKG_DIR="$NODE_DIR/$PACKAGE"
if [ ! -d "$PKG_DIR" ]; then
    echo "[mcp-node-runner] ERROR: Package '$PACKAGE' not found in $NODE_DIR" >&2
    echo "[mcp-node-runner] Run: cd $PROJECT_DIR && npm install" >&2
    exit 1
fi

# Get bin entry from package.json
BIN_PATH=$(cd "$PKG_DIR" && "$NODE" -e "
  const pkg = require('./package.json');
  const bin = pkg.bin;
  if (typeof bin === 'string') { console.log(bin); }
  else if (typeof bin === 'object') { console.log(Object.values(bin)[0]); }
  else { process.exit(1); }
")

if [ -z "$BIN_PATH" ] || [ ! -f "$PKG_DIR/$BIN_PATH" ]; then
    echo "[mcp-node-runner] ERROR: Cannot resolve bin entry for '$PACKAGE'" >&2
    exit 1
fi

ENTRY="$PKG_DIR/$BIN_PATH"
echo "[mcp-node-runner] Starting $PACKAGE via $ENTRY" >&2

exec "$NODE" "$ENTRY" "$@"
