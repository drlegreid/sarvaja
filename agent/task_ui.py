"""
Task UI Module for Sarvaja Agent Platform
==========================================
Implements AG-UI protocol for task submission, progress streaming, and results.

Per RULE-019: UI/UX Design Standards
Per Phase 6.1: Enhance Agno Playground with task input/progress
Per DOC-SIZE-01-v1: Models & store in task_ui_models.py.
"""

import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

# Re-export models for backward compatibility
from .task_ui_models import (  # noqa: F401
    AGUIEventType,
    TaskStatus,
    TaskSubmission,
    TaskResponse,
    TaskResult,
    AGUIEvent,
    TaskStore,
    task_store,
)


# =============================================================================
# TASK EXECUTOR
# =============================================================================

async def execute_task(task: TaskResult, agents: dict):
    """Execute task with AG-UI event streaming."""
    task_id = task.task_id

    await task_store.emit_event(task_id, AGUIEvent(
        type=AGUIEventType.RUN_STARTED,
        run_id=task_id,
        data={"agent": task.agent, "prompt": task.prompt}
    ))

    task_store.update_task(task_id, status=TaskStatus.RUNNING)
    start_time = datetime.utcnow()

    try:
        agent = agents.get(task.agent)
        if not agent:
            raise ValueError(f"Agent '{task.agent}' not found")

        await task_store.emit_event(task_id, AGUIEvent(
            type=AGUIEventType.STATE_DELTA,
            run_id=task_id,
            data={"phase": "processing", "progress": 0.1}
        ))

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                pool,
                lambda: agent.run(task.prompt)
            )

        response_text = str(response.content) if hasattr(response, 'content') else str(response)
        await task_store.emit_event(task_id, AGUIEvent(
            type=AGUIEventType.TEXT_MESSAGE,
            run_id=task_id,
            data={"role": "assistant", "content": response_text}
        ))

        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        task_store.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            response=response_text,
            duration_ms=duration_ms,
            completed_at=end_time.isoformat()
        )

        await task_store.emit_event(task_id, AGUIEvent(
            type=AGUIEventType.RUN_FINISHED,
            run_id=task_id,
            data={"duration_ms": duration_ms, "status": "completed"}
        ))

    except Exception as e:
        task_store.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=str(e),
            completed_at=datetime.utcnow().isoformat()
        )

        await task_store.emit_event(task_id, AGUIEvent(
            type=AGUIEventType.RUN_ERROR,
            run_id=task_id,
            data={"error": str(e), "error_type": type(e).__name__}
        ))


# =============================================================================
# API ROUTER
# =============================================================================

def create_task_router(agents: dict) -> APIRouter:
    """Create FastAPI router for task endpoints."""
    router = APIRouter(prefix="/tasks", tags=["tasks"])

    @router.post("", response_model=TaskResponse)
    async def submit_task(submission: TaskSubmission):
        """Submit a new task for execution."""
        if submission.agent not in agents:
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{submission.agent}' not found. Available: {list(agents.keys())}"
            )

        task = task_store.create_task(submission)

        if submission.dry_run:
            return TaskResponse(
                task_id=task.task_id,
                status=task.status,
                agent=task.agent,
                created_at=task.created_at,
                message="Dry run - task validated but not executed"
            )

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
                "X-Accel-Buffering": "no",
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
    """Integrate task UI into existing FastAPI app."""
    router = create_task_router(agents)
    app.include_router(router)

    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
