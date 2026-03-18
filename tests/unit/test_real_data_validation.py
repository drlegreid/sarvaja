"""
Real-Data TDD Suite — validate actual CC session JSONL files.

Per RELIABILITY-PLAN-01-v1 P4: Tests run against real Claude Code session
files on disk. Skips gracefully if no CC sessions are available.

This suite validates that the SessionContentValidator produces meaningful
results against real data, not just synthetic test fixtures.
"""
import json
from pathlib import Path

import pytest

from governance.services.session_content_validator import (
    ContentValidationResult,
    validate_session_content,
    _derive_server_from_tool_name,
)


# Discover real CC session JSONL files
_CC_PROJECTS_DIR = Path.home() / ".claude" / "projects"
_REAL_JSONL_FILES = []

if _CC_PROJECTS_DIR.exists():
    for jsonl in _CC_PROJECTS_DIR.rglob("*.jsonl"):
        # Only include files > 1KB (skip empty/trivial sessions)
        if jsonl.stat().st_size > 1024:
            _REAL_JSONL_FILES.append(jsonl)

# Sort by size descending — largest sessions first (most interesting)
_REAL_JSONL_FILES.sort(key=lambda p: p.stat().st_size, reverse=True)

# Cap at 10 files to keep test time reasonable
_REAL_JSONL_FILES = _REAL_JSONL_FILES[:10]


def _skip_if_no_real_data():
    if not _REAL_JSONL_FILES:
        pytest.skip("No real CC session JSONL files found on this machine")


class TestRealDataDiscovery:
    """Verify we can find real CC session data."""

    def test_cc_projects_dir_exists(self):
        """The ~/.claude/projects directory should exist on dev machines."""
        if not _CC_PROJECTS_DIR.exists():
            pytest.skip("~/.claude/projects not found")
        assert _CC_PROJECTS_DIR.is_dir()

    def test_found_real_jsonl_files(self):
        """At least one non-trivial JSONL file should exist."""
        _skip_if_no_real_data()
        assert len(_REAL_JSONL_FILES) >= 1
        # Verify files are actually JSONL (first line parses as JSON)
        with open(_REAL_JSONL_FILES[0]) as f:
            first_line = f.readline().strip()
            if first_line:
                json.loads(first_line)  # Should not raise


class TestRealDataBasicValidation:
    """Run basic validation on real CC session files."""

    def test_largest_session_has_entries(self):
        """Largest session file should have non-zero entries."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        assert result.entry_count > 0, (
            f"Largest session {_REAL_JSONL_FILES[0].name} has 0 entries"
        )

    def test_largest_session_has_messages(self):
        """Largest session should have both user and assistant messages."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        assert result.has_user_messages, "No user messages in largest session"
        assert result.has_assistant_messages, "No assistant messages in largest session"

    def test_largest_session_has_tool_calls(self):
        """Real CC sessions should have tool calls (Read, Write, Bash, etc.)."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        assert result.has_tool_calls, "No tool calls in largest session"
        assert result.tool_calls_total >= 1

    def test_largest_session_has_thinking(self):
        """Real CC sessions should have thinking/reasoning blocks."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        assert result.has_thinking, "No thinking blocks in largest session"
        assert result.thinking_chars_total > 0

    def test_largest_session_is_valid(self):
        """Largest session should pass validation (file exists, parseable)."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        assert result.valid is True

    def test_parse_error_rate_below_5_percent(self):
        """Parse errors should be rare in real sessions (<5% of lines)."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        total_lines = result.entry_count + result.parse_errors
        if total_lines > 0:
            error_rate = result.parse_errors / total_lines
            assert error_rate < 0.05, (
                f"Parse error rate {error_rate:.1%} exceeds 5% "
                f"({result.parse_errors}/{total_lines})"
            )


