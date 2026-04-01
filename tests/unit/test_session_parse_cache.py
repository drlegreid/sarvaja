"""TDD tests for Phase 7: SessionParseCache — LRU, mtime invalidation, thread safety, size guard.

BDD Scenarios:
  - Second call hits cache (hit_count increments, no re-parse)
  - File modification invalidates cache (mtime changed)
  - LRU eviction when cache full (max_size=10)
  - Large file returns truncated summary with WARNING
  - Cache stats report hit/miss/eviction counts
  - Thread safety under concurrent access
  - Cache clear resets all entries and stats

Created: 2026-03-26  EPIC-PERF-TELEM-V1 Phase 7
"""
import os
import threading
import time
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Scenario: Second call hits cache
# ---------------------------------------------------------------------------

def test_cache_hit_returns_same_result():
    """Second get() for same key returns cached result without re-parse."""
    from governance.services.cc_session_cache import SessionParseCache

    cache = SessionParseCache(max_size=10)
    data = {"tool_breakdown": {"Read": 5}, "thinking_summary": {"total_chars": 100}}

    cache.put("S1", 2, data, mtime=1000.0)
    result = cache.get("S1", 2, current_mtime=1000.0)

    assert result == data
    assert cache.stats()["hit_count"] == 1
    assert cache.stats()["miss_count"] == 0


def test_cache_miss_returns_none():
    """get() for uncached key returns None and increments miss_count."""
    from governance.services.cc_session_cache import SessionParseCache

    cache = SessionParseCache(max_size=10)
    result = cache.get("S1", 2, current_mtime=1000.0)

    assert result is None
    assert cache.stats()["miss_count"] == 1
    assert cache.stats()["hit_count"] == 0


# ---------------------------------------------------------------------------
# Scenario: File modification invalidates cache
# ---------------------------------------------------------------------------

def test_mtime_change_invalidates_cache():
    """If file mtime changed, cached entry is stale — returns None (miss)."""
    from governance.services.cc_session_cache import SessionParseCache

    cache = SessionParseCache(max_size=10)
    data = {"tool_breakdown": {"Read": 5}}

    cache.put("S1", 2, data, mtime=1000.0)
    result = cache.get("S1", 2, current_mtime=1001.0)  # mtime changed

    assert result is None
    assert cache.stats()["miss_count"] == 1


# ---------------------------------------------------------------------------
# Scenario: LRU eviction when full
# ---------------------------------------------------------------------------

def test_lru_eviction_when_full():
    """When cache is full, oldest entry is evicted on new put()."""
    from governance.services.cc_session_cache import SessionParseCache

    cache = SessionParseCache(max_size=3)

    cache.put("S1", 1, {"data": 1}, mtime=100.0)
    cache.put("S2", 1, {"data": 2}, mtime=100.0)
    cache.put("S3", 1, {"data": 3}, mtime=100.0)

    # Access S1 to make it recently used
    cache.get("S1", 1, current_mtime=100.0)

    # Add S4 — should evict S2 (oldest untouched)
    cache.put("S4", 1, {"data": 4}, mtime=100.0)

    assert cache.get("S2", 1, current_mtime=100.0) is None  # evicted
    assert cache.get("S1", 1, current_mtime=100.0) is not None  # recently used
    assert cache.get("S4", 1, current_mtime=100.0) is not None  # just added
    assert cache.stats()["eviction_count"] >= 1


# ---------------------------------------------------------------------------
# Scenario: Cache stats endpoint
# ---------------------------------------------------------------------------

def test_stats_reports_counts():
    """stats() returns hit_count, miss_count, eviction_count, size."""
    from governance.services.cc_session_cache import SessionParseCache

    cache = SessionParseCache(max_size=10)
    cache.put("S1", 1, {"x": 1}, mtime=1.0)
    cache.get("S1", 1, current_mtime=1.0)  # hit
    cache.get("S2", 1, current_mtime=1.0)  # miss

    stats = cache.stats()
    assert stats["hit_count"] == 1
    assert stats["miss_count"] == 1
    assert stats["eviction_count"] == 0
    assert stats["size"] == 1
    assert stats["max_size"] == 10


# ---------------------------------------------------------------------------
# Scenario: Cache clear
# ---------------------------------------------------------------------------

def test_clear_resets_everything():
    """clear() removes all entries and resets stats."""
    from governance.services.cc_session_cache import SessionParseCache

    cache = SessionParseCache(max_size=10)
    cache.put("S1", 1, {"x": 1}, mtime=1.0)
    cache.get("S1", 1, current_mtime=1.0)

    cache.clear()

    assert cache.get("S1", 1, current_mtime=1.0) is None
    stats = cache.stats()
    assert stats["hit_count"] == 0
    assert stats["size"] == 0


# ---------------------------------------------------------------------------
# Scenario: Thread safety
# ---------------------------------------------------------------------------

def test_thread_safety():
    """Concurrent put/get operations don't corrupt cache."""
    from governance.services.cc_session_cache import SessionParseCache

    cache = SessionParseCache(max_size=50)
    errors = []

    def worker(session_prefix, count):
        try:
            for i in range(count):
                sid = f"{session_prefix}-{i}"
                cache.put(sid, 1, {"data": i}, mtime=1.0)
                cache.get(sid, 1, current_mtime=1.0)
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=worker, args=(f"T{t}", 20))
        for t in range(5)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    stats = cache.stats()
    assert stats["hit_count"] > 0


# ---------------------------------------------------------------------------
# Scenario: Different zoom levels are separate cache entries
# ---------------------------------------------------------------------------

