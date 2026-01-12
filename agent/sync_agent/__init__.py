"""
Sync Agent Module.

Per RULE-032: File Size Limit (< 300 lines)
Modularized from: agent/sync_agent.py (687 lines)

Created: 2026-01-04

This module combines all sync agent components:
- Models: Change, SyncResult, TaskExecution
- Transports: SyncTransport, GitTransport, ClearMLTransport, LocalFileTransport
- Resolver: ConflictResolver
- SyncAgent: Main sync orchestrator
- TaskBacklogAgent: Task execution agent
- CLI: Command-line interface
"""

from .models import Change, SyncResult, TaskExecution
from .transports import (
    SyncTransport,
    GitTransport,
    ClearMLTransport,
    LocalFileTransport,
)
from .resolver import ConflictResolver
from .sync import SyncAgent
from .backlog import TaskBacklogAgent
from .governance_sync import GovernanceSync, SyncStatus
from .cli import load_config, main


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
