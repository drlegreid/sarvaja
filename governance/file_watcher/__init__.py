"""
File Watcher Module.

Per GAP-SYNC-AUTO-001: Auto-sync when files change.
Per DOC-SIZE-01-v1: Modular architecture.

Created: 2026-01-21
"""

from governance.file_watcher.handler import DocumentChangeHandler
from governance.file_watcher.queue import FileEventQueue
from governance.file_watcher.watcher import FileWatcher, get_watcher

__all__ = [
    "DocumentChangeHandler",
    "FileEventQueue",
    "FileWatcher",
    "get_watcher",
]
