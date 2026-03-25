"""Tests for H-RULE heuristic checks (H-RULE-002, H-RULE-005, H-RULE-006).

Per EPIC-RULES-V3-P3: TDD — tests written BEFORE implementation.
Per TEST-GUARD-01: Tests exist before code.
"""
from unittest.mock import MagicMock, patch

API = "http://testhost:9999"


def _mock_get(status=200, json_data=None):
    """Create a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data
    return resp


# ===== H-RULE-002: MANDATORY enforcement =====

class TestCheckMandatoryEnforcement:
    """H-RULE-002: Every MANDATORY-applicability rule has ≥1 implementing task."""

    @patch("httpx.get")
    def test_mandatory_rule_with_implementing_task_passes(self, mock_get):
        from governance.routes.tests.heuristic_checks_rules import check_mandatory_enforcement
        mock_get.return_value = _mock_get(200, {
            "items": [
                {"rule_id": "RULE-A", "applicability": "MANDATORY", "linked_tasks_count": 3},
                {"rule_id": "RULE-B", "applicability": "MANDATORY", "linked_tasks_count": 1},
            ]
        })
        result = check_mandatory_enforcement(API)
        assert result["status"] == "PASS"
        assert result["violations"] == []

    @patch("httpx.get")
    def test_mandatory_rule_without_implementing_task_fails(self, mock_get):
        from governance.routes.tests.heuristic_checks_rules import check_mandatory_enforcement
        mock_get.return_value = _mock_get(200, {
            "items": [
                {"rule_id": "RULE-A", "applicability": "MANDATORY", "linked_tasks_count": 0},
                {"rule_id": "RULE-B", "applicability": "MANDATORY", "linked_tasks_count": 2},
                {"rule_id": "RULE-C", "applicability": "MANDATORY", "linked_tasks_count": 0},
            ]
        })
        result = check_mandatory_enforcement(API)
        assert result["status"] == "FAIL"
        assert "RULE-A" in result["violations"]
        assert "RULE-C" in result["violations"]
        assert len(result["violations"]) == 2

    @patch("httpx.get")
    def test_non_mandatory_rule_without_task_is_ok(self, mock_get):
        from governance.routes.tests.heuristic_checks_rules import check_mandatory_enforcement
        mock_get.return_value = _mock_get(200, {
            "items": [
                {"rule_id": "RULE-A", "applicability": "RECOMMENDED", "linked_tasks_count": 0},
                {"rule_id": "RULE-B", "applicability": "OPTIONAL", "linked_tasks_count": 0},
            ]
        })
        result = check_mandatory_enforcement(API)
        assert result["status"] == "SKIP"


# ===== H-RULE-005: Circular dependencies =====

class TestCheckRuleCircularDeps:
    """H-RULE-005: No circular dependencies in the rule dependency graph."""

    @patch("httpx.get")
    def test_no_circular_deps_passes(self, mock_get):
        from governance.routes.tests.heuristic_checks_rules import check_rule_circular_deps
        mock_get.return_value = _mock_get(200, {
            "circular_count": 0,
            "cycles": [],
            "total_dependencies": 27,
        })
        result = check_rule_circular_deps(API)
        assert result["status"] == "PASS"
        assert result["violations"] == []

    @patch("httpx.get")
    def test_circular_dep_detected_fails_with_cycle_details(self, mock_get):
        from governance.routes.tests.heuristic_checks_rules import check_rule_circular_deps
        mock_get.return_value = _mock_get(200, {
            "circular_count": 1,
            "cycles": [["RULE-A", "RULE-B", "RULE-A"]],
            "total_dependencies": 10,
        })
        result = check_rule_circular_deps(API)
        assert result["status"] == "FAIL"
        assert len(result["violations"]) == 1
        assert "RULE-A" in result["violations"][0]
        assert "RULE-B" in result["violations"][0]


# ===== H-RULE-006: Unique IDs =====

class TestCheckRuleUniqueIds:
    """H-RULE-006: Every rule-id in TypeDB is unique (no duplicates)."""

    @patch("httpx.get")
    def test_unique_rule_ids_passes(self, mock_get):
        from governance.routes.tests.heuristic_checks_rules import check_rule_unique_ids
        mock_get.return_value = _mock_get(200, {
            "items": [
                {"rule_id": "RULE-A"},
                {"rule_id": "RULE-B"},
                {"rule_id": "RULE-C"},
            ]
        })
        result = check_rule_unique_ids(API)
        assert result["status"] == "PASS"
        assert result["violations"] == []

    @patch("httpx.get")
    def test_duplicate_rule_id_fails(self, mock_get):
        from governance.routes.tests.heuristic_checks_rules import check_rule_unique_ids
        mock_get.return_value = _mock_get(200, {
            "items": [
                {"rule_id": "RULE-A"},
                {"rule_id": "RULE-B"},
                {"rule_id": "RULE-A"},
            ]
        })
        result = check_rule_unique_ids(API)
        assert result["status"] == "FAIL"
        assert "RULE-A" in result["violations"]


# ===== Registry integration =====

class TestRuleHeuristicsRegistry:
    """Verify H-RULE checks are registered in the main registry."""

    def test_rule_heuristics_registered_in_checks_registry(self):
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        check_ids = [c["id"] for c in HEURISTIC_CHECKS]
        assert "H-RULE-002" in check_ids
        assert "H-RULE-005" in check_ids
        assert "H-RULE-006" in check_ids

    def test_cvp_sweep_includes_all_h_rule_checks(self):
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        rule_checks = [c for c in HEURISTIC_CHECKS if c["id"].startswith("H-RULE-")]
        assert len(rule_checks) >= 6, (
            f"Expected ≥6 H-RULE checks, got {len(rule_checks)}: "
            f"{[c['id'] for c in rule_checks]}"
        )
