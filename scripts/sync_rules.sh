#!/bin/bash
# Wrapper script for sync_rules_to_typedb.py
# Per user feedback: avoid python vs python3 confusion

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use python3 explicitly
exec python3 "$SCRIPT_DIR/sync_rules_to_typedb.py" "$@"
