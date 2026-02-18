"""Deep scan batch 187: UI controllers layer.

Batch 187 findings: 7 total, 3 confirmed fixes, 4 deferred.
- BUG-187-001: rules.py is_loading stuck True on early return.
- BUG-187-002: decisions.py is_loading stuck True on early return.
- BUG-187-003: tests.py run_id=None spawns poll thread for 5 minutes.
"""
import pytest
from pathlib import Path


# ── is_loading reset defense ──────────────


class TestIsLoadingResetDefense:
    """Verify all early returns in form submit handlers reset is_loading."""

    def _find_early_returns_in_try(self, src: str, func_name: str) -> list:
        """Find return statements inside try blocks after is_loading = True."""
        start = src.index(f"def {func_name}")
        # Find next def or end
        rest = src[start:]
        next_def = rest.find("\n    @ctrl.trigger")
        if next_def == -1:
            next_def = rest.find("\ndef ")
            if next_def == -1:
                next_def = len(rest)
        func = rest[:next_def]
        lines = func.split("\n")
        loading_set = False
        early_returns = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "is_loading = True" in stripped:
                loading_set = True
            if loading_set and stripped == "return":
                # Check if line before has is_loading = False
                prev_lines = [lines[j].strip() for j in range(max(0, i - 3), i)]
                has_reset = any("is_loading = False" in p for p in prev_lines)
                early_returns.append({"line": i, "has_reset": has_reset})
        return early_returns

    def test_rules_submit_resets_on_early_return(self):
        """rules.py: submit_rule_form resets is_loading on all early returns."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/rules.py").read_text()
        returns = self._find_early_returns_in_try(src, "submit_rule_form")
        for r in returns:
            assert r["has_reset"], f"Early return at line {r['line']} missing is_loading reset"

    def test_decisions_submit_resets_on_early_return(self):
        """decisions.py: submit_decision_form resets is_loading on all early returns."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/decisions.py").read_text()
        returns = self._find_early_returns_in_try(src, "submit_decision_form")
        for r in returns:
            assert r["has_reset"], f"Early return at line {r['line']} missing is_loading reset"


# ── Test runner None guard defense ──────────────


class TestRunnerNoneGuardDefense:
    """Verify test controller guards against None run_id."""

    def test_run_tests_guards_none_run_id(self):
        """tests.py: on_run_tests checks for None run_id before thread."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/tests.py").read_text()
        start = src.index("def on_run_tests")
        end_marker = "\n    @ctrl.trigger"
        end = src.index(end_marker, start + 1) if end_marker in src[start + 1:] else len(src)
        func = src[start:end]
        # Should have a guard before Thread creation
        thread_idx = func.index("threading.Thread")
        before_thread = func[:thread_idx]
        assert "not run_id" in before_thread or "run_id is None" in before_thread

    def test_poll_function_exists(self):
        """poll_for_results function exists in tests.py."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/tests.py").read_text()
        assert "def poll_for_results" in src


# ── Controller structure defense ──────────────


class TestControllerStructureDefense:
    """Verify controller modules exist and have key triggers."""

    def test_rules_controller_has_submit(self):
        """rules.py has submit_rule_form."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/rules.py").read_text()
        assert "def submit_rule_form" in src

    def test_decisions_controller_has_submit(self):
        """decisions.py has submit_decision_form."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/decisions.py").read_text()
        assert "def submit_decision_form" in src

    def test_tests_controller_has_run(self):
        """tests.py has on_run_tests."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/tests.py").read_text()
        assert "def on_run_tests" in src

    def test_trust_controller_has_select_agent(self):
        """trust.py has select_agent."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/trust.py").read_text()
        assert "def select_agent" in src

    def test_infra_loaders_exists(self):
        """infra_loaders.py exists and has load_infra_status."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/infra_loaders.py").read_text()
        assert "def load_infra_status" in src

    def test_monitor_controller_exists(self):
        """monitor.py exists."""
        root = Path(__file__).parent.parent.parent
        path = root / "agent/governance_ui/controllers/monitor.py"
        assert path.exists()

    def test_impact_controller_exists(self):
        """impact.py exists."""
        root = Path(__file__).parent.parent.parent
        path = root / "agent/governance_ui/controllers/impact.py"
        assert path.exists()