def test_different_zoom_separate_entries():
    """Same session_id with different zoom = different cache entries."""
    from governance.services.cc_session_cache import SessionParseCache

    cache = SessionParseCache(max_size=10)
    cache.put("S1", 1, {"zoom": 1}, mtime=1.0)
    cache.put("S1", 2, {"zoom": 2}, mtime=1.0)

    r1 = cache.get("S1", 1, current_mtime=1.0)
    r2 = cache.get("S1", 2, current_mtime=1.0)

    assert r1["zoom"] == 1
    assert r2["zoom"] == 2


# ---------------------------------------------------------------------------
# Scenario: Size guard — large file returns truncated summary
# ---------------------------------------------------------------------------

def test_size_guard_rejects_large_file():
    """check_size_guard returns True for oversized files (>JSONL_MAX_SIZE_MB)."""
    from governance.services.cc_session_cache import check_size_guard

    # 250MB file, limit 200MB
    assert check_size_guard(250 * 1024 * 1024, max_mb=200) is True


def test_size_guard_allows_normal_file():
    """check_size_guard returns False for files within limit."""
    from governance.services.cc_session_cache import check_size_guard

    # 50MB file, limit 200MB
    assert check_size_guard(50 * 1024 * 1024, max_mb=200) is False


def test_size_guard_env_configurable():
    """JSONL_MAX_SIZE_MB env overrides default."""
    with patch.dict(os.environ, {"JSONL_MAX_SIZE_MB": "100"}):
        from governance.services.cc_session_cache import _get_max_size_mb
        # Need to call the function that reads the env
        assert _get_max_size_mb() == 100


# ---------------------------------------------------------------------------
# Integration: get_session_detail() wiring
# ---------------------------------------------------------------------------

_SVC = "governance.services.cc_session_ingestion"


def _make_tool_use(name="Read"):
    tu = MagicMock()
    tu.name = name
    tu.input_summary = '{"file": "test.py"}'
    tu.is_mcp = False
    tu.tool_use_id = f"tu_{name}"
    return tu


def _make_entry(tool_uses=None, thinking_chars=0, thinking_content=None):
    from datetime import datetime
    entry = MagicMock()
    entry.tool_uses = tool_uses or []
    entry.tool_results = []
    entry.thinking_chars = thinking_chars
    entry.thinking_content = thinking_content
    entry.timestamp = datetime(2026, 3, 26, 10, 0)
    return entry


@patch(f"{_SVC}.parse_log_file")
@patch(f"{_SVC}._find_jsonl_for_session")
@patch(f"{_SVC}.session_service")
def test_get_session_detail_skips_parse_on_cache_hit(mock_svc, mock_find, mock_parse):
    """get_session_detail() does NOT call parse_log_file on second call (cache hit)."""
    from governance.services.cc_session_ingestion import get_session_detail

    mock_svc.get_session.return_value = {"session_id": "S-CACHE", "status": "COMPLETED"}
    mock_find.return_value = "/tmp/cache_test.jsonl"
    mock_parse.return_value = iter([_make_entry(tool_uses=[_make_tool_use("Read")])])

    # First call — cache miss, parse called
    get_session_detail("S-CACHE", zoom=1)
    assert mock_parse.call_count == 1

    # Second call — cache hit, parse NOT called again
    mock_parse.return_value = iter([])  # would return empty if called
    get_session_detail("S-CACHE", zoom=1)
    assert mock_parse.call_count == 1  # still 1, not 2


@patch(f"{_SVC}.parse_log_file")
@patch(f"{_SVC}._find_jsonl_for_session")
@patch(f"{_SVC}.session_service")
def test_get_session_detail_size_guard_returns_truncated(mock_svc, mock_find, mock_parse):
    """get_session_detail() returns truncated=True for files > JSONL_MAX_SIZE_MB."""
    from governance.services.cc_session_ingestion import get_session_detail

    from pathlib import Path as RealPath

    mock_svc.get_session.return_value = {"session_id": "S-BIG", "status": "COMPLETED"}
    mock_path = MagicMock(spec=RealPath)
    mock_stat = MagicMock()
    mock_stat.st_size = 300 * 1024 * 1024  # 300MB
    mock_stat.st_mtime = 1000.0
    mock_path.stat.return_value = mock_stat
    mock_find.return_value = mock_path

    with patch.dict(os.environ, {"JSONL_MAX_SIZE_MB": "200"}):
        result = get_session_detail("S-BIG", zoom=2)

    assert result["truncated"] is True
    assert "300" in result["truncated_reason"]
    mock_parse.assert_not_called()  # should NOT parse oversized file


@patch(f"{_SVC}.parse_log_file")
@patch(f"{_SVC}._find_jsonl_for_session")
@patch(f"{_SVC}.session_service")
def test_get_session_detail_pagination_from_cache(mock_svc, mock_find, mock_parse):
    """Different page/per_page on same session paginate from one cached parse."""
    from governance.services.cc_session_ingestion import get_session_detail

    mock_svc.get_session.return_value = {"session_id": "S-PAGE", "status": "COMPLETED"}
    mock_find.return_value = "/tmp/page_test.jsonl"
    # 5 tool calls
    mock_parse.return_value = iter([
        _make_entry(tool_uses=[_make_tool_use(f"Tool{i}") for i in range(5)])
    ])

    # First call: page=1, per_page=2
    r1 = get_session_detail("S-PAGE", zoom=2, page=1, per_page=2)
    assert len(r1["tool_calls"]) == 2
    assert r1["tool_calls_total"] == 5

    # Second call: page=2, per_page=2 — should use cache, NOT re-parse
    r2 = get_session_detail("S-PAGE", zoom=2, page=2, per_page=2)
    assert len(r2["tool_calls"]) == 2
    assert r2["tool_calls"][0]["name"] != r1["tool_calls"][0]["name"]  # different page
    assert r2["tool_calls_total"] == 5
    assert mock_parse.call_count == 1  # only parsed once
