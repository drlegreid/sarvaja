"""
Task UI Module for Sim.ai Agent Platform
=========================================
Implements AG-UI protocol for task submission, progress streaming, and results.

Per RULE-019: UI/UX Design Standards
Per Phase 6.1: Enhance Agno Playground with task input/progress

AG-UI Events:
- RUN_STARTED: Task accepted, run_id assigned
- TEXT_MESSAGE: Agent text output
- TOOL_CALL_START: Tool execution beginning
- TOOL_CALL_END: Tool execution complete
- STATE_DELTA: Progress/state updates
- RUN_FINISHED: Task complete
- RUN_ERROR: Task failed
"""

import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Optional
from dataclasses import dataclass, field, asdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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
                # Send heartbeat to keep connection alive
                yield AGUIEvent(
                    type=AGUIEventType.STATE_DELTA,
                    run_id=task_id,
                    data={"heartbeat": True}
                )


# Global store instance
task_store = TaskStore()


# =============================================================================
# TASK EXECUTOR
# =============================================================================

async def execute_task(task: TaskResult, agents: dict):
    """Execute task with AG-UI event streaming.

    Args:
        task: Task to execute
        agents: Dict of available agents by name
    """
    task_id = task.task_id

    # Emit RUN_STARTED
    await task_store.emit_event(task_id, AGUIEvent(
        type=AGUIEventType.RUN_STARTED,
        run_id=task_id,
        data={"agent": task.agent, "prompt": task.prompt}
    ))

    task_store.update_task(task_id, status=TaskStatus.RUNNING)
    start_time = datetime.utcnow()

    try:
        # Get agent
        agent = agents.get(task.agent)
        if not agent:
            raise ValueError(f"Agent '{task.agent}' not found")

        # Emit STATE_DELTA for progress
        await task_store.emit_event(task_id, AGUIEvent(
            type=AGUIEventType.STATE_DELTA,
            run_id=task_id,
            data={"phase": "processing", "progress": 0.1}
        ))

        # Execute agent (Agno Agent.run is synchronous)
        # Run in thread pool to avoid blocking
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                pool,
                lambda: agent.run(task.prompt)
            )

        # Emit TEXT_MESSAGE with response
        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        await task_store.emit_event(task_id, AGUIEvent(
            type=AGUIEventType.TEXT_MESSAGE,
            run_id=task_id,
            data={"role": "assistant", "content": response_text}
        ))

        # Calculate duration
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Update task with result
        task_store.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            response=response_text,
            duration_ms=duration_ms,
            completed_at=end_time.isoformat()
        )

        # Emit RUN_FINISHED
        await task_store.emit_event(task_id, AGUIEvent(
            type=AGUIEventType.RUN_FINISHED,
            run_id=task_id,
            data={"duration_ms": duration_ms, "status": "completed"}
        ))

    except Exception as e:
        # Update task with error
        task_store.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=str(e),
            completed_at=datetime.utcnow().isoformat()
        )

        # Emit RUN_ERROR
        await task_store.emit_event(task_id, AGUIEvent(
            type=AGUIEventType.RUN_ERROR,
            run_id=task_id,
            data={"error": str(e), "error_type": type(e).__name__}
        ))


# =============================================================================
# API ROUTER
# =============================================================================

def create_task_router(agents: dict) -> APIRouter:
    """Create FastAPI router for task endpoints.

    Args:
        agents: Dict of available agents by name

    Returns:
        FastAPI APIRouter with task endpoints
    """
    router = APIRouter(prefix="/tasks", tags=["tasks"])

    @router.post("", response_model=TaskResponse)
    async def submit_task(submission: TaskSubmission):
        """Submit a new task for execution.

        Returns task_id immediately. Use /tasks/{task_id}/events for progress.
        """
        # Validate agent exists
        if submission.agent not in agents:
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{submission.agent}' not found. Available: {list(agents.keys())}"
            )

        # Create task
        task = task_store.create_task(submission)

        if submission.dry_run:
            return TaskResponse(
                task_id=task.task_id,
                status=task.status,
                agent=task.agent,
                created_at=task.created_at,
                message="Dry run - task validated but not executed"
            )

        # Start execution in background
        asyncio.create_task(execute_task(task, agents))

        return TaskResponse(
            task_id=task.task_id,
            status=task.status,
            agent=task.agent,
            created_at=task.created_at,
            message="Task submitted. Use /tasks/{task_id}/events for progress."
        )

    @router.get("/{task_id}", response_model=TaskResult)
    async def get_task(task_id: str):
        """Get task details and result."""
        task = task_store.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return task

    @router.get("/{task_id}/events")
    async def stream_events(task_id: str):
        """Stream AG-UI events for task via Server-Sent Events."""
        task = task_store.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        async def event_generator():
            async for event in task_store.get_events(task_id):
                yield event.to_sse()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    @router.get("", response_model=list[TaskResult])
    async def list_tasks(limit: int = 50):
        """List recent tasks."""
        return task_store.list_tasks(limit)

    return router


# =============================================================================
# INTEGRATION HELPER
# =============================================================================

def integrate_task_ui(app, agents: dict):
    """Integrate task UI into existing FastAPI app.

    Args:
        app: FastAPI application instance
        agents: Dict of agents by name

    Usage:
        from agent.task_ui import integrate_task_ui

        agent_os = AgentOS(agents=agents)
        app = agent_os.get_app()
        integrate_task_ui(app, {a.name: a for a in agents})
    """
    router = create_task_router(agents)
    app.include_router(router)

    # Add CORS for UI development
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
