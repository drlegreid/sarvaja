"""
Sync Agent for Sarvaja PoC.
Synchronizes skills, sessions, rules, and memories across environments.

MODULARIZED: 2026-01-04 per RULE-032 (File Size Limit < 300 lines)
Original file was 687 lines, now split into sync_agent/ module:
- sync_agent/models.py: Data models (Change, SyncResult, TaskExecution)
- sync_agent/transports.py: Transport implementations (Git, ClearML, Local)
- sync_agent/resolver.py: ConflictResolver
- sync_agent/sync.py: SyncAgent orchestrator
- sync_agent/backlog.py: TaskBacklogAgent
- sync_agent/governance_sync.py: TypeDB ↔ Filesystem sync (2026-01-11)
- sync_agent/cli.py: CLI and main entry point

This file is a backward-compatible wrapper.
Import from agent.sync_agent for all sync operations.

Transports:
- Git: Skillbooks and rules (version controlled)
- ClearML: Sessions (MLOps integration)
- WebDAV: Local network sync (laptop ↔ server)

Task Backlog Agent (TODO-6/7):
- Picks up tasks from governance API
- Reports evidence on task completion
- Integrates with rule monitoring

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing

Created: 2024-12-XX
Modularized: 2026-01-04
"""

# Backward-compatible imports - all operations now in sync_agent/ submodule
from .sync_agent import (
    # Models
    Change,
    SyncResult,
    TaskExecution,
    # Transports
    SyncTransport,
    GitTransport,
    ClearMLTransport,
    LocalFileTransport,
    # Resolver
    ConflictResolver,
    # Agents
    SyncAgent,
    TaskBacklogAgent,
    GovernanceSync,
    SyncStatus,
    # CLI
    load_config,
    main,
)

__all__ = [
    # Models
    'Change',
    'SyncResult',
    'TaskExecution',
    # Transports
    'SyncTransport',
    'GitTransport',
    'ClearMLTransport',
    'LocalFileTransport',
    # Resolver
    'ConflictResolver',
    # Agents
    'SyncAgent',
    'TaskBacklogAgent',
    'GovernanceSync',
    'SyncStatus',
    # CLI
    'load_config',
    'main',
]


if __name__ == "__main__":
    main()
