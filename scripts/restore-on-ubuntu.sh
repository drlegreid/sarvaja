#!/bin/bash
# Restore Script for Ubuntu after Migration
# Per RULE-024: AMNESIA Protocol
# Created: 2026-01-04
#
# Usage: ./scripts/restore-on-ubuntu.sh /path/to/backup

set -e

BACKUP_PATH="${1:-/media/backup}"

echo "============================================"
echo "  Sarvaja Migration Restore Script (Ubuntu)"
echo "  Backup Source: $BACKUP_PATH"
echo "============================================"

# Verify backup exists
if [ ! -f "$BACKUP_PATH/BACKUP_INVENTORY.json" ]; then
    echo "ERROR: Backup inventory not found at $BACKUP_PATH"
    echo "Please provide the correct backup path as argument"
    exit 1
fi

# Create target directories
echo ""
echo "[1/6] Creating target directories..."
mkdir -p ~/Documents/Vibe
mkdir -p ~/.claude-mem

# Restore Vibe directory
echo ""
echo "[2/6] Restoring Vibe directory..."
if [ -d "$BACKUP_PATH/Vibe" ]; then
    cp -r "$BACKUP_PATH/Vibe/"* ~/Documents/Vibe/
    echo "  Vibe directory restored"
else
    echo "  WARNING: Vibe directory not found in backup"
fi

# Restore claude-mem
echo ""
echo "[3/6] Restoring claude-mem..."
if [ -d "$BACKUP_PATH/.claude-mem" ]; then
    cp -r "$BACKUP_PATH/.claude-mem/"* ~/.claude-mem/
    echo "  Claude-mem restored"
else
    echo "  WARNING: claude-mem not found in backup"
fi

# Create Docker volumes
echo ""
echo "[4/6] Creating Docker volumes..."
podman volume create sim-ai_typedb_data 2>/dev/null || true
podman volume create sim-ai_chromadb_data 2>/dev/null || true
podman volume create sim-ai_ollama_data 2>/dev/null || true
podman volume create claude-memory 2>/dev/null || true
echo "  Docker volumes created"

# Restore Docker volume data
echo ""
echo "[5/6] Restoring Docker volume data..."

restore_volume() {
    local vol_name=$1
    local backup_dir=$2

    if [ -d "$BACKUP_PATH/Docker/$backup_dir" ]; then
        echo "  Restoring $vol_name..."
        podman run --rm \
            -v "$vol_name:/data" \
            -v "$BACKUP_PATH/Docker/$backup_dir:/backup:ro" \
            alpine sh -c "cp -r /backup/* /data/ 2>/dev/null || true"
        echo "    $vol_name restored"
    else
        echo "    SKIP: $backup_dir not found in backup"
    fi
}

restore_volume "sim-ai_typedb_data" "typedb_data"
restore_volume "sim-ai_chromadb_data" "chromadb_data"
restore_volume "sim-ai_ollama_data" "ollama_data"
restore_volume "claude-memory" "claude_memory"

# Set up Python environment
echo ""
echo "[6/6] Setting up Python environment..."
cd ~/Documents/Vibe/sarvaja/platform

if command -v python3.12 &> /dev/null; then
    python3.12 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    echo "  Python environment created"
else
    echo "  WARNING: Python 3.12 not found. Install it and run:"
    echo "    python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

# Summary
echo ""
echo "============================================"
echo "  RESTORE COMPLETE"
echo "============================================"
echo ""
echo "Next Steps:"
echo "  1. Start Docker services:"
echo "     cd ~/Documents/Vibe/sarvaja/platform"
echo "     podman compose --profile dev up -d"
echo ""
echo "  2. Verify recovery:"
echo "     source .venv/bin/activate"
echo "     python -c \"from governance.client import TypeDBClient; c=TypeDBClient(); print('Rules:', len(c.get_all_rules()))\""
echo ""
echo "  3. Set environment variables in ~/.bashrc:"
echo "     export ANTHROPIC_API_KEY='sk-ant-...'"
echo "     export LITELLM_MASTER_KEY='sk-litellm-master-key'"
echo ""
echo "Full recovery guide: ~/Documents/Vibe/sarvaja/platform/docs/RECOVERY.md"
echo ""
