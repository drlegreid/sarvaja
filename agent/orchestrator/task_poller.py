"""
TypeDB Task Poller (ORCH-002).

Polls TypeDB for available tasks and manages task claiming.

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class TaskPriority(Enum):
    """Task priority levels per RULE-011."""
    CRITICAL = 0  # Highest priority
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class PollableTask:
    """Task from TypeDB ready for dispatch."""
    task_id: str
    name: str
    priority: TaskPriority
    phase: str
    status: str
    requires_evidence: bool
    agent_id: Optional[str] = None
    claimed_at: Optional[datetime] = None
    body: Optional[str] = None
    gap_id: Optional[str] = None

    @classmethod
    def from_typedb_task(cls, task: Any) -> "PollableTask":
        """Convert TypeDB Task to PollableTask."""
        # Map string priority to enum
        priority_map = {
            "CRITICAL": TaskPriority.CRITICAL,
            "HIGH": TaskPriority.HIGH,
            "MEDIUM": TaskPriority.MEDIUM,
            "LOW": TaskPriority.LOW,
        }
        # Infer priority from phase prefix or default to MEDIUM
        priority = TaskPriority.MEDIUM
        if hasattr(task, 'phase') and task.phase:
            if task.phase.startswith("P10") or task.phase.startswith("P11"):
                priority = TaskPriority.HIGH
            elif task.phase.startswith("RD"):
                priority = TaskPriority.MEDIUM

        # Determine if evidence required (CRITICAL/HIGH per RULE-028)
        requires_evidence = priority in (TaskPriority.CRITICAL, TaskPriority.HIGH)

        return cls(
            task_id=task.id,
            name=task.name,
            priority=priority,
            phase=task.phase,
            status=task.status,
            requires_evidence=requires_evidence,
            agent_id=task.agent_id if hasattr(task, 'agent_id') else None,
            body=task.body if hasattr(task, 'body') else None,
            gap_id=task.gap_id if hasattr(task, 'gap_id') else None,
        )


class TypeDBTaskPoller:
    """
    Polls TypeDB for available tasks.

    Usage:
        poller = TypeDBTaskPoller(typedb_client)

        # One-shot poll
        tasks = await poller.poll_once()

        # Continuous polling with callback
        await poller.start_polling(callback=on_task_available, interval=5.0)

        # Stop polling
        await poller.stop_polling()
    """

    def __init__(self, client: Any, poll_interval: float = 5.0):
        """
        Initialize poller.

        Args:
            client: TypeDB client instance (governance.client.TypeDBClient)
            poll_interval: Seconds between polls (default 5.0)
        """
        self._client = client
        self._poll_interval = poll_interval
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[PollableTask], None]] = []
        self._last_poll: Optional[datetime] = None
        self._poll_count = 0
        self._tasks_found = 0

    @property
    def is_running(self) -> bool:
        """Check if poller is actively polling."""
        return self._running

    @property
    def stats(self) -> Dict[str, Any]:
        """Get polling statistics."""
        return {
            "running": self._running,
            "poll_count": self._poll_count,
            "tasks_found": self._tasks_found,
            "last_poll": self._last_poll.isoformat() if self._last_poll else None,
            "interval_seconds": self._poll_interval,
        }

    def add_callback(self, callback: Callable[[PollableTask], None]) -> None:
        """Add callback for when tasks are found."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[PollableTask], None]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def poll_once(self) -> List[PollableTask]:
        """
        Poll TypeDB once for available tasks.

        Returns:
            List of unclaimed tasks ready for dispatch.
        """
        self._poll_count += 1
        self._last_poll = datetime.now()

        try:
            # Use existing client method
            typedb_tasks = self._client.get_available_tasks()

            pollable_tasks = [
                PollableTask.from_typedb_task(t)
                for t in typedb_tasks
            ]

            self._tasks_found += len(pollable_tasks)

            # Sort by priority (CRITICAL first)
            pollable_tasks.sort(key=lambda t: t.priority.value)

            return pollable_tasks

        except Exception as e:
            print(f"[TypeDBTaskPoller] Poll error: {e}")
            return []

    async def claim_task(self, task_id: str, agent_id: str) -> bool:
        """
        Claim a task for an agent.

        Prevents duplicate execution per ORCH-003 requirements.

        Args:
            task_id: Task to claim
            agent_id: Agent claiming the task

        Returns:
            True if claim successful, False if already claimed
        """
        try:
            result = self._client.update_task_status(
                task_id=task_id,
                status="in_progress",
                agent_id=agent_id
            )
            return result is not None
        except Exception as e:
            print(f"[TypeDBTaskPoller] Claim error: {e}")
            return False

    async def release_task(self, task_id: str) -> bool:
        """
        Release a claimed task back to available pool.

        Used when agent cannot complete task.

        Args:
            task_id: Task to release

        Returns:
            True if release successful
        """
        try:
            result = self._client.update_task_status(
                task_id=task_id,
                status="pending",
                agent_id=None
            )
            return result is not None
        except Exception as e:
            print(f"[TypeDBTaskPoller] Release error: {e}")
            return False

    async def complete_task(self, task_id: str, agent_id: str, evidence: str = None) -> bool:
        """
        Mark task as completed with optional evidence.

        Per RULE-028: CRITICAL/HIGH tasks require evidence.

        Args:
            task_id: Task to complete
            agent_id: Agent that completed task
            evidence: Optional evidence string (required for CRITICAL/HIGH)

        Returns:
            True if completion recorded
        """
        try:
            result = self._client.update_task_status(
                task_id=task_id,
                status="completed",
                agent_id=agent_id,
                evidence=evidence
            )
            return result is not None
        except Exception as e:
            print(f"[TypeDBTaskPoller] Complete error: {e}")
            return False

    async def start_polling(
        self,
        callback: Callable[[PollableTask], None] = None,
        interval: float = None
    ) -> None:
        """
        Start continuous polling.

        Args:
            callback: Optional callback for each task found
            interval: Override default poll interval
        """
        if self._running:
            return

        if callback:
            self.add_callback(callback)

        if interval:
            self._poll_interval = interval

        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop_polling(self) -> None:
        """Stop continuous polling."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

    async def _poll_loop(self) -> None:
        """Internal polling loop."""
        while self._running:
            tasks = await self.poll_once()

            # Notify callbacks for each task
            for task in tasks:
                for callback in self._callbacks:
                    try:
                        callback(task)
                    except Exception as e:
                        print(f"[TypeDBTaskPoller] Callback error: {e}")

            await asyncio.sleep(self._poll_interval)


# =============================================================================
# Convenience Functions
# =============================================================================

def create_poller_from_env() -> TypeDBTaskPoller:
    """Create poller using environment configuration."""
    from governance.client import TypeDBClient

    client = TypeDBClient()
    if client.connect():
        return TypeDBTaskPoller(client)
    else:
        raise ConnectionError("Failed to connect to TypeDB")
