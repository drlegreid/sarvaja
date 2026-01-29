"""
Robot Framework Library for Session Metrics.

Wraps governance/session_metrics for Robot Framework integration tests.
Per SESSION-METRICS-01-v1.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SessionMetricsLibrary:
    """Robot Framework library for session metrics testing."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self._tmp_dir = None

    # =========================================================================
    # Discovery Tests
    # =========================================================================

    def create_test_log_dir(self) -> str:
        """Create a temp dir with sample JSONL files. Returns path."""
        self._tmp_dir = tempfile.mkdtemp(prefix="session_metrics_test_")
        entries = [
            {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
             "sessionId": "s1", "message": {"role": "user", "content": "hi"}},
            {"type": "assistant", "timestamp": "2026-01-28T10:05:00Z",
             "sessionId": "s1",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [{"type": "text", "text": "hello"},
                                     {"type": "tool_use", "id": "t1",
                                      "name": "Read", "input": {}}]}},
            {"type": "user", "timestamp": "2026-01-28T10:10:00Z",
             "sessionId": "s1", "message": {"role": "user", "content": "bye"}},
            # 40 min gap → new session
            {"type": "user", "timestamp": "2026-01-28T10:50:00Z",
             "sessionId": "s1", "message": {"role": "user", "content": "back"}},
            {"type": "assistant", "timestamp": "2026-01-28T10:55:00Z",
             "sessionId": "s1",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [{"type": "text", "text": "wb"},
                                     {"type": "tool_use", "id": "t2",
                                      "name": "mcp__gov-core__health_check",
                                      "input": {}}]}},
        ]
        log_file = Path(self._tmp_dir) / "test-session.jsonl"
        with open(log_file, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        # Also create an agent file
        agent_file = Path(self._tmp_dir) / "agent-sub.jsonl"
        with open(agent_file, "w") as f:
            f.write(json.dumps(entries[0]) + "\n")

        return self._tmp_dir

    def discover_log_files_count(self, directory: str,
                                 include_agents: bool = True) -> int:
        """Discover log files and return count."""
        from governance.session_metrics.parser import discover_log_files
        files = discover_log_files(Path(directory), include_agents=include_agents)
        return len(files)

    # =========================================================================
    # Parser Tests
    # =========================================================================

    def parse_log_entries_count(self, directory: str) -> int:
        """Parse all main log files and return total entry count."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        files = discover_log_files(Path(directory), include_agents=False)
        count = 0
        for f in files:
            count += sum(1 for _ in parse_log_file(f))
        return count

    def parse_log_tool_names(self, directory: str) -> List[str]:
        """Parse logs and return list of tool names found."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        files = discover_log_files(Path(directory), include_agents=False)
        names = []
        for f in files:
            for entry in parse_log_file(f):
                for tu in entry.tool_uses:
                    names.append(tu.name)
        return names

    # =========================================================================
    # Calculator Tests
    # =========================================================================

    def calculate_metrics_from_dir(self, directory: str,
                                   idle_threshold: int = 30) -> Dict[str, Any]:
        """Parse + calculate metrics, return dict."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file(f)]
        metrics = calculate_metrics(entries, idle_threshold_min=idle_threshold)
        return metrics.to_dict()

    # =========================================================================
    # MCP Tool Tests
    # =========================================================================

    def mcp_tool_with_test_dir(self, directory: str, days: int = 5) -> Dict[str, Any]:
        """Call the MCP tool logic directly with a test directory."""
        from governance.mcp_tools.session_metrics import _resolve_project_dir
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        from governance.session_metrics.calculator import (
            calculate_metrics, filter_entries_by_days,
        )

        log_dir = Path(directory)
        files = discover_log_files(log_dir, include_agents=False)
        entries = [e for f in files for e in parse_log_file(f)]
        filtered = filter_entries_by_days(entries, days=days)
        metrics = calculate_metrics(filtered, idle_threshold_min=30)
        result = metrics.to_dict()
        result["metadata"] = {
            "log_dir": str(log_dir),
            "log_files": [f.name for f in files],
            "total_entries_parsed": len(entries),
            "entries_in_range": len(filtered),
        }
        return result

    # =========================================================================
    # Agent Tests
    # =========================================================================

    def create_agent_test_dir(self) -> str:
        """Create a temp dir with main + agent JSONL files. Returns path."""
        self._agent_dir = tempfile.mkdtemp(prefix="session_agent_test_")
        main_entries = [
            {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
             "sessionId": "s1",
             "message": {"role": "user", "content": "explore"}},
            {"type": "assistant", "timestamp": "2026-01-28T10:01:00Z",
             "sessionId": "s1",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [{"type": "tool_use", "id": "tu1",
                                      "name": "Task", "input": {}}]}},
        ]
        agent_entries = [
            {"type": "assistant", "timestamp": "2026-01-28T10:01:05Z",
             "sessionId": "s1",
             "message": {"role": "assistant", "model": "claude-haiku-3-5-20241022",
                         "content": [{"type": "tool_use", "id": "atu1",
                                      "name": "Grep", "input": {}}]}},
            {"type": "assistant", "timestamp": "2026-01-28T10:02:00Z",
             "sessionId": "s1",
             "message": {"role": "assistant", "model": "claude-haiku-3-5-20241022",
                         "content": [{"type": "text", "text": "Found results."}]}},
        ]
        main_file = Path(self._agent_dir) / "main-session.jsonl"
        agent_file = Path(self._agent_dir) / "agent-explore.jsonl"
        with open(main_file, "w") as f:
            for e in main_entries:
                f.write(json.dumps(e) + "\n")
        with open(agent_file, "w") as f:
            for e in agent_entries:
                f.write(json.dumps(e) + "\n")
        return self._agent_dir

    def agent_metrics_from_dir(self, directory: str) -> Dict[str, Any]:
        """Calculate agent metrics for directory."""
        from governance.session_metrics.agents import calculate_agent_metrics
        return calculate_agent_metrics(Path(directory))

    # =========================================================================
    # Search Tests
    # =========================================================================

    def create_search_test_dir(self) -> str:
        """Create a temp dir with searchable entries. Returns path."""
        self._search_dir = tempfile.mkdtemp(prefix="session_search_test_")
        entries = [
            {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
             "sessionId": "sess-A", "gitBranch": "main",
             "message": {"role": "user", "content": "fix auth bug"}},
            {"type": "assistant", "timestamp": "2026-01-28T10:01:00Z",
             "sessionId": "sess-A", "gitBranch": "main",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [
                             {"type": "text", "text": "I'll fix the authentication issue."},
                             {"type": "tool_use", "id": "t1", "name": "Read",
                              "input": {"file_path": "/src/auth.py"}},
                         ]}},
            {"type": "user", "timestamp": "2026-01-29T14:00:00Z",
             "sessionId": "sess-B", "gitBranch": "feature/dashboard",
             "message": {"role": "user", "content": "add dashboard"}},
            {"type": "assistant", "timestamp": "2026-01-29T14:02:00Z",
             "sessionId": "sess-B", "gitBranch": "feature/dashboard",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [
                             {"type": "text",
                              "text": "DECISION: Using React for the dashboard."},
                         ]}},
        ]
        log_file = Path(self._search_dir) / "search-test.jsonl"
        with open(log_file, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        return self._search_dir

    def search_entries_from_dir(self, directory: str,
                                query: str = "",
                                session_id: str = "",
                                git_branch: str = "") -> List[Dict[str, Any]]:
        """Parse extended + search, return list of result dicts."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file_extended
        from governance.session_metrics.search import search_entries, results_to_dicts
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file_extended(f)]
        results = search_entries(
            entries,
            query=query,
            session_id=session_id or None,
            git_branch=git_branch or None,
        )
        return results_to_dicts(results)

    # =========================================================================
    # Correlation Tests
    # =========================================================================

    def create_correlation_test_dir(self) -> str:
        """Create a temp dir with tool_use → tool_result pairs. Returns path."""
        self._corr_dir = tempfile.mkdtemp(prefix="session_corr_test_")
        entries = [
            {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
             "sessionId": "s1",
             "message": {"role": "user", "content": "hi"}},
            # Assistant with 2 tool_use blocks
            {"type": "assistant", "timestamp": "2026-01-28T10:00:05Z",
             "sessionId": "s1",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [
                             {"type": "tool_use", "id": "tu1",
                              "name": "Read", "input": {}},
                             {"type": "tool_use", "id": "tu2",
                              "name": "mcp__gov-core__health_check",
                              "input": {}},
                         ]}},
            # tool_result for Read (0.5s)
            {"type": "user", "timestamp": "2026-01-28T10:00:05.500Z",
             "sessionId": "s1",
             "message": {"role": "user",
                         "content": [{"type": "tool_result",
                                      "tool_use_id": "tu1",
                                      "content": "file data"}]}},
            # tool_result for MCP health_check (2s, with mcpMeta)
            {"type": "user", "timestamp": "2026-01-28T10:00:07Z",
             "sessionId": "s1",
             "mcpMeta": {"serverName": "gov-core", "tool": "health_check"},
             "message": {"role": "user",
                         "content": [{"type": "tool_result",
                                      "tool_use_id": "tu2",
                                      "content": "ok"}]}},
        ]
        log_file = Path(self._corr_dir) / "correlation-test.jsonl"
        with open(log_file, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        return self._corr_dir

    def correlate_from_dir(self, directory: str) -> List[Dict[str, Any]]:
        """Parse + correlate, return list of dicts."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        from governance.session_metrics.correlation import correlate_tool_calls
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file(f)]
        correlated = correlate_tool_calls(entries)
        return [{"tool_name": c.tool_name, "latency_ms": c.latency_ms,
                 "is_mcp": c.is_mcp, "server_name": c.server_name}
                for c in correlated]

    def summarize_correlation_from_dir(self, directory: str) -> Dict[str, Any]:
        """Parse + correlate + summarize, return summary dict."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        from governance.session_metrics.correlation import (
            correlate_tool_calls, summarize_correlation,
        )
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file(f)]
        correlated = correlate_tool_calls(entries)
        return summarize_correlation(correlated)

    # =========================================================================
    # Error/Retry Tests (GAP-SESSION-METRICS-ERRORS)
    # =========================================================================

    def create_error_test_dir(self) -> str:
        """Create a temp dir with normal + error JSONL entries. Returns path."""
        self._error_dir = tempfile.mkdtemp(prefix="session_error_test_")
        entries = [
            {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
             "sessionId": "sess-001",
             "message": {"role": "user", "content": "hello"}},
            {"type": "assistant", "timestamp": "2026-01-28T10:01:00Z",
             "sessionId": "sess-001",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [{"type": "text", "text": "hi"}]}},
            # API error (500)
            {"type": "assistant", "timestamp": "2026-01-28T10:02:00Z",
             "sessionId": "sess-001",
             "isApiErrorMessage": True,
             "message": {"role": "assistant",
                         "content": "Internal server error (500)"}},
            # Retry succeeds
            {"type": "assistant", "timestamp": "2026-01-28T10:02:30Z",
             "sessionId": "sess-001",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [{"type": "text", "text": "retry ok"}]}},
            # Another API error
            {"type": "assistant", "timestamp": "2026-01-28T10:05:00Z",
             "sessionId": "sess-001",
             "isApiErrorMessage": True,
             "message": {"role": "assistant",
                         "content": "Overloaded (529)"}},
            {"type": "user", "timestamp": "2026-01-28T10:06:00Z",
             "sessionId": "sess-001",
             "message": {"role": "user", "content": "continue"}},
        ]
        log_file = Path(self._error_dir) / "error-test.jsonl"
        with open(log_file, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        return self._error_dir

    def error_metrics_from_dir(self, directory: str) -> Dict[str, Any]:
        """Calculate metrics from error test dir, return dict."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file(f)]
        metrics = calculate_metrics(entries)
        return metrics.to_dict()

    # =========================================================================
    # Temporal Query Tests (GAP-SESSION-METRICS-TEMPORAL)
    # =========================================================================

    def create_temporal_test_dir(self) -> str:
        """Create a temp dir with multi-day JSONL entries. Returns path."""
        self._temporal_dir = tempfile.mkdtemp(prefix="session_temporal_test_")
        entries = [
            {"type": "user", "timestamp": "2026-01-27T09:00:00Z",
             "sessionId": "sess-A", "gitBranch": "main",
             "message": {"role": "user", "content": "morning"}},
            {"type": "assistant", "timestamp": "2026-01-27T09:05:00Z",
             "sessionId": "sess-A", "gitBranch": "main",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [{"type": "text", "text": "Fixing auth bug."},
                                     {"type": "tool_use", "id": "t1",
                                      "name": "Read", "input": {}}]}},
            {"type": "user", "timestamp": "2026-01-28T14:00:00Z",
             "sessionId": "sess-B", "gitBranch": "feature/dash",
             "message": {"role": "user", "content": "afternoon"}},
            {"type": "assistant", "timestamp": "2026-01-28T14:10:00Z",
             "sessionId": "sess-B", "gitBranch": "feature/dash",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [{"type": "text", "text": "Building dashboard."},
                                     {"type": "tool_use", "id": "t2",
                                      "name": "Edit", "input": {}}]}},
        ]
        log_file = Path(self._temporal_dir) / "temporal-test.jsonl"
        with open(log_file, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        return self._temporal_dir

    def query_at_time_from_dir(self, directory: str,
                                target_iso: str,
                                window_minutes: int = 30) -> Dict[str, Any]:
        """Query entries near a time point."""
        from datetime import datetime, timezone
        from governance.session_metrics.parser import discover_log_files, parse_log_file_extended
        from governance.session_metrics.temporal import query_at_time
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file_extended(f)]
        target = datetime.fromisoformat(target_iso)
        return query_at_time(entries, target, window_minutes=window_minutes)

    def activity_timeline_from_dir(self, directory: str) -> List[Dict[str, Any]]:
        """Generate activity timeline from directory."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file_extended
        from governance.session_metrics.temporal import activity_timeline
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file_extended(f)]
        return activity_timeline(entries)

    # =========================================================================
    # Platform Integration Tests (GAP-SESSION-METRICS-PLATFORM)
    # =========================================================================

    def generate_evidence_markdown(self, directory: str) -> str:
        """Generate evidence markdown from log directory metrics."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        from governance.session_metrics.evidence import generate_evidence_markdown
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file(f)]
        metrics = calculate_metrics(entries)
        return generate_evidence_markdown(metrics.to_dict())

    def write_evidence_file_from_dir(self, directory: str) -> str:
        """Generate + write evidence file, return path string."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        from governance.session_metrics.evidence import write_evidence_file
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file(f)]
        metrics = calculate_metrics(entries)
        self._evidence_dir = Path(tempfile.mkdtemp(prefix="session_evidence_test_"))
        path = write_evidence_file(metrics.to_dict(), output_dir=self._evidence_dir)
        return str(path)

    def build_metrics_insert_query(self, directory: str) -> str:
        """Build TypeDB insert query from directory metrics."""
        from governance.session_metrics.parser import discover_log_files, parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        files = discover_log_files(Path(directory), include_agents=False)
        entries = [e for f in files for e in parse_log_file(f)]
        metrics = calculate_metrics(entries)
        return build_metrics_insert_query(
            session_id="SESSION-TEST-METRICS",
            metrics=metrics.to_dict(),
        )

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup_test_dir(self):
        """Remove temp test directories."""
        import shutil
        if self._tmp_dir and Path(self._tmp_dir).exists():
            shutil.rmtree(self._tmp_dir)
            self._tmp_dir = None
        if hasattr(self, "_corr_dir") and self._corr_dir and Path(self._corr_dir).exists():
            shutil.rmtree(self._corr_dir)
            self._corr_dir = None
        if hasattr(self, "_search_dir") and self._search_dir and Path(self._search_dir).exists():
            shutil.rmtree(self._search_dir)
            self._search_dir = None
        if hasattr(self, "_agent_dir") and self._agent_dir and Path(self._agent_dir).exists():
            shutil.rmtree(self._agent_dir)
            self._agent_dir = None
        if hasattr(self, "_error_dir") and self._error_dir and Path(self._error_dir).exists():
            shutil.rmtree(self._error_dir)
            self._error_dir = None
        if hasattr(self, "_evidence_dir") and self._evidence_dir and Path(self._evidence_dir).exists():
            shutil.rmtree(self._evidence_dir)
            self._evidence_dir = None
        if hasattr(self, "_temporal_dir") and self._temporal_dir and Path(self._temporal_dir).exists():
            shutil.rmtree(self._temporal_dir)
            self._temporal_dir = None