class TestRealDataToolPairing:
    """Validate tool call/result pairing on real data."""

    def test_tool_pairing_rate_above_90_percent(self):
        """At least 90% of tool calls should have matching results."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        if result.tool_calls_total == 0:
            pytest.skip("No tool calls to check pairing")
        pairing_rate = 1.0 - (result.orphaned_tool_calls / result.tool_calls_total)
        assert pairing_rate >= 0.90, (
            f"Tool pairing rate {pairing_rate:.1%} below 90% "
            f"({result.orphaned_tool_calls} orphaned of {result.tool_calls_total})"
        )

    def test_tool_error_rate_below_20_percent(self):
        """Tool errors should be under 20% of total calls."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        if result.tool_calls_total == 0:
            pytest.skip("No tool calls to check errors")
        error_rate = result.tool_errors / result.tool_calls_total
        assert error_rate < 0.20, (
            f"Tool error rate {error_rate:.1%} exceeds 20% "
            f"({result.tool_errors}/{result.tool_calls_total})"
        )


class TestRealDataMCPMetadata:
    """Validate MCP server metadata on real data."""

    def test_mcp_calls_have_server_attribution(self):
        """MCP calls should have server name (via metadata or name derivation)."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        if result.mcp_calls_total == 0:
            pytest.skip("No MCP calls in this session")
        coverage = result.mcp_calls_with_server / result.mcp_calls_total
        assert coverage >= 0.90, (
            f"MCP server coverage {coverage:.1%} below 90% "
            f"({result.mcp_calls_with_server}/{result.mcp_calls_total})"
        )

    def test_mcp_server_distribution_non_empty(self):
        """MCP calls should map to at least one known server."""
        _skip_if_no_real_data()
        result = validate_session_content(str(_REAL_JSONL_FILES[0]))
        if result.mcp_calls_total == 0:
            pytest.skip("No MCP calls in this session")
        assert len(result.mcp_server_distribution) >= 1
        # Should have recognizable server names
        known_servers = {
            "gov-core", "gov-tasks", "gov-sessions", "gov-agents",
            "claude-mem", "playwright", "rest-api",
        }
        found_servers = set(result.mcp_server_distribution.keys())
        overlap = found_servers & known_servers
        assert len(overlap) >= 1, (
            f"No known servers found. Got: {found_servers}"
        )


class TestRealDataAllFiles:
    """Run validation across all discovered JSONL files."""

    def test_all_files_validate_without_crash(self):
        """Every discovered JSONL file validates without raising exceptions."""
        _skip_if_no_real_data()
        results = []
        for jsonl in _REAL_JSONL_FILES:
            result = validate_session_content(str(jsonl))
            results.append((jsonl.name, result))
        # All should produce a result (no crashes)
        assert len(results) == len(_REAL_JSONL_FILES)
        # At least one should have entries
        has_entries = any(r.entry_count > 0 for _, r in results)
        assert has_entries, "No JSONL files had any valid entries"

    def test_validation_results_serializable(self):
        """All results should be JSON-serializable."""
        _skip_if_no_real_data()
        for jsonl in _REAL_JSONL_FILES[:3]:  # Check first 3
            result = validate_session_content(str(jsonl))
            d = result.to_dict()
            serialized = json.dumps(d)
            assert isinstance(json.loads(serialized), dict)

    def test_aggregate_metrics_report(self):
        """Aggregate metrics across all sessions for visibility."""
        _skip_if_no_real_data()
        total_entries = 0
        total_tool_calls = 0
        total_mcp_calls = 0
        total_thinking = 0
        total_orphaned = 0

        for jsonl in _REAL_JSONL_FILES:
            result = validate_session_content(str(jsonl))
            total_entries += result.entry_count
            total_tool_calls += result.tool_calls_total
            total_mcp_calls += result.mcp_calls_total
            total_thinking += result.thinking_blocks_total
            total_orphaned += result.orphaned_tool_calls

        # Aggregate should be non-trivial
        assert total_entries > 100, f"Only {total_entries} entries across all files"
        assert total_tool_calls > 10, f"Only {total_tool_calls} tool calls"

        # Report for visibility (printed in test output with -v)
        pairing_rate = (
            1.0 - (total_orphaned / total_tool_calls)
            if total_tool_calls > 0 else 1.0
        )
        print(f"\n  Real-Data Validation Report ({len(_REAL_JSONL_FILES)} files):")
        print(f"  Entries: {total_entries:,}")
        print(f"  Tool Calls: {total_tool_calls:,} ({pairing_rate:.1%} paired)")
        print(f"  MCP Calls: {total_mcp_calls:,}")
        print(f"  Thinking Blocks: {total_thinking:,}")
        print(f"  Orphaned Calls: {total_orphaned:,}")
