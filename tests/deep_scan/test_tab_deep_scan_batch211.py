"""Batch 211 — Heuristic cross-checks defense tests.

Validates fixes for:
- BUG-211-CROSS-ISINSTANCE-001: isinstance guard on _api_get result
- BUG-211-CROSS-ENCODING-001: encoding on file open in check_testid_coverage
"""
from pathlib import Path
from unittest.mock import patch


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-211-CROSS-ISINSTANCE-001: isinstance guard ───────────────────

class TestCrossCheckIsinstanceGuard:
    """check_service_layer_coverage must guard against list response."""

    def test_returns_skip_on_list_response(self):
        """When _api_get returns a list, check should SKIP not crash."""
        from governance.routes.tests.heuristic_checks_cross import (
            check_service_layer_coverage,
        )
        with patch("governance.routes.tests.heuristic_checks_cross._api_get", return_value=["unexpected"]), \
             patch("governance.routes.tests.heuristic_checks_cross._is_self_referential", return_value=False):
            result = check_service_layer_coverage("http://fake:8082")
        assert result["status"] == "SKIP"

    def test_isinstance_guard_in_source(self):
        """Source must check isinstance(data, dict) before .get()."""
        src = (SRC / "governance/routes/tests/heuristic_checks_cross.py").read_text()
        # Find the isinstance guard within check_service_layer_coverage
        in_func = False
        found_guard = False
        for line in src.splitlines():
            if "def check_service_layer_coverage" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "isinstance(data, dict)" in line:
                found_guard = True
        assert found_guard, "Must have isinstance(data, dict) guard"


# ── BUG-211-CROSS-ENCODING-001: File encoding ────────────────────────

class TestCrossCheckEncoding:
    """check_testid_coverage must specify encoding on open."""

    def test_encoding_in_source(self):
        """check_testid_coverage open must include encoding='utf-8'."""
        src = (SRC / "governance/routes/tests/heuristic_checks_cross.py").read_text()
        in_func = False
        found_encoding = False
        for line in src.splitlines():
            if "def check_testid_coverage" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "encoding" in line and "utf-8" in line:
                found_encoding = True
        assert found_encoding, "Must use encoding='utf-8' in file open"


# ── Cross checks defense ──────────────────────────────────────────────

class TestCrossChecksDefense:
    """Defense tests for cross-entity heuristic checks."""

    def test_check_service_layer_callable(self):
        from governance.routes.tests.heuristic_checks_cross import check_service_layer_coverage
        assert callable(check_service_layer_coverage)

    def test_check_api_endpoint_health_callable(self):
        from governance.routes.tests.heuristic_checks_cross import check_api_endpoint_health
        assert callable(check_api_endpoint_health)

    def test_check_pagination_contract_callable(self):
        from governance.routes.tests.heuristic_checks_cross import check_pagination_contract
        assert callable(check_pagination_contract)

    def test_check_decisions_link_rules_callable(self):
        from governance.routes.tests.heuristic_checks_cross import check_decisions_link_rules
        assert callable(check_decisions_link_rules)

    def test_check_testid_coverage_callable(self):
        from governance.routes.tests.heuristic_checks_cross import check_testid_coverage
        assert callable(check_testid_coverage)

    def test_all_cross_checks_skip_on_self_ref(self):
        """All cross-checks that call _is_self_referential should SKIP."""
        from governance.routes.tests.heuristic_checks_cross import CROSS_API_UI_CHECKS
        with patch("governance.routes.tests.heuristic_checks_cross._is_self_referential", return_value=True):
            for check in CROSS_API_UI_CHECKS:
                result = check["check_fn"]("http://fake:8082")
                assert result["status"] in ("SKIP", "PASS"), \
                    f"{check['id']} should SKIP on self-referential, got {result['status']}"

    def test_cross_checks_registry_exists(self):
        from governance.routes.tests.heuristic_checks_cross import CROSS_API_UI_CHECKS
        assert isinstance(CROSS_API_UI_CHECKS, list)
        assert len(CROSS_API_UI_CHECKS) >= 4


# ── Heuristic checks registry defense ─────────────────────────────────

class TestHeuristicChecksRegistry:
    """Defense tests for the unified check registry."""

    def test_heuristic_checks_imported(self):
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        assert isinstance(HEURISTIC_CHECKS, list)

    def test_all_checks_have_required_keys(self):
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        required = {"id", "domain", "name", "check_fn"}
        for check in HEURISTIC_CHECKS:
            missing = required - set(check.keys())
            assert not missing, f"Check {check.get('id', '?')} missing keys: {missing}"

    def test_all_check_fns_are_callable(self):
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        for check in HEURISTIC_CHECKS:
            assert callable(check["check_fn"]), f"{check['id']} check_fn not callable"
