"""
Ingestion Management Routes.

Per P2-10: Event-driven ingestion with manual trigger and scheduler control.
Per P2-10a: JSONL file watcher status endpoint.

Endpoints:
    POST /ingestion/scan        — Trigger immediate discovery scan
    GET  /ingestion/scheduler   — Get scheduler status
    PUT  /ingestion/scheduler   — Configure scan interval
    GET  /ingestion/watcher     — Get JSONL file watcher status

The existing GET /ingestion/status/{session_id} remains in sessions/detail.py.

Created: 2026-03-19
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Ingestion"])


class SchedulerConfigRequest(BaseModel):
    interval_seconds: int = Field(ge=30, le=86400, description="Scan interval in seconds (30s-24h)")


@router.post("/ingestion/scan")
async def trigger_scan():
    """Trigger an immediate CC session discovery scan.

    Returns the scan result including new projects/sessions found.
    """
    from governance.services.ingestion_scheduler import get_scheduler

    scheduler = get_scheduler()
    if not scheduler.is_running:
        raise HTTPException(
            status_code=503,
            detail="Ingestion scheduler is not running",
        )

    try:
        result = await scheduler.trigger_scan()
        return {
            "status": "completed",
            "result": result.to_dict(),
        }
    except Exception as e:
        logger.error("Manual scan failed: %s", type(e).__name__, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan failed: {type(e).__name__}")


@router.get("/ingestion/scheduler")
def scheduler_status():
    """Get ingestion scheduler status and statistics."""
    from governance.services.ingestion_scheduler import get_scheduler

    scheduler = get_scheduler()
    return scheduler.get_status()


@router.put("/ingestion/scheduler")
def configure_scheduler(config: SchedulerConfigRequest):
    """Update the ingestion scan interval.

    Takes effect on the next scan cycle (does not interrupt a running scan).
    """
    from governance.services.ingestion_scheduler import get_scheduler

    scheduler = get_scheduler()
    old_interval = scheduler.interval
    scheduler.configure(config.interval_seconds)
    return {
        "status": "configured",
        "old_interval_seconds": old_interval,
        "new_interval_seconds": scheduler.interval,
    }


@router.get("/ingestion/watcher")
def watcher_status():
    """Get JSONL file watcher status and statistics.

    Per P2-10a: Event-driven JSONL monitoring for CC sessions.
    """
    from governance.services.claude_watcher import get_claude_watcher

    watcher = get_claude_watcher()
    if watcher is None:
        return {
            "running": False,
            "message": "ClaudeWatcher not initialized",
        }
    return watcher.get_status()
