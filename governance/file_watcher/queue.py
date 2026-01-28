"""
File Event Queue.

Per GAP-SYNC-AUTO-001: Batch file changes for efficient sync.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Implements a debounced event queue to batch rapid file changes
and prevent excessive sync operations.

Created: 2026-01-21
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
from collections import defaultdict


class FileEventType(str, Enum):
    """Types of file events."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class SyncCategory(str, Enum):
    """Categories for sync prioritization."""
    RULES = "rules"      # docs/rules/**/*.md
    TASKS = "tasks"      # TODO.md, docs/backlog/**/*.md
    EVIDENCE = "evidence"  # evidence/**/*.md
    GAPS = "gaps"        # docs/gaps/**/*.md
    OTHER = "other"


@dataclass
class FileEvent:
    """Represents a file change event."""
    path: str
    event_type: FileEventType
    timestamp: float = field(default_factory=time.time)
    category: SyncCategory = SyncCategory.OTHER

    @classmethod
    def categorize(cls, path: str) -> SyncCategory:
        """Determine sync category from file path."""
        path_lower = path.lower()
        if "/docs/rules/" in path_lower:
            return SyncCategory.RULES
        if "todo.md" in path_lower or "/docs/backlog/" in path_lower:
            return SyncCategory.TASKS
        # Check gaps BEFORE evidence (gaps/evidence/ should be GAPS)
        if "/docs/gaps/" in path_lower:
            return SyncCategory.GAPS
        if "/evidence/" in path_lower:
            return SyncCategory.EVIDENCE
        return SyncCategory.OTHER


@dataclass
class FileEventQueue:
    """
    Event queue with debouncing and batching.

    Features:
    - Debounce rapid changes to same file
    - Batch changes by category
    - Priority ordering (rules > tasks > evidence)
    """
    debounce_seconds: float = 2.0  # Wait time before processing
    max_batch_size: int = 50
    _events: Dict[str, FileEvent] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _last_event_time: float = field(default=0.0)

    async def add_event(self, event: FileEvent) -> None:
        """
        Add event to queue, deduping by path.

        Later events for same path replace earlier ones (debounce).
        """
        async with self._lock:
            # Dedupe by path - keep latest event for each file
            self._events[event.path] = event
            self._last_event_time = time.time()

    async def get_batch(self) -> List[FileEvent]:
        """
        Get batch of events ready for processing.

        Returns empty list if debounce period hasn't elapsed.
        """
        async with self._lock:
            # Check if debounce period has elapsed
            if time.time() - self._last_event_time < self.debounce_seconds:
                return []

            if not self._events:
                return []

            # Get all events, sorted by priority (category)
            events = list(self._events.values())
            self._events.clear()

            # Sort by category priority: RULES > TASKS > GAPS > EVIDENCE > OTHER
            priority_order = {
                SyncCategory.RULES: 0,
                SyncCategory.TASKS: 1,
                SyncCategory.GAPS: 2,
                SyncCategory.EVIDENCE: 3,
                SyncCategory.OTHER: 4,
            }
            events.sort(key=lambda e: priority_order.get(e.category, 5))

            # Limit batch size
            return events[:self.max_batch_size]

    async def size(self) -> int:
        """Get current queue size."""
        async with self._lock:
            return len(self._events)

    async def clear(self) -> int:
        """Clear queue and return count of cleared events."""
        async with self._lock:
            count = len(self._events)
            self._events.clear()
            return count

    def get_stats(self) -> dict:
        """Get queue statistics (non-async for status checks)."""
        return {
            "queue_size": len(self._events),
            "debounce_seconds": self.debounce_seconds,
            "last_event_time": self._last_event_time,
            "categories": self._count_by_category(),
        }

    def _count_by_category(self) -> Dict[str, int]:
        """Count events by category."""
        counts = defaultdict(int)
        for event in self._events.values():
            counts[event.category.value] += 1
        return dict(counts)
