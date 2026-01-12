"""
Sync Agent Data Models.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: agent/sync_agent.py

Created: 2026-01-04
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Change:
    """Represents a change to sync."""
    collection: str
    doc_id: str
    action: str  # upsert, delete
    data: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncResult:
    """Result of a sync operation."""
    timestamp: datetime
    changes_pushed: int = 0
    changes_pulled: int = 0
    conflicts_resolved: int = 0
    errors: list = field(default_factory=list)


@dataclass
class TaskExecution:
    """Result of executing a task."""
    task_id: str
    success: bool
    evidence: str
    duration_seconds: float
    rules_applied: list[str] = field(default_factory=list)
    error: Optional[str] = None


__all__ = ['Change', 'SyncResult', 'TaskExecution']
