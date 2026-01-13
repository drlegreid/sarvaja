#!/usr/bin/env python3
"""
Claude Code Settings Recovery Script

Creates a backup of settings.local.json with timestamp suffix and restores
to a clean minimal configuration.

Usage:
    python .claude/hooks/recover.py [--backup-only] [--restore FILE]

Options:
    --backup-only   Only create backup, don't restore to minimal
    --restore FILE  Restore from a specific backup file
    --list          List available backups
    --help          Show this help

Per EPIC-006: Used when hooks cause Claude Code startup failures.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


# Configuration
CLAUDE_DIR = Path(__file__).parent.parent  # .claude directory
SETTINGS_FILE = CLAUDE_DIR / "settings.local.json"
BACKUP_DIR = CLAUDE_DIR / "backups"


def get_timestamp() -> str:
    """Get timestamp for backup filename."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_backup() -> Path:
    """Create backup of current settings.local.json."""
    BACKUP_DIR.mkdir(exist_ok=True)

    if not SETTINGS_FILE.exists():
        print(f"No settings file to backup: {SETTINGS_FILE}")
        return None

    timestamp = get_timestamp()
    backup_path = BACKUP_DIR / f"settings.local.json.{timestamp}.bak"

    shutil.copy2(SETTINGS_FILE, backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path


def get_minimal_settings() -> dict:
    """Get minimal safe settings configuration."""
    return {
        "hooks": {
            "SessionStart": [
                {
                    "type": "command",
                    "command": f"python3 {CLAUDE_DIR / 'hooks' / 'healthcheck.py'}",
                    "timeout": 3000
                }
            ]
        }
    }


def restore_minimal():
    """Restore to minimal safe settings."""
    minimal = get_minimal_settings()

    with open(SETTINGS_FILE, "w") as f:
        json.dump(minimal, f, indent=2)

    print(f"Restored minimal settings: {SETTINGS_FILE}")
    print("Minimal hooks enabled: SessionStart (healthcheck only)")


def restore_from_backup(backup_file: Path):
    """Restore from a specific backup file."""
    if not backup_file.exists():
        print(f"Backup file not found: {backup_file}")
        return False

    # Backup current before restoring
    if SETTINGS_FILE.exists():
        create_backup()

    shutil.copy2(backup_file, SETTINGS_FILE)
    print(f"Restored from: {backup_file}")
    return True


def list_backups():
    """List available backup files."""
    if not BACKUP_DIR.exists():
        print("No backups directory found.")
        return []

    backups = sorted(BACKUP_DIR.glob("settings.local.json.*.bak"), reverse=True)

    if not backups:
        print("No backup files found.")
        return []

    print(f"Available backups ({len(backups)}):")
    for backup in backups:
        # Extract timestamp from filename
        stat = backup.stat()
        size = stat.st_size
        print(f"  {backup.name} ({size} bytes)")

    return backups


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Settings Recovery Script"
    )
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Only create backup, don't restore"
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

    args = parser.parse_args()

    if args.list:
        list_backups()
        return 0

    if args.restore:
        if not args.restore.exists():
            # Check in backup dir
            backup_path = BACKUP_DIR / args.restore
            if not backup_path.exists():
                print(f"Backup file not found: {args.restore}")
                return 1
            args.restore = backup_path

        return 0 if restore_from_backup(args.restore) else 1

    # Default: backup and restore minimal
    print("=" * 50)
    print("Claude Code Settings Recovery")
    print("=" * 50)

    backup_path = create_backup()

    if not args.backup_only:
        print()
        restore_minimal()
        print()
        print("Recovery complete!")
        print("Restart Claude Code to apply minimal settings.")
        if backup_path:
            print(f"To restore: python .claude/hooks/recover.py --restore {backup_path.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
