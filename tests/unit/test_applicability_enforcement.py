"""
Tests for Applicability Enforcement Framework.

Per EPIC-GOV-RULES-V3 P4: TDD RED phase.
Tests for ComplianceResult model and check_rule_compliance() function.

Created: 2026-03-25
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# ComplianceResult model tests
# ---------------------------------------------------------------------------

class TestComplianceResult:
    """Tests for the ComplianceResult dataclass."""

    def test_compliance_result_mandatory_block(self):
        from governance.workflow_compliance.enforcement import ComplianceResult
        result = ComplianceResult(
            level="MANDATORY_BLOCK",
            rule_id="DOC-SIZE-01-v1",
            message="File exceeds 300 lines",
            action="file_create",
        )
        assert result.level == "MANDATORY_BLOCK"
        assert result.rule_id == "DOC-SIZE-01-v1"
        assert result.is_blocking is True

    def test_compliance_result_recommended_warn(self):
        from governance.workflow_compliance.enforcement import ComplianceResult
        result = ComplianceResult(
            level="RECOMMENDED_WARN",
            rule_id="DOC-LINK-01-v1",
            message="Document lacks cross-references",
            action="doc_update",
        )
        assert result.level == "RECOMMENDED_WARN"
        assert result.is_blocking is False

    def test_compliance_result_forbidden_block(self):
        from governance.workflow_compliance.enforcement import ComplianceResult
        result = ComplianceResult(
            level="FORBIDDEN_BLOCK",
            rule_id="SAFETY-DESTR-01-v1",
            message="Destructive action forbidden",
            action="git_force_push",
        )
        assert result.level == "FORBIDDEN_BLOCK"
        assert result.is_blocking is True

    def test_compliance_result_conditional_delegates(self):
        from governance.workflow_compliance.enforcement import ComplianceResult
        result = ComplianceResult(
            level="CONDITIONAL_DELEGATE",
            rule_id="TEST-E2E-01-v1",
            message="E2E required when changing routes",
            action="route_change",
        )
        assert result.level == "CONDITIONAL_DELEGATE"
        assert result.is_blocking is False

    def test_compliance_result_pass(self):
        from governance.workflow_compliance.enforcement import ComplianceResult
        result = ComplianceResult(
            level="PASS",
            rule_id="GOV-RULE-01-v1",
            message="Rule compliant",
            action="rule_check",
        )
        assert result.level == "PASS"
        assert result.is_blocking is False

    def test_compliance_result_to_dict(self):
        from governance.workflow_compliance.enforcement import ComplianceResult
        result = ComplianceResult(
            level="MANDATORY_BLOCK",
            rule_id="DOC-SIZE-01-v1",
            message="File exceeds 300 lines",
            action="file_create",
        )
        d = result.to_dict()
        assert d["level"] == "MANDATORY_BLOCK"
        assert d["rule_id"] == "DOC-SIZE-01-v1"
        assert d["message"] == "File exceeds 300 lines"
        assert d["action"] == "file_create"
        assert d["is_blocking"] is True


# ---------------------------------------------------------------------------
# check_rule_compliance() tests
# ---------------------------------------------------------------------------

class TestCheckRuleCompliance:
    """Tests for the check_rule_compliance function."""

    def _make_rule(self, rule_id="TEST-RULE-01", applicability="MANDATORY",
                   status="ACTIVE", **kwargs):
        return {
            "id": rule_id,
            "semantic_id": rule_id,
            "name": f"Test Rule {rule_id}",
            "applicability": applicability,
            "status": status,
            **kwargs,
        }

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_mandatory_rule_non_compliant_returns_block(self, mock_fetch):
        from governance.workflow_compliance.enforcement import check_rule_compliance
        mock_fetch.return_value = [
            self._make_rule("DOC-SIZE-01-v1", "MANDATORY"),
        ]
        result = check_rule_compliance(
            action="file_create",
            context={"rule_id": "DOC-SIZE-01-v1", "compliant": False},
        )
        assert result.level == "MANDATORY_BLOCK"
        assert result.rule_id == "DOC-SIZE-01-v1"
        assert result.is_blocking is True

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_mandatory_rule_compliant_returns_pass(self, mock_fetch):
        from governance.workflow_compliance.enforcement import check_rule_compliance
        mock_fetch.return_value = [
            self._make_rule("DOC-SIZE-01-v1", "MANDATORY"),
        ]
        result = check_rule_compliance(
            action="file_create",
            context={"rule_id": "DOC-SIZE-01-v1", "compliant": True},
        )
        assert result.level == "PASS"
        assert result.is_blocking is False

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_recommended_rule_non_compliant_returns_warn(self, mock_fetch):
        from governance.workflow_compliance.enforcement import check_rule_compliance
        mock_fetch.return_value = [
            self._make_rule("DOC-LINK-01-v1", "RECOMMENDED"),
        ]
        result = check_rule_compliance(
            action="doc_update",
            context={"rule_id": "DOC-LINK-01-v1", "compliant": False},
        )
        assert result.level == "RECOMMENDED_WARN"
        assert result.is_blocking is False

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_forbidden_action_returns_block(self, mock_fetch):
        from governance.workflow_compliance.enforcement import check_rule_compliance
        mock_fetch.return_value = [
            self._make_rule("SAFETY-DESTR-01-v1", "FORBIDDEN"),
        ]
        result = check_rule_compliance(
            action="git_force_push",
            context={"rule_id": "SAFETY-DESTR-01-v1", "compliant": False},
        )
        assert result.level == "FORBIDDEN_BLOCK"
        assert result.is_blocking is True

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_conditional_rule_returns_delegate(self, mock_fetch):
        from governance.workflow_compliance.enforcement import check_rule_compliance
        mock_fetch.return_value = [
            self._make_rule("TEST-E2E-01-v1", "CONDITIONAL"),
        ]
        result = check_rule_compliance(
            action="route_change",
            context={"rule_id": "TEST-E2E-01-v1", "compliant": False},
        )
        assert result.level == "CONDITIONAL_DELEGATE"
        assert result.is_blocking is False

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_unknown_applicability_defaults_to_warn(self, mock_fetch):
        from governance.workflow_compliance.enforcement import check_rule_compliance
        mock_fetch.return_value = [
            self._make_rule("UNKNOWN-RULE-01", "EXPERIMENTAL"),
        ]
        result = check_rule_compliance(
            action="unknown_action",
            context={"rule_id": "UNKNOWN-RULE-01", "compliant": False},
        )
        assert result.level == "RECOMMENDED_WARN"
        assert result.is_blocking is False

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_rule_not_found_returns_pass(self, mock_fetch):
        from governance.workflow_compliance.enforcement import check_rule_compliance
        mock_fetch.return_value = []
        result = check_rule_compliance(
            action="file_create",
            context={"rule_id": "NONEXISTENT-RULE", "compliant": False},
        )
        assert result.level == "PASS"
        assert "not found" in result.message.lower()


# ---------------------------------------------------------------------------
# ComplianceChecker class tests (strategy pattern)
# ---------------------------------------------------------------------------

class TestComplianceChecker:
    """Tests for the ComplianceChecker class with strategy pattern."""

    def _make_rule(self, rule_id="TEST-RULE-01", applicability="MANDATORY",
                   status="ACTIVE", **kwargs):
        return {
            "id": rule_id,
            "semantic_id": rule_id,
            "name": f"Test Rule {rule_id}",
            "applicability": applicability,
            "status": status,
            **kwargs,
        }

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_checker_get_enforcement_summary(self, mock_fetch):
        from governance.workflow_compliance.enforcement import ComplianceChecker
        mock_fetch.return_value = [
            self._make_rule("R1", "MANDATORY"),
            self._make_rule("R2", "MANDATORY"),
            self._make_rule("R3", "RECOMMENDED"),
            self._make_rule("R4", "FORBIDDEN"),
            self._make_rule("R5", "CONDITIONAL"),
            self._make_rule("R6", None),  # no applicability
        ]
        checker = ComplianceChecker()
        summary = checker.get_enforcement_summary()
        assert summary["mandatory"] == 2
        assert summary["recommended"] == 1
        assert summary["forbidden"] == 1
        assert summary["conditional"] == 1
        assert summary["unspecified"] == 1
        assert summary["total"] == 6

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_checker_unimplemented_mandatory_lists_rules(self, mock_fetch):
        from governance.workflow_compliance.enforcement import ComplianceChecker
        mock_fetch.return_value = [
            self._make_rule("R1", "MANDATORY"),
            self._make_rule("R2", "MANDATORY"),
            self._make_rule("R3", "RECOMMENDED"),
        ]
        checker = ComplianceChecker()
        summary = checker.get_enforcement_summary()
        # All MANDATORY rules appear in unimplemented list (no runtime checks registered)
        assert "unimplemented_mandatory" in summary
        assert isinstance(summary["unimplemented_mandatory"], list)

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_checker_register_check_removes_from_unimplemented(self, mock_fetch):
        from governance.workflow_compliance.enforcement import ComplianceChecker
        mock_fetch.return_value = [
            self._make_rule("DOC-SIZE-01-v1", "MANDATORY"),
            self._make_rule("TEST-GUARD-01-v1", "MANDATORY"),
        ]
        checker = ComplianceChecker()
        checker.register_check("DOC-SIZE-01-v1", lambda ctx: True)
        summary = checker.get_enforcement_summary()
        unimpl_ids = [r["rule_id"] for r in summary["unimplemented_mandatory"]]
        assert "DOC-SIZE-01-v1" not in unimpl_ids
        assert "TEST-GUARD-01-v1" in unimpl_ids

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_checker_strategies_are_populated(self, mock_fetch):
        from governance.workflow_compliance.enforcement import ComplianceChecker
        mock_fetch.return_value = []
        checker = ComplianceChecker()
        # Strategy pattern: must have handlers for all 4 levels
        assert "MANDATORY" in checker.strategies
        assert "RECOMMENDED" in checker.strategies
        assert "FORBIDDEN" in checker.strategies
        assert "CONDITIONAL" in checker.strategies

    @patch("governance.workflow_compliance.enforcement.fetch_rules")
    def test_checker_fetch_failure_returns_empty_summary(self, mock_fetch):
        from governance.workflow_compliance.enforcement import ComplianceChecker
        mock_fetch.return_value = []
        checker = ComplianceChecker()
        summary = checker.get_enforcement_summary()
        assert summary["total"] == 0
        assert summary["mandatory"] == 0
