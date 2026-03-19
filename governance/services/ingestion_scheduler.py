"""
Event-Driven Ingestion Scheduler.

Per P2-10: Replace startup-only auto-ingest with periodic scheduled scans.
New CC sessions are discovered without requiring a container restart.

Configurable via INGESTION_SCAN_INTERVAL env var (seconds, default 300).

Created: 2026-03-19
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from governance.services.cc_session_scanner import (
    discover_cc_projects,
    discover_filesystem_projects,
)
from governance.services.cc_session_ingestion import ingest_all
from governance.services.projects import create_project, get_project
from governance.services.workspace_registry import detect_project_type

logger = logging.getLogger(__name__)

# Default scan interval: 5 minutes
DEFAULT_SCAN_INTERVAL = int(os.environ.get("INGESTION_SCAN_INTERVAL", "300"))
# Minimum allowed interval: 30 seconds
MIN_SCAN_INTERVAL = 30


@dataclass
class ScanResult:
    """Result of a single ingestion scan cycle."""

    projects_created: int = 0
    sessions_ingested: int = 0
    errors: list = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "projects_created": self.projects_created,
            "sessions_ingested": self.sessions_ingested,
            "errors": self.errors[:10],
            "duration_ms": round(self.duration_ms, 1),
            "timestamp": self.timestamp,
        }


def run_discovery_scan() -> ScanResult:
    """Execute one CC session discovery + ingestion cycle.

    This is a synchronous function that reuses the existing discovery pipeline.
    Called from the scheduler's async loop via run_in_executor.
    """
    result = ScanResult(timestamp=datetime.now(timezone.utc).isoformat())
    t0 = time.monotonic()

    try:
        cc_projects = discover_cc_projects()
        if not cc_projects:
            result.duration_ms = (time.monotonic() - t0) * 1000
            return result

        for cc_proj in cc_projects:
            pid = cc_proj["project_id"]

            # Create project if missing
            existing = get_project(pid)
            if not existing:
                proj_path = cc_proj.get("path", "")
                proj_type = "generic"
                try:
                    proj_type = detect_project_type(proj_path)
                except Exception:
                    pass
                create_project(
                    project_id=pid,
                    name=cc_proj["name"],
                    path=proj_path,
                    project_type=proj_type,
                )
                result.projects_created += 1

            # Ingest sessions
            cc_dir = cc_proj.get("cc_directory")
            if cc_dir:
                slug = pid.replace("PROJ-", "").lower()
                try:
                    ingested = ingest_all(
                        directory=Path(cc_dir),
                        project_slug=slug,
                        project_id=pid,
                        dry_run=False,
                    )
                    result.sessions_ingested += len(ingested)
                except Exception as e:
                    result.errors.append(f"ingest {pid}: {type(e).__name__}")

        # Also discover filesystem projects
        try:
            existing_paths = {p.get("path", "") for p in cc_projects}
            existing_ids = {p["project_id"] for p in cc_projects}
            scan_dirs = set()
            for cc_proj in cc_projects:
                p = cc_proj.get("path", "")
                if p:
                    scan_dirs.add(str(Path(p).parent))

            fs_projects = discover_filesystem_projects(
                scan_dirs=list(scan_dirs),
                existing_paths=existing_paths,
                existing_ids=existing_ids,
            )
            for fs_proj in fs_projects:
                existing = get_project(fs_proj["project_id"])
                if not existing:
                    create_project(
                        project_id=fs_proj["project_id"],
                        name=fs_proj["name"],
                        path=fs_proj["path"],
                        project_type=fs_proj.get("project_type", "generic"),
                    )
                    result.projects_created += 1
        except Exception as e:
            result.errors.append(f"fs_discovery: {type(e).__name__}")

    except Exception as e:
        result.errors.append(f"scan: {type(e).__name__}")
        logger.warning("Ingestion scan failed: %s", type(e).__name__, exc_info=True)

    result.duration_ms = (time.monotonic() - t0) * 1000
    return result


class IngestionScheduler:
    """Periodic scheduler for CC session discovery and ingestion.

    Replaces the one-shot startup discovery with a recurring scan loop.
    Uses asyncio.create_task + sleep for lightweight scheduling.
    """

    def __init__(self, interval_seconds: int = DEFAULT_SCAN_INTERVAL):
        self._interval = max(interval_seconds, MIN_SCAN_INTERVAL)
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._scan_count = 0
        self._total_sessions_ingested = 0
        self._total_projects_created = 0
        self._last_result: Optional[ScanResult] = None
        self._started_at: Optional[str] = None

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def is_running(self) -> bool:
        return self._running

    def configure(self, interval_seconds: int) -> None:
        """Update scan interval. Takes effect on next cycle."""
        self._interval = max(interval_seconds, MIN_SCAN_INTERVAL)
        logger.info("Ingestion scheduler interval set to %ds", self._interval)

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """Start the periodic scan loop."""
        if self._running:
            logger.warning("Ingestion scheduler already running")
            return

        self._running = True
        self._started_at = datetime.now(timezone.utc).isoformat()

        if loop is None:
            loop = asyncio.get_running_loop()

        self._task = loop.create_task(self._scan_loop())
        logger.info(
            "Ingestion scheduler started (interval=%ds)", self._interval
        )

    async def stop(self) -> None:
        """Stop the periodic scan loop."""
        if not self._running:
            return

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Ingestion scheduler stopped")

    async def trigger_scan(self) -> ScanResult:
        """Trigger an immediate scan (outside the regular interval)."""
        return await self._execute_scan()

    def get_status(self) -> dict:
        """Return current scheduler status."""
        return {
            "running": self._running,
            "interval_seconds": self._interval,
            "scan_count": self._scan_count,
            "total_sessions_ingested": self._total_sessions_ingested,
            "total_projects_created": self._total_projects_created,
            "started_at": self._started_at,
            "last_scan": self._last_result.to_dict() if self._last_result else None,
        }

    async def _scan_loop(self) -> None:
        """Main loop: run scan, sleep, repeat."""
        # Run first scan immediately (replaces startup one-shot)
        await self._execute_scan()

        while self._running:
            try:
                await asyncio.sleep(self._interval)
                if not self._running:
                    break
                await self._execute_scan()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.error("Scheduler loop error", exc_info=True)
                # Don't crash the loop — wait and retry
                await asyncio.sleep(self._interval)

    async def _execute_scan(self) -> ScanResult:
        """Execute a scan in a thread pool and update stats."""
        import concurrent.futures

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            concurrent.futures.ThreadPoolExecutor(max_workers=1),
            run_discovery_scan,
        )

        self._scan_count += 1
        self._total_sessions_ingested += result.sessions_ingested
        self._total_projects_created += result.projects_created
        self._last_result = result

        if result.sessions_ingested or result.projects_created:
            logger.info(
                "Scan #%d: %d sessions ingested, %d projects created (%.0fms)",
                self._scan_count,
                result.sessions_ingested,
                result.projects_created,
                result.duration_ms,
            )
        else:
            logger.debug(
                "Scan #%d: no new sessions (%.0fms)",
                self._scan_count,
                result.duration_ms,
            )

        return result


# Module-level singleton
_scheduler: Optional[IngestionScheduler] = None


def get_scheduler() -> IngestionScheduler:
    """Get or create the module-level scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = IngestionScheduler()
    return _scheduler
