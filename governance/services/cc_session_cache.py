"""
Session JSONL Parse Cache — LRU with mtime invalidation.

Per EPIC-PERF-TELEM-V1 Phase 7: Avoid re-parsing JSONL files
when /tools, /thoughts, /transcript, /validate hit get_session_detail().
Thread-safe via threading.Lock. Stats for observability.

Created: 2026-03-26
"""

import logging
import os
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def _get_max_size_mb() -> int:
    """Read JSONL_MAX_SIZE_MB from env, default 200."""
    try:
        return int(os.environ.get("JSONL_MAX_SIZE_MB", "200"))
    except (ValueError, TypeError):
        return 200


def check_size_guard(file_size_bytes: int, max_mb: Optional[int] = None) -> bool:
    """Return True if file exceeds the size limit (should skip full parse).

    Args:
        file_size_bytes: File size in bytes.
        max_mb: Override limit in MB. Uses JSONL_MAX_SIZE_MB env if None.
    """
    if max_mb is None:
        max_mb = _get_max_size_mb()
    return file_size_bytes > max_mb * 1024 * 1024


class SessionParseCache:
    """LRU cache for parsed JSONL session data.

    Keys: (session_id, zoom) tuples.
    Invalidation: mtime-based — if JSONL file was modified since cache
    entry was created, the entry is stale.
    Thread-safe: all operations guarded by threading.Lock.
    """

    def __init__(self, max_size: int = 10):
        self._max_size = max_size
        self._lock = threading.Lock()
        self._cache: OrderedDict[Tuple[str, int], _CacheEntry] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0

    def get(
        self, session_id: str, zoom: int, current_mtime: float
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached parse result if valid.

        Returns None on miss or stale entry (mtime changed).
        """
        key = (session_id, zoom)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._miss_count += 1
                return None
            if entry.mtime != current_mtime:
                # File was modified — stale
                del self._cache[key]
                self._miss_count += 1
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hit_count += 1
            return entry.data

    def put(
        self, session_id: str, zoom: int,
        data: Dict[str, Any], mtime: float,
    ) -> None:
        """Store parse result in cache, evicting LRU if full."""
        key = (session_id, zoom)
        with self._lock:
            if key in self._cache:
                # Update existing — move to end
                self._cache[key] = _CacheEntry(data=data, mtime=mtime)
                self._cache.move_to_end(key)
                return
            # Evict LRU if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
                self._eviction_count += 1
            self._cache[key] = _CacheEntry(data=data, mtime=mtime)

    def clear(self) -> None:
        """Remove all entries and reset stats."""
        with self._lock:
            self._cache.clear()
            self._hit_count = 0
            self._miss_count = 0
            self._eviction_count = 0

    def stats(self) -> Dict[str, int]:
        """Return cache statistics."""
        with self._lock:
            return {
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "eviction_count": self._eviction_count,
                "size": len(self._cache),
                "max_size": self._max_size,
            }


class _CacheEntry:
    """Internal cache entry with data and file mtime."""
    __slots__ = ("data", "mtime")

    def __init__(self, data: Dict[str, Any], mtime: float):
        self.data = data
        self.mtime = mtime


# Module-level singleton used by get_session_detail()
_session_cache = SessionParseCache(max_size=10)
