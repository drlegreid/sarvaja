#!/bin/bash
# Sim.ai Foundation Setup Script
# xubuntu migration - 2026-01-09
# Installs all dependencies for MCP + Multi-Agent orchestration

set -e

echo "=== Sim.ai Foundation Setup ==="
echo "Building: MCP + Multi-Agent + Governance Layer"
echo ""

# Step 1: System prerequisites
echo "[1/5] Installing system packages..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev git curl

# Step 2: Create virtual environment
echo "[2/5] Creating Python virtual environment..."
VENV_PATH="$HOME/.venv/sim-ai"
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"

# Step 3: Core sim-ai dependencies
echo "[3/5] Installing sim-ai core dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Test dependencies
echo "[4/5] Installing test dependencies..."
pip install -r requirements-test.txt

# Step 5: Claude Agent SDK + Multi-Agent
echo "[5/5] Installing Claude Agent SDK for multi-agent orchestration..."
pip install claude-agent-sdk mcp-agent

echo ""
echo "=== Foundation Complete ==="
echo ""
echo "Installed packages:"
pip list | grep -E "(mcp|claude|anthropic|agno|typedb|chromadb|fastapi)"
echo ""
echo "Activate venv: source ~/.venv/sim-ai/bin/activate"
echo "Verify MCP:    python3 -m governance.mcp_server_core --help"
echo ""
echo "Next: Restart Claude Code to pick up MCP servers"
