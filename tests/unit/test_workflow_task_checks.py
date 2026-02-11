"""
Unit tests for Workflow Compliance Task Checks.

Per DOC-SIZE-01-v1: Tests for extracted task_checks.py module.
Tests: check_task_evidence_compliance, check_task_session_linkage, check_task_rule_linkage.
"""

import pytest
from unittest.mock import patch

from governance.workflow_compliance.checks.task_checks import (
    check_task_evidence_compliance,
    check_task_session_linkage,
    check_task_rule_linkage,
)


class TestCheckTaskEvidenceCompliance:
    """Tests for check_task_evidence_compliance()."""

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_no_tasks_returns_skip(self, mock_fetch):
        mock_fetch.return_value = []
        result = check_task_evidence_compliance()
        assert result.status == "SKIP"
        assert result.rule_id == "TEST-FIX-01-v1"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_no_completed_tasks_returns_skip(self, mock_fetch):
        mock_fetch.return_value = [{"status": "OPEN", "task_id": "T-1"}]
        result = check_task_evidence_compliance()
        assert result.status == "SKIP"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_all_completed_have_evidence_pass(self, mock_fetch):
        mock_fetch.return_value = [
            {"status": "DONE", "evidence": "ev.md", "task_id": "T-1"},
            {"status": "DONE", "evidence": "ev2.md", "task_id": "T-2"},
        ]
        result = check_task_evidence_compliance()
        assert result.status == "PASS"
        assert "100%" in result.message

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_some_missing_evidence_warning(self, mock_fetch):
        tasks = [{"status": "DONE", "evidence": "ev.md", "task_id": f"T-{i}"} for i in range(7)]
        tasks += [{"status": "DONE", "evidence": None, "task_id": f"T-M{i}"} for i in range(3)]
        mock_fetch.return_value = tasks
        result = check_task_evidence_compliance()
        assert result.status == "WARNING"
        assert "70%" in result.message

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_most_missing_evidence_fail(self, mock_fetch):
        tasks = [{"status": "DONE", "evidence": "ev.md", "task_id": "T-1"}]
        tasks += [{"status": "DONE", "evidence": None, "task_id": f"T-{i}"} for i in range(9)]
        mock_fetch.return_value = tasks
        result = check_task_evidence_compliance()
        assert result.status == "FAIL"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_fetch_error_returns_skip(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        result = check_task_evidence_compliance()
        assert result.status == "SKIP"
        assert "Network error" in result.message

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_violations_included_on_fail(self, mock_fetch):
        mock_fetch.return_value = [
            {"status": "DONE", "evidence": None, "task_id": "T-FAIL-1"},
            {"status": "DONE", "evidence": None, "task_id": "T-FAIL-2"},
        ]
        result = check_task_evidence_compliance()
        assert result.violations is not None
        assert "T-FAIL-1" in result.violations


class TestCheckTaskSessionLinkage:
    """Tests for check_task_session_linkage()."""

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_no_tasks_returns_skip(self, mock_fetch):
        mock_fetch.return_value = []
        result = check_task_session_linkage()
        assert result.status == "SKIP"
        assert result.rule_id == "SESSION-EVID-01-v1"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_no_completed_returns_skip(self, mock_fetch):
        mock_fetch.return_value = [{"status": "OPEN"}]
        result = check_task_session_linkage()
        assert result.status == "SKIP"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_linked_tasks_pass(self, mock_fetch):
        mock_fetch.return_value = [
            {"status": "DONE", "linked_sessions": ["S-1"], "task_id": "T-1"},
        ]
        result = check_task_session_linkage()
        assert result.status == "PASS"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_no_linked_tasks_fail(self, mock_fetch):
        mock_fetch.return_value = [
            {"status": "DONE", "linked_sessions": [], "task_id": "T-1"},
        ]
        result = check_task_session_linkage()
        assert result.status == "FAIL"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_fetch_error_returns_skip(self, mock_fetch):
        mock_fetch.side_effect = Exception("Timeout")
        result = check_task_session_linkage()
        assert result.status == "SKIP"


class TestCheckTaskRuleLinkage:
    """Tests for check_task_rule_linkage()."""

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_no_tasks_returns_skip(self, mock_fetch):
        mock_fetch.return_value = []
        result = check_task_rule_linkage()
        assert result.status == "SKIP"
        assert result.rule_id == "TASK-LIFE-01-v1"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_many_linked_pass(self, mock_fetch):
        tasks = [{"linked_rules": ["R-1"], "task_id": f"T-{i}"} for i in range(5)]
        mock_fetch.return_value = tasks
        result = check_task_rule_linkage()
        assert result.status == "PASS"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_no_linked_warning(self, mock_fetch):
        mock_fetch.return_value = [
            {"linked_rules": [], "task_id": "T-1"},
            {"linked_rules": [], "task_id": "T-2"},
        ]
        result = check_task_rule_linkage()
        assert result.status == "WARNING"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_some_linked_warning(self, mock_fetch):
        tasks = [{"linked_rules": ["R-1"], "task_id": "T-1"}]
        tasks += [{"linked_rules": [], "task_id": f"T-{i}"} for i in range(19)]
        mock_fetch.return_value = tasks
        result = check_task_rule_linkage()
        # 1/20 = 5% < 20% → WARNING
        assert result.status == "WARNING"

    @patch("governance.workflow_compliance.checks.task_checks.fetch_tasks")
    def test_fetch_error_returns_skip(self, mock_fetch):
        mock_fetch.side_effect = Exception("DB down")
        result = check_task_rule_linkage()
        assert result.status == "SKIP"
