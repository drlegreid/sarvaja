"""
AG-UI Task Models & Store.

Per DOC-SIZE-01-v1: Extracted from task_ui.py (397 lines).
Event types, data models, and in-memory task store.
"""

import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Optional
from dataclasses import dataclass, field

from pydantic import BaseModel, Field


# =============================================================================
# AG-UI EVENT TYPES
# =============================================================================

class AGUIEventType(str, Enum):
    """AG-UI protocol event types."""
    RUN_STARTED = "RUN_STARTED"
    TEXT_MESSAGE = "TEXT_MESSAGE"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_END = "TOOL_CALL_END"
    STATE_DELTA = "STATE_DELTA"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"


class TaskStatus(str, Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# DATA MODELS
# =============================================================================

class TaskSubmission(BaseModel):
    """Task submission request."""
    prompt: str = Field(..., min_length=1, description="Task prompt/instruction")
    agent: str = Field(default="orchestrator", description="Target agent name")
    context: Optional[dict] = Field(default=None, description="Additional context")
    dry_run: bool = Field(default=False, description="Validate without executing")


class TaskResponse(BaseModel):
    """Task submission response."""
    task_id: str
    status: TaskStatus
    agent: str
    created_at: str
    message: str


class TaskResult(BaseModel):
    """Task execution result."""
    task_id: str
    status: TaskStatus
    agent: str
    prompt: str
    response: Optional[str] = None
    tool_calls: list[dict] = Field(default_factory=list)
    duration_ms: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AGUIEvent:
    """AG-UI protocol event."""
    type: AGUIEventType
    run_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    data: dict = field(default_factory=dict)

    def to_sse(self) -> str:
        """Convert to Server-Sent Events format."""
        payload = {
            "type": self.type.value,
            "runId": self.run_id,
            "timestamp": self.timestamp,
            **self.data
        }
        return f"data: {json.dumps(payload)}\n\n"


# =============================================================================
# TASK STORE (In-Memory for PoC)
# =============================================================================

class TaskStore:
    """In-memory task storage for PoC. Replace with persistence for production."""

    def __init__(self):
        self._tasks: dict[str, TaskResult] = {}
        self._event_queues: dict[str, asyncio.Queue] = {}

    def create_task(self, submission: TaskSubmission) -> TaskResult:
        """Create a new task."""
        task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow().isoformat()

        task = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            agent=submission.agent,
            prompt=submission.prompt,
            created_at=now,
        )
        self._tasks[task_id] = task
        self._event_queues[task_id] = asyncio.Queue()
        return task

    def get_task(self, task_id: str) -> Optional[TaskResult]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def update_task(self, task_id: str, **updates) -> Optional[TaskResult]:
        """Update task fields."""
        task = self._tasks.get(task_id)
        if task:
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
        return task

    def list_tasks(self, limit: int = 50) -> list[TaskResult]:
        """List recent tasks."""
        tasks = list(self._tasks.values())
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    async def emit_event(self, task_id: str, event: AGUIEvent):
        """Emit AG-UI event for task."""
        queue = self._event_queues.get(task_id)
        if queue:
            await queue.put(event)

    async def get_events(self, task_id: str) -> AsyncGenerator[AGUIEvent, None]:
        """Stream AG-UI events for task."""
        queue = self._event_queues.get(task_id)
        if not queue:
            return

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield event
                if event.type in (AGUIEventType.RUN_FINISHED, AGUIEventType.RUN_ERROR):
                    break
            except asyncio.TimeoutError:
                yield AGUIEvent(
                    type=AGUIEventType.STATE_DELTA,
                    run_id=task_id,
                    data={"heartbeat": True}
                )


# Global store instance
task_store = TaskStore()
