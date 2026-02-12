"""
Unit tests for Agent Task Backlog State.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/backlog.py module.
Tests: with_available_tasks, with_claimed_tasks, with_selected_task,
       with_current_agent, get_task_status_color, format_backlog_task.
"""

import pytest

from agent.governance_ui.state.backlog import (
    with_available_tasks,
    with_claimed_tasks,
    with_selected_task,
    with_current_agent,
    get_task_status_color,
    format_backlog_task,
)


# ── with_available_tasks ───────────────────────────────────────


class TestWithAvailableTasks:
    def test_adds_tasks(self):
        state = {"foo": "bar"}
        tasks = [{"task_id": "T-1"}]
        result = with_available_tasks(state, tasks)
        assert result["available_tasks"] == tasks
        assert result["foo"] == "bar"

    def test_immutable(self):
        state = {"foo": "bar"}
        result = with_available_tasks(state, [])
        assert "available_tasks" not in state
        assert result is not state


# ── with_claimed_tasks ─────────────────────────────────────────


class TestWithClaimedTasks:
    def test_adds_claimed(self):
        state = {}
        tasks = [{"task_id": "T-1", "agent_id": "a1"}]
        result = with_claimed_tasks(state, tasks)
        assert result["claimed_tasks"] == tasks

    def test_immutable(self):
        state = {"x": 1}
        result = with_claimed_tasks(state, [])
        assert result is not state


# ── with_selected_task ─────────────────────────────────────────


class TestWithSelectedTask:
    def test_select_task(self):
        state = {}
        task = {"task_id": "T-1", "status": "OPEN"}
        result = with_selected_task(state, task)
        assert result["selected_task"] == task
        assert result["show_task_detail"] is True

    def test_deselect(self):
        state = {"selected_task": {"task_id": "T-1"}}
        result = with_selected_task(state, None)
        assert result["selected_task"] is None
        assert result["show_task_detail"] is False


# ── with_current_agent ─────────────────────────────────────────


class TestWithCurrentAgent:
    def test_set_agent(self):
        state = {}
        result = with_current_agent(state, "agent-1")
        assert result["current_agent_id"] == "agent-1"

    def test_clear_agent(self):
        state = {"current_agent_id": "agent-1"}
        result = with_current_agent(state, None)
        assert result["current_agent_id"] is None


# ── get_task_status_color ──────────────────────────────────────


class TestGetTaskStatusColor:
    def test_known_statuses(self):
        # Test a few known statuses — exact colors depend on constants
        result = get_task_status_color("TODO")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_status_grey(self):
        result = get_task_status_color("NONEXISTENT")
        assert result == "grey"

    def test_case_insensitive(self):
        upper = get_task_status_color("TODO")
        lower = get_task_status_color("todo")
        assert upper == lower


# ── format_backlog_task ────────────────────────────────────────


class TestFormatBacklogTask:
    def test_formats_full_task(self):
        task = {
            "task_id": "T-1",
            "description": "Do thing",
            "body": "Details",
            "phase": "P10",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "claimed_at": "2026-02-11T10:00:00",
            "completed_at": None,
            "linked_rules": ["R-1"],
            "linked_sessions": ["S-1"],
            "gap_id": "GAP-001",
            "evidence": "Tests pass",
        }
        result = format_backlog_task(task)
        assert result["task_id"] == "T-1"
        assert result["description"] == "Do thing"
        assert result["phase"] == "P10"
        assert result["status"] == "IN_PROGRESS"
        assert isinstance(result["status_color"], str)
        assert result["agent_id"] == "code-agent"
        assert result["gap_id"] == "GAP-001"
        assert result["linked_rules"] == ["R-1"]

    def test_formats_minimal_task(self):
        task = {}
        result = format_backlog_task(task)
        assert result["task_id"] == "Unknown"
        assert result["description"] == ""
        assert result["status"] == "TODO"
        assert result["agent_id"] is None
        assert result["linked_rules"] == []
        assert result["linked_sessions"] == []

    def test_status_color_applied(self):
        task = {"status": "DONE"}
        result = format_backlog_task(task)
        assert result["status_color"] == get_task_status_color("DONE")
