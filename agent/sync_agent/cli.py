"""
Sync Agent CLI.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: agent/sync_agent.py

Created: 2026-01-04
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import yaml

from .sync import SyncAgent
from .backlog import TaskBacklogAgent


def load_config(path: str = "config/sync_config.yaml") -> dict:
    """Load sync configuration from file."""
    if Path(path).exists():
        with open(path) as f:
            return yaml.safe_load(f)
    return {}


def print_usage():
    print("""
Sync Agent CLI
==============

Usage:
  python -m agent.sync_agent [command] [options]

Commands:
  --sync          Run sync agent (default)
  --sync-once     Single sync operation
  --sync-test     Test sync with sample data

  --backlog       Run task backlog agent
  --backlog-once  Process one task and exit
  --backlog-test  Test backlog with sample task claim

Options:
  --agent-id ID   Set agent ID (default: sync-agent-001)
  --api-url URL   API base URL (default: http://localhost:8082)

Examples:
  python -m agent.sync_agent --backlog --agent-id my-agent-001
  python -m agent.sync_agent --backlog-once
  python -m agent.sync_agent --sync-once
""")


def main():
    """Main entry point for CLI."""
    # Parse arguments
    args = sys.argv[1:]
    agent_id = "sync-agent-001"
    api_url = "http://localhost:8082"

    # Extract options
    if "--agent-id" in args:
        idx = args.index("--agent-id")
        if idx + 1 < len(args):
            agent_id = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    if "--api-url" in args:
        idx = args.index("--api-url")
        if idx + 1 < len(args):
            api_url = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    command = args[0] if args else "--sync"

    if command in ["-h", "--help"]:
        print_usage()
        sys.exit(0)

    # Task Backlog Agent commands
    if command == "--backlog":
        backlog_agent = TaskBacklogAgent(agent_id=agent_id, api_base_url=api_url)
        try:
            asyncio.run(backlog_agent.run_loop())
        except KeyboardInterrupt:
            backlog_agent.stop()
            print("\nBacklog agent stopped.")

    elif command == "--backlog-once":
        backlog_agent = TaskBacklogAgent(agent_id=agent_id, api_base_url=api_url)
        result = asyncio.run(backlog_agent.process_one_task())
        if result:
            print(f"Task processed. Stats: {backlog_agent.get_stats()}")
        else:
            print("No available tasks to process.")

    elif command == "--backlog-test":
        backlog_agent = TaskBacklogAgent(agent_id=agent_id, api_base_url=api_url)
        tasks = asyncio.run(backlog_agent.get_available_tasks())
        print(f"Available tasks: {len(tasks)}")
        if tasks:
            print(f"First task: {tasks[0].get('task_id', tasks[0].get('id'))}")
            print(f"Description: {tasks[0].get('description', 'N/A')}")

    # Sync Agent commands
    elif command in ["--sync", ""]:
        config = load_config()
        sync_agent = SyncAgent(config if config else None)
        try:
            asyncio.run(sync_agent.run())
        except KeyboardInterrupt:
            sync_agent.stop()
            print("\nSync agent stopped.")

    elif command == "--sync-once":
        config = load_config()
        sync_agent = SyncAgent(config if config else None)
        result = asyncio.run(sync_agent.sync_once())
        print(f"Sync result: {result}")

    elif command == "--sync-test":
        config = load_config()
        sync_agent = SyncAgent(config if config else None)
        sync_agent.track_change("skills", "test_skill_001", {
            "name": "Test Skill",
            "description": "A test skill for validation",
            "created_at": datetime.utcnow().isoformat()
        })
        result = asyncio.run(sync_agent.sync_once())
        print(f"Test sync result: {result}")

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
