"""
TDD Test Spec: Session Metrics Agent Subprocess Analytics
==========================================================
Per GAP-SESSION-METRICS-AGENTS: Agent subprocess analytics
with parent attribution and aggregate metrics.

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_session_metrics_agents.py -v
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures: synthetic agent subprocess JSONL files
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_log_dir(tmp_path):
    """Directory with main log + 2 agent subprocess logs."""
    # Main session log
    main_entries = [
        {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
         "sessionId": "sess-001",
         "message": {"role": "user", "content": "explore codebase"}},
        {"type": "assistant", "timestamp": "2026-01-28T10:01:00Z",
         "sessionId": "sess-001",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "Launching agent..."},
                         {"type": "tool_use", "id": "tu1", "name": "Task",
                          "input": {"description": "explore"}},
                     ]}},
        {"type": "assistant", "timestamp": "2026-01-28T10:05:00Z",
         "sessionId": "sess-001",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "Agent found 10 files."},
                     ]}},
    ]
    # Agent 1: 2 minutes active, 3 tool calls
    agent1_entries = [
        {"type": "assistant", "timestamp": "2026-01-28T10:01:05Z",
         "sessionId": "sess-001", "parentToolUseID": "tu1",
         "isSidechain": True,
         "message": {"role": "assistant", "model": "claude-haiku-3-5-20241022",
                     "content": [
                         {"type": "tool_use", "id": "atu1", "name": "Glob",
                          "input": {"pattern": "**/*.py"}},
                     ]}},
        {"type": "user", "timestamp": "2026-01-28T10:01:10Z",
         "sessionId": "sess-001",
         "message": {"role": "user",
                     "content": [{"type": "tool_result", "tool_use_id": "atu1",
                                  "content": "src/main.py\nsrc/utils.py"}]}},
        {"type": "assistant", "timestamp": "2026-01-28T10:02:00Z",
         "sessionId": "sess-001",
         "message": {"role": "assistant", "model": "claude-haiku-3-5-20241022",
                     "content": [
                         {"type": "tool_use", "id": "atu2", "name": "Read",
                          "input": {"file_path": "src/main.py"}},
                         {"type": "tool_use", "id": "atu3", "name": "Grep",
                          "input": {"pattern": "class"}},
                     ]}},
        {"type": "assistant", "timestamp": "2026-01-28T10:03:00Z",
         "sessionId": "sess-001",
         "message": {"role": "assistant", "model": "claude-haiku-3-5-20241022",
                     "content": [{"type": "text", "text": "Found 10 files."}]}},
    ]
    # Agent 2: 1 minute active, 1 tool call
    agent2_entries = [
        {"type": "assistant", "timestamp": "2026-01-28T10:05:05Z",
         "sessionId": "sess-001", "parentToolUseID": "tu2",
         "isSidechain": True,
         "message": {"role": "assistant", "model": "claude-haiku-3-5-20241022",
                     "content": [
                         {"type": "tool_use", "id": "btu1", "name": "Read",
                          "input": {"file_path": "README.md"}},
                     ]}},
        {"type": "assistant", "timestamp": "2026-01-28T10:06:00Z",
         "sessionId": "sess-001",
         "message": {"role": "assistant", "model": "claude-haiku-3-5-20241022",
                     "content": [{"type": "text", "text": "Done."}]}},
    ]

    main_file = tmp_path / "main-session.jsonl"
    agent1_file = tmp_path / "agent-explore.jsonl"
    agent2_file = tmp_path / "agent-read.jsonl"

    for filepath, entries in [
        (main_file, main_entries),
        (agent1_file, agent1_entries),
        (agent2_file, agent2_entries),
    ]:
        with open(filepath, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

    return tmp_path


# ---------------------------------------------------------------------------
# Tests: Agent file discovery
# ---------------------------------------------------------------------------

class TestAgentDiscovery:
    """Test discovering agent subprocess log files."""

    def test_discover_agent_files(self, agent_log_dir):
        """Discover agent-*.jsonl files in directory."""
        from governance.session_metrics.parser import discover_log_files
        all_files = discover_log_files(agent_log_dir, include_agents=True)
        agent_files = [f for f in all_files if f.name.startswith("agent-")]
        assert len(agent_files) == 2

    def test_discover_main_excludes_agents(self, agent_log_dir):
        """Main discovery excludes agent files."""
        from governance.session_metrics.parser import discover_log_files
        main_files = discover_log_files(agent_log_dir, include_agents=False)
        assert len(main_files) == 1
        assert not any(f.name.startswith("agent-") for f in main_files)


# ---------------------------------------------------------------------------
# Tests: Agent metrics calculation
# ---------------------------------------------------------------------------

class TestAgentMetrics:
    """Test calculating metrics for agent subprocesses."""

    def test_agent_summary_counts_agents(self, agent_log_dir):
        """Agent summary counts number of agent files."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        assert result["agent_count"] == 2

    def test_agent_summary_total_entries(self, agent_log_dir):
        """Agent summary has total entry count across agents."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        assert result["total_entries"] == 6  # 4 + 2

    def test_agent_summary_total_tool_calls(self, agent_log_dir):
        """Agent summary counts tool calls across agents."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        assert result["total_tool_calls"] == 4  # 3 + 1

    def test_agent_summary_total_active_minutes(self, agent_log_dir):
        """Agent summary calculates active minutes across agents."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        # Agent 1: 10:01:05 → 10:03:00 ≈ 1 min, Agent 2: 10:05:05 → 10:06:00 ≈ 0 min
        assert result["total_active_minutes"] >= 1

    def test_agent_per_file_breakdown(self, agent_log_dir):
        """Agent summary has per-file breakdown."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        assert "per_agent" in result
        assert len(result["per_agent"]) == 2

    def test_agent_per_file_has_name(self, agent_log_dir):
        """Per-agent breakdown has file name."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        names = {a["file_name"] for a in result["per_agent"]}
        assert "agent-explore.jsonl" in names
        assert "agent-read.jsonl" in names

    def test_agent_per_file_has_tool_calls(self, agent_log_dir):
        """Per-agent breakdown has tool call count."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        agent_map = {a["file_name"]: a for a in result["per_agent"]}
        assert agent_map["agent-explore.jsonl"]["tool_calls"] == 3
        assert agent_map["agent-read.jsonl"]["tool_calls"] == 1

    def test_agent_tool_breakdown(self, agent_log_dir):
        """Agent summary has tool breakdown across all agents."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        assert "tool_breakdown" in result
        assert result["tool_breakdown"]["Glob"] == 1
        assert result["tool_breakdown"]["Read"] == 2  # 1 from each agent

    def test_agent_model_breakdown(self, agent_log_dir):
        """Agent summary has model usage breakdown."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        assert "model_breakdown" in result
        assert "claude-haiku-3-5-20241022" in result["model_breakdown"]

    def test_agent_empty_dir(self, tmp_path):
        """Empty directory returns zero counts."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(tmp_path)
        assert result["agent_count"] == 0
        assert result["total_entries"] == 0

    def test_agent_serializable(self, agent_log_dir):
        """Agent metrics are JSON-serializable."""
        from governance.session_metrics.agents import calculate_agent_metrics
        result = calculate_agent_metrics(agent_log_dir)
        json.dumps(result)  # Should not raise
