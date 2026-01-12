#!/usr/bin/env python3
"""
MCP Configuration Backup Script

Creates timestamped backups of MCP configuration files and manages restoration.

Usage:
    python .claude/scripts/mcp-backup.py [--backup-only] [--restore FILE] [--list]

Options:
    --backup-only   Only create backup, don't modify configs
    --restore FILE  Restore from a specific backup file
    --list          List available backups
    --help          Show this help

Per R&D TOOL-009: MCP optimization for memory management.
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


# Configuration
CLAUDE_DIR = Path(__file__).parent.parent  # .claude directory
PROJECT_ROOT = CLAUDE_DIR.parent
BACKUP_DIR = CLAUDE_DIR / "backups" / "mcp"

# MCP config files
MCP_FILES = {
    "project": PROJECT_ROOT / ".mcp.json",
    "disabled": CLAUDE_DIR / "mcp-backup.json",
    "global": Path.home() / ".claude.json"
}


def get_timestamp() -> str:
    """Get timestamp for backup filename."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_backup() -> Path:
    """Create backup of all MCP configuration files."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = get_timestamp()
    backup_data = {
        "_created": datetime.now().isoformat(),
        "_files_backed_up": [],
        "configs": {}
    }

    for name, path in MCP_FILES.items():
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    backup_data["configs"][name] = {
                        "path": str(path),
                        "content": json.load(f)
                    }
                backup_data["_files_backed_up"].append(name)
                print(f"Backed up: {name} ({path})")
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse {name} ({path}): {e}")
        else:
            print(f"Skipped (not found): {name} ({path})")

    backup_path = BACKUP_DIR / f"mcp-backup.{timestamp}.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2)

    print(f"\nBackup created: {backup_path}")
    return backup_path


def restore_from_backup(backup_file: Path) -> bool:
    """Restore MCP configs from a backup file."""
    if not backup_file.exists():
        print(f"Backup file not found: {backup_file}")
        return False

    # Create backup before restoring
    print("Creating backup of current state before restore...")
    create_backup()
    print()

    with open(backup_file, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    configs = backup_data.get("configs", {})
    restored = []

    for name, data in configs.items():
        path = Path(data["path"])
        content = data["content"]

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)
            restored.append(name)
            print(f"Restored: {name} ({path})")
        except Exception as e:
            print(f"Error restoring {name}: {e}")

    print(f"\nRestored {len(restored)} config(s) from: {backup_file}")
    return True


def list_backups() -> list:
    """List available backup files."""
    if not BACKUP_DIR.exists():
        print("No backups directory found.")
        return []

    backups = sorted(BACKUP_DIR.glob("mcp-backup.*.json"), reverse=True)

    if not backups:
        print("No backup files found.")
        return []

    print(f"Available MCP backups ({len(backups)}):\n")
    for backup in backups:
        stat = backup.stat()
        size = stat.st_size

        # Try to read metadata
        try:
            with open(backup, "r") as f:
                data = json.load(f)
            files = ", ".join(data.get("_files_backed_up", []))
            created = data.get("_created", "unknown")
        except Exception:
            files = "unknown"
            created = "unknown"

        print(f"  {backup.name}")
        print(f"    Created: {created}")
        print(f"    Files: {files}")
        print(f"    Size: {size} bytes")
        print()

    return backups


def validate_mcp_json(path: Path) -> dict:
    """Validate an MCP JSON file and return parsed content."""
    if not path.exists():
        return {"valid": False, "error": "File not found"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check for expected structure
        if path.name == ".mcp.json":
            if "mcpServers" not in data:
                return {"valid": False, "error": "Missing mcpServers key"}
            servers = data["mcpServers"]
            return {
                "valid": True,
                "server_count": len(servers),
                "servers": list(servers.keys())
            }
        elif path.name == "mcp-backup.json":
            if "disabled_mcps" not in data:
                return {"valid": False, "error": "Missing disabled_mcps key"}
            disabled = data["disabled_mcps"]
            return {
                "valid": True,
                "disabled_count": len(disabled),
                "servers": list(disabled.keys())
            }
        elif path.name == ".claude.json":
            if "mcpServers" not in data:
                return {"valid": False, "error": "Missing mcpServers key"}
            servers = data["mcpServers"]
            return {
                "valid": True,
                "server_count": len(servers),
                "servers": list(servers.keys())
            }
        else:
            return {"valid": True, "note": "Unknown format"}

    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"Invalid JSON: {e}"}


def show_status():
    """Show current MCP configuration status."""
    print("=" * 60)
    print("MCP Configuration Status")
    print("=" * 60)

    for name, path in MCP_FILES.items():
        print(f"\n{name.upper()}: {path}")
        result = validate_mcp_json(path)

        if result["valid"]:
            if "server_count" in result:
                print(f"  Status: Valid ({result['server_count']} servers)")
                print(f"  Servers: {', '.join(result['servers'][:5])}")
                if len(result['servers']) > 5:
                    print(f"           ... and {len(result['servers']) - 5} more")
            elif "disabled_count" in result:
                print(f"  Status: Valid ({result['disabled_count']} disabled)")
                print(f"  Disabled: {', '.join(result['servers'])}")
            else:
                print(f"  Status: Valid")
        else:
            print(f"  Status: INVALID - {result['error']}")


def main():
    parser = argparse.ArgumentParser(
        description="MCP Configuration Backup Script"
    )
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Only create backup"
    )
    parser.add_argument(
        "--restore",
        type=Path,
        help="Restore from specific backup file"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current MCP config status"
    )

    args = parser.parse_args()

    if args.list:
        list_backups()
        return 0

    if args.status:
        show_status()
        return 0

    if args.restore:
        if not args.restore.exists():
            # Check in backup dir
            backup_path = BACKUP_DIR / args.restore
            if not backup_path.exists():
                # Try with just filename
                backup_path = BACKUP_DIR / args.restore.name
                if not backup_path.exists():
                    print(f"Backup file not found: {args.restore}")
                    return 1
            args.restore = backup_path

        return 0 if restore_from_backup(args.restore) else 1

    # Default: show status and create backup
    print("=" * 60)
    print("MCP Configuration Backup")
    print("=" * 60)

    show_status()
    print()

    backup_path = create_backup()

    if not args.backup_only:
        print()
        print("Backup complete!")
        print(f"To restore: python .claude/scripts/mcp-backup.py --restore {backup_path.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
