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
    # Cleanup
    # =========================================================================

    def cleanup_test_dir(self):
        """Remove temp test directory."""
        import shutil
        if self._tmp_dir and Path(self._tmp_dir).exists():
            shutil.rmtree(self._tmp_dir)
            self._tmp_dir = None
