"""
Unit tests for Task-related Compliance Checks.

Per DOC-SIZE-01-v1: Tests for workflow_compliance/checks/task_checks.py module.
Tests: check_task_evidence_compliance, check_task_session_linkage, check_task_rule_linkage.
"""

from unittest.mock import patch

from governance.workflow_compliance.checks.task_checks import (
    check_task_evidence_compliance,
    check_task_session_linkage,
    check_task_rule_linkage,
)

_PATCH = "governance.workflow_compliance.checks.task_checks.fetch_tasks"


class TestTaskEvidenceCompliance:
    @patch(_PATCH, return_value=None)
    def test_no_tasks(self, _m):
        result = check_task_evidence_compliance()
        assert result.status == "SKIP"

    @patch(_PATCH, return_value=[])
    def test_empty_tasks(self, _m):
        result = check_task_evidence_compliance()
        assert result.status == "SKIP"

    @patch(_PATCH, return_value=[
        {"status": "DONE", "evidence": "proof.md"},
        {"status": "DONE", "evidence": "test.md"},
    ])
    def test_all_with_evidence(self, _m):
        result = check_task_evidence_compliance()
        assert result.status == "PASS"
        assert "100%" in result.message

    @patch(_PATCH, return_value=[
        {"status": "DONE", "evidence": "proof.md"},
        {"status": "DONE", "evidence": None},
    ])
    def test_half_evidence(self, _m):
        result = check_task_evidence_compliance()
        assert result.status == "WARNING"

    @patch(_PATCH, return_value=[
        {"status": "DONE", "evidence": None},
        {"status": "DONE", "evidence": None},
        {"status": "DONE", "evidence": None},
    ])
    def test_no_evidence(self, _m):
        result = check_task_evidence_compliance()
        assert result.status == "FAIL"
        assert len(result.violations) > 0

    @patch(_PATCH, return_value=[
        {"status": "OPEN"},
        {"status": "TODO"},
    ])
    def test_no_completed(self, _m):
        result = check_task_evidence_compliance()
        assert result.status == "SKIP"

    @patch(_PATCH, side_effect=Exception("API down"))
    def test_exception(self, _m):
        result = check_task_evidence_compliance()
        assert result.status == "SKIP"
        # BUG-474: message now contains type(e).__name__ (sanitized)
        assert "Exception" in result.message


class TestTaskSessionLinkage:
    @patch(_PATCH, return_value=None)
    def test_no_tasks(self, _m):
        result = check_task_session_linkage()
        assert result.status == "SKIP"

    @patch(_PATCH, return_value=[
        {"status": "DONE", "linked_sessions": ["S-1"]},
    ])
    def test_linked(self, _m):
        result = check_task_session_linkage()
        assert result.status == "PASS"

    @patch(_PATCH, return_value=[
        {"status": "DONE", "linked_sessions": []},
        {"status": "DONE"},
    ])
    def test_no_links(self, _m):
        result = check_task_session_linkage()
        assert result.status == "FAIL"

    @patch(_PATCH, return_value=[
        {"status": "DONE", "linked_sessions": ["S-1"]},
        *[{"status": "DONE", "linked_sessions": []} for _ in range(20)],
    ])
    def test_low_percentage(self, _m):
        result = check_task_session_linkage()
        # 1/21 ≈ 4.8% → WARNING (>0 but <10)
        assert result.status == "WARNING"

    @patch(_PATCH, side_effect=Exception("err"))
    def test_exception(self, _m):
        result = check_task_session_linkage()
        assert result.status == "SKIP"


class TestTaskRuleLinkage:
    @patch(_PATCH, return_value=None)
    def test_no_tasks(self, _m):
        result = check_task_rule_linkage()
        assert result.status == "SKIP"

    @patch(_PATCH, return_value=[
        {"status": "OPEN", "linked_rules": ["RULE-001"]},
        {"status": "OPEN", "linked_rules": ["RULE-002"]},
    ])
    def test_all_linked(self, _m):
        result = check_task_rule_linkage()
        assert result.status == "PASS"

    @patch(_PATCH, return_value=[
        {"status": "OPEN", "linked_rules": []},
        {"status": "OPEN"},
    ])
    def test_none_linked(self, _m):
        result = check_task_rule_linkage()
        assert result.status == "WARNING"

    @patch(_PATCH, return_value=[
        {"status": "OPEN", "linked_rules": ["R-1"]},
        *[{"status": "OPEN"} for _ in range(10)],
    ])
    def test_low_linkage(self, _m):
        result = check_task_rule_linkage()
        # 1/11 ≈ 9% → WARNING (<20%)
        assert result.status == "WARNING"

    @patch(_PATCH, side_effect=Exception("err"))
    def test_exception(self, _m):
        result = check_task_rule_linkage()
        assert result.status == "SKIP"
