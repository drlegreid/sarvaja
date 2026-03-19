"""
Claude Watcher — event-driven JSONL file monitor for CC session ingestion.

Per P2-10a / SESSION-EVENT-01-v1: Watch ~/.claude/projects/**/*.jsonl for
new/modified files and trigger session ingestion on the fly.

Architecture:
  - JsonlChangeHandler: watchdog event handler, filters to *.jsonl
  - ClaudeWatcher: coordinator with debouncing + async ingestion dispatch
  - ingest_single_session(): scan metadata + create/update session entity

Event-driven primary, periodic IngestionScheduler as fallback/reconciliation.

Created: 2026-03-19
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore
    FileSystemEvent = object  # type: ignore

from governance.services.cc_session_scanner import (
    scan_jsonl_metadata,
    build_session_id,
    derive_project_slug,
    DEFAULT_CC_DIR,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Single-session ingestion (reusable outside the watcher)
# ---------------------------------------------------------------------------


def ingest_single_session(
    jsonl_path: Path,
    project_slug: str,
    project_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Scan a single JSONL file and create/update the session entity.

    Returns the session dict on success, None if file is empty/invalid.
    Skips creation if session already exists (idempotent).
    """
    meta = scan_jsonl_metadata(jsonl_path)
    if not meta:
        return None

    session_id = build_session_id(meta, project_slug)

    # Check if session already exists
    try:
        from governance.services.sessions import get_session
        existing = get_session(session_id)
        if existing:
            logger.debug("Session %s already exists, skipping create", session_id)
            return existing
    except Exception:
        pass  # Service layer may not be available

    # Derive project_id from slug if not provided
    if not project_id:
        project_id = f"PROJ-{project_slug.upper()}"

    # Check project exists
    try:
        from governance.services.projects import get_project
        get_project(project_id)
    except Exception:
        pass

    # Create session entity
    try:
        from governance.services.sessions import create_session
        session_data = {
            "session_id": session_id,
            "topic": meta.get("slug", "unknown"),
            "session_type": "cc",
            "status": "COMPLETED",
            "start_time": meta.get("first_ts", ""),
            "end_time": meta.get("last_ts", ""),
            "source": "cc",
            "cc_session_uuid": meta.get("session_uuid", ""),
            "project_id": project_id,
            "tool_count": meta.get("tool_use_count", 0),
            "thinking_chars": meta.get("thinking_chars", 0),
            "user_count": meta.get("user_count", 0),
            "assistant_count": meta.get("assistant_count", 0),
            "models": meta.get("models", []),
            "jsonl_path": str(jsonl_path),
            "file_size": meta.get("file_size", 0),
        }
        result = create_session(**session_data)
        logger.info("Ingested session %s from %s", session_id, jsonl_path.name)
        return result
    except Exception as e:
        logger.warning(
            "Failed to create session %s: %s", session_id, type(e).__name__,
            exc_info=True,
        )
        return {"session_id": session_id, "error": str(e)}


# ---------------------------------------------------------------------------
# JsonlChangeHandler — watchdog event handler
# ---------------------------------------------------------------------------


class JsonlChangeHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Watchdog handler that filters for *.jsonl file events."""

    def __init__(self, on_change_callback):
        """
        Args:
            on_change_callback: callable(path: str, event_type: str)
        """
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self._callback = on_change_callback

    def _should_process(self, path: str) -> bool:
        """Only process *.jsonl files, skip dotfiles and tmp files."""
        p = Path(path)
        if p.suffix != ".jsonl":
            return False
        if p.name.startswith("."):
            return False
        # Skip editor swap/tmp files
        if any(p.name.endswith(ext) for ext in (".tmp", ".swp", ".bak")):
            return False
        return True

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        if self._should_process(event.src_path):
            self._callback(event.src_path, "created")

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        if self._should_process(event.src_path):
            self._callback(event.src_path, "modified")


# ---------------------------------------------------------------------------
# ClaudeWatcher — coordinator
# ---------------------------------------------------------------------------


class ClaudeWatcher:
    """Event-driven JSONL file watcher for CC session ingestion.

    Monitors a directory tree (default: ~/.claude/projects/) for *.jsonl
    changes. Debounces rapid events and triggers single-session ingestion.
    """

    def __init__(
        self,
        watch_path: Optional[str] = None,
        debounce_seconds: float = 3.0,
    ):
        self.watch_path = Path(watch_path) if watch_path else DEFAULT_CC_DIR
        self.debounce_seconds = debounce_seconds

        self._observer = None
        self._handler = None
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

        # Debounce state: {path: last_event_time}
        self._pending: Dict[str, float] = {}
        self._pending_types: Dict[str, str] = {}

        # Stats
        self._stats = {
            "events_processed": 0,
            "sessions_ingested": 0,
            "errors": 0,
            "started_at": None,
        }

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> bool:
        """Start watching for JSONL file changes."""
        if not WATCHDOG_AVAILABLE:
            logger.error("watchdog library not installed — cannot start ClaudeWatcher")
            return False

        if self._running:
            logger.debug("ClaudeWatcher already running")
            return True

        try:
            self._handler = JsonlChangeHandler(self._on_jsonl_change)
            self._observer = Observer()
            self._observer.schedule(
                self._handler,
                str(self.watch_path),
                recursive=True,
            )
            self._observer.start()
            self._running = True
            self._stats["started_at"] = time.time()

            # Start async worker for debounce processing
            self._worker_task = asyncio.create_task(self._worker_loop())

            logger.info("ClaudeWatcher started: %s (debounce=%.1fs)",
                        self.watch_path, self.debounce_seconds)
            return True

        except Exception as e:
            logger.error("ClaudeWatcher start failed: %s", type(e).__name__,
                         exc_info=True)
            self._running = False
            return False

    async def stop(self) -> None:
        """Stop watching."""
        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None

        logger.info("ClaudeWatcher stopped")

    def _on_jsonl_change(self, path: str, event_type: str) -> None:
        """Callback from JsonlChangeHandler — records event for debouncing."""
        self._pending[path] = time.time()
        self._pending_types[path] = event_type
        logger.debug("JSONL event: %s %s", event_type, Path(path).name)

    async def _worker_loop(self) -> None:
        """Background task: periodically process debounced events."""
        while self._running:
            try:
                await asyncio.sleep(1.0)
                await self._process_pending()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.error("ClaudeWatcher worker error", exc_info=True)
                self._stats["errors"] += 1

    async def _process_pending(self) -> None:
        """Process any pending events whose debounce period has elapsed."""
        if not self._pending:
            return

        now = time.time()
        ready = [
            path for path, ts in self._pending.items()
            if now - ts >= self.debounce_seconds
        ]

        for path in ready:
            self._pending.pop(path, None)
            event_type = self._pending_types.pop(path, "unknown")
            await self._ingest_file(path, event_type)

    async def _ingest_file(self, path: str, event_type: str) -> None:
        """Run single-session ingestion in a thread pool."""
        import concurrent.futures

        self._stats["events_processed"] += 1

        jsonl_path = Path(path)
        if not jsonl_path.exists():
            logger.debug("File vanished before ingestion: %s", jsonl_path.name)
            return

        # Derive project slug from parent directory name
        project_slug = derive_project_slug(jsonl_path.parent)

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                concurrent.futures.ThreadPoolExecutor(max_workers=1),
                lambda: ingest_single_session(jsonl_path, project_slug),
            )

            if result and "error" not in result:
                self._stats["sessions_ingested"] += 1
                logger.info("Watcher ingested: %s (%s)", result.get("session_id", "?"), event_type)
            elif result and "error" in result:
                self._stats["errors"] += 1

        except Exception as e:
            self._stats["errors"] += 1
            logger.warning("Watcher ingest failed for %s: %s",
                           jsonl_path.name, type(e).__name__, exc_info=True)

    def get_status(self) -> dict:
        """Return watcher status for API/monitoring."""
        return {
            "running": self._running,
            "watch_path": str(self.watch_path),
            "debounce_seconds": self.debounce_seconds,
            "events_processed": self._stats["events_processed"],
            "sessions_ingested": self._stats["sessions_ingested"],
            "errors": self._stats["errors"],
            "pending_events": len(self._pending),
            "started_at": self._stats["started_at"],
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_watcher_instance: Optional[ClaudeWatcher] = None


def get_claude_watcher(
    watch_path: Optional[str] = None,
    debounce_seconds: float = 3.0,
) -> Optional[ClaudeWatcher]:
    """Get or create the global ClaudeWatcher singleton.

    Args:
        watch_path: Directory to watch (required on first call).
        debounce_seconds: Seconds to wait before processing a file event.

    Returns:
        ClaudeWatcher instance, or None if not yet initialized.
    """
    global _watcher_instance

    if _watcher_instance is None and watch_path:
        _watcher_instance = ClaudeWatcher(
            watch_path=watch_path,
            debounce_seconds=debounce_seconds,
        )

    return _watcher_instance


def reset_claude_watcher() -> None:
    """Reset the singleton (for testing)."""
    global _watcher_instance
    _watcher_instance = None
