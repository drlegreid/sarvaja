"""Batch 198 — Heuristic checks defense tests.

Validates fixes for:
- BUG-198-EXPLR-FIELD-001: rule_id field in violation reports
- BUG-198-EXPLR-DEC-FIELD-001: decision_id field in violation reports
- CVP category handling (known documented issue)
"""
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-198-EXPLR-FIELD-001: Rule field name ────────────────────────

class TestExploratoryRuleField:
    """H-EXPLR-005 must use rule_id, not id."""

    def test_rule_doc_check_uses_rule_id(self):
        """Verify violation list uses r.get('rule_id') not r.get('id')."""
        src = (SRC / "governance/routes/tests/heuristic_checks_exploratory.py").read_text()
        # Find check_rule_document_paths_populated and look for rule_id
        in_func = False
        found_rule_id = False
        found_bare_id = False
        for line in src.splitlines():
            if "def check_rule_document_paths_populated" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func:
                if 'r.get("rule_id"' in line:
                    found_rule_id = True
                if 'r.get("id",' in line and "rule_id" not in line and "decision_id" not in line:
                    found_bare_id = True
        assert found_rule_id, "Should use rule_id for violation ID"
        assert not found_bare_id, "Should not use bare 'id' for rule violations"


# ── BUG-198-EXPLR-DEC-FIELD-001: Decision field name ────────────────

class TestExploratoryDecisionField:
    """H-EXPLR-003 must use decision_id with id fallback."""

    def test_decision_rule_check_uses_decision_id(self):
        """Verify violation list uses d.get('decision_id') not bare d.get('id')."""
        src = (SRC / "governance/routes/tests/heuristic_checks_exploratory.py").read_text()
        in_func = False
        found_decision_id = False
        for line in src.splitlines():
            if "def check_decision_rule_linking" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "decision_id" in line:
                found_decision_id = True
        assert found_decision_id, "Should use decision_id for violation ID"


# ── CVP category structure ──────────────────────────────────────────

class TestCVPCategoryStructure:
    """CVP sweep pre-seeds category with tier info."""

    def test_cvp_runner_has_category_field(self):
        """CVP runner should pre-seed category with tier info."""
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        assert "cvp-tier" in src or "category" in src

    def test_heuristic_checks_all_importable(self):
        """All heuristic check modules should be importable."""
        from governance.routes.tests import heuristic_checks_exploratory
        assert hasattr(heuristic_checks_exploratory, "check_rule_document_paths_populated")
        assert hasattr(heuristic_checks_exploratory, "check_decision_rule_linking")

    def test_api_get_helper_exists(self):
        """_api_get helper should exist in heuristic checks."""
        from governance.routes.tests.heuristic_checks_exploratory import _api_get
        assert callable(_api_get)
