"""
Document Change Handler.

Per GAP-SYNC-AUTO-001: File system event handler.
Per DOC-SIZE-01-v1: File Size Limit (< 300 lines).

Watches for changes to markdown files and queues them for sync.

Created: 2026-01-21
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Set

try:
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object  # type: ignore
    FileSystemEvent = object  # type: ignore

from governance.file_watcher.queue import FileEvent, FileEventType, FileEventQueue


logger = logging.getLogger(__name__)


class DocumentChangeHandler(FileSystemEventHandler):
    """
    Handles file system events for document changes.

    Filters for markdown files and queues events for sync.
    """

    # File extensions to monitor
    WATCHED_EXTENSIONS: Set[str] = {".md", ".yaml", ".yml", ".tql"}

    # Paths to ignore
    IGNORED_PATTERNS: Set[str] = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".claude",
    }

    def __init__(
        self,
        queue: FileEventQueue,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """
        Initialize handler with event queue.

        Args:
            queue: FileEventQueue to add events to
            loop: Event loop for async queue operations
        """
        super().__init__()
        self.queue = queue
        self._loop = loop

    def _should_process(self, path: str) -> bool:
        """Check if file should be processed."""
        path_obj = Path(path)

        # Check extension
        if path_obj.suffix.lower() not in self.WATCHED_EXTENSIONS:
            return False

        # Check ignored patterns
        for part in path_obj.parts:
            if part in self.IGNORED_PATTERNS:
                return False

        return True

    def _queue_event(self, event_type: FileEventType, path: str) -> None:
        """Queue event for processing."""
        if not self._should_process(path):
            return

        file_event = FileEvent(
            path=path,
            event_type=event_type,
            category=FileEvent.categorize(path),
        )

        # Run async add in event loop
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.queue.add_event(file_event),
                self._loop
            )
        else:
            # Fallback for sync context
            try:
                asyncio.run(self.queue.add_event(file_event))
            except RuntimeError:
                # Event loop already running - create task
                asyncio.create_task(self.queue.add_event(file_event))

        logger.debug(f"Queued {event_type.value}: {path}")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation."""
        if event.is_directory:
            return
        self._queue_event(FileEventType.CREATED, event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification."""
        if event.is_directory:
            return
        self._queue_event(FileEventType.MODIFIED, event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion."""
        if event.is_directory:
            return
        self._queue_event(FileEventType.DELETED, event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move/rename."""
        if event.is_directory:
            return
        # Treat as delete + create
        self._queue_event(FileEventType.DELETED, event.src_path)
        if hasattr(event, 'dest_path'):
            self._queue_event(FileEventType.CREATED, event.dest_path)
