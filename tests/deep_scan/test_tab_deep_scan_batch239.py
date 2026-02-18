"""Batch 239 — UI controllers layer defense tests.

Validates fixes for:
- BUG-239-RULES-001: None guard on state.rules/decisions/agents iteration
- BUG-239-TESTS-002: Double-submit guard on run_tests trigger
- BUG-239-DL-002: Unwrap paginated dict for available_tasks
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-239-RULES-001: None guard on state iteration ────────────────

class TestNoneGuardOnStateIteration:
    """Controllers must guard against None state lists."""

    def test_rules_controller_has_or_guard(self):
        src = (SRC / "agent/governance_ui/controllers/rules.py").read_text()
        assert "(state.rules or [])" in src

    def test_decisions_controller_has_or_guard(self):
        src = (SRC / "agent/governance_ui/controllers/decisions.py").read_text()
        assert "(state.decisions or [])" in src

    def test_trust_controller_has_or_guard(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        assert "(state.agents or [])" in src

    def test_rules_bug_marker(self):
        src = (SRC / "agent/governance_ui/controllers/rules.py").read_text()
        assert "BUG-239-RULES-001" in src

    def test_decisions_bug_marker(self):
        src = (SRC / "agent/governance_ui/controllers/decisions.py").read_text()
        assert "BUG-239-RULES-001" in src

    def test_trust_bug_marker(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        assert "BUG-239-RULES-001" in src


# ── BUG-239-TESTS-002: Double-submit guard ───────────────────────────

class TestTestsDoubleSubmitGuard:
    """on_run_tests must check tests_running before launching."""

    def test_has_double_submit_guard(self):
        src = (SRC / "agent/governance_ui/controllers/tests.py").read_text()
        idx = src.index("def on_run_tests")
        block = src[idx:idx + 300]
        assert "if state.tests_running:" in block
        assert "return" in block

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/controllers/tests.py").read_text()
        assert "BUG-239-TESTS-002" in src


# ── BUG-239-DL-002: Unwrap paginated dict for available_tasks ────────

class TestAvailableTasksUnwrap:
    """available_tasks must handle paginated dict response."""

    def test_unwrap_pattern_present(self):
        src = (SRC / "agent/governance_ui/controllers/data_loaders.py").read_text()
        idx = src.index("api/tasks/available")
        block = src[idx:idx + 300]
        assert 'isinstance(data, dict)' in block
        assert '"items"' in block

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/controllers/data_loaders.py").read_text()
        assert "BUG-239-DL-002" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch239Imports:
    def test_audit_loaders_importable(self):
        import agent.governance_ui.controllers.audit_loaders
        assert agent.governance_ui.controllers.audit_loaders is not None

    def test_data_loaders_importable(self):
        import agent.governance_ui.controllers.data_loaders
        assert agent.governance_ui.controllers.data_loaders is not None

    def test_decisions_importable(self):
        import agent.governance_ui.controllers.decisions
        assert agent.governance_ui.controllers.decisions is not None

    def test_infra_loaders_importable(self):
        import agent.governance_ui.controllers.infra_loaders
        assert agent.governance_ui.controllers.infra_loaders is not None

    def test_rules_importable(self):
        import agent.governance_ui.controllers.rules
        assert agent.governance_ui.controllers.rules is not None

    def test_sessions_importable(self):
        import agent.governance_ui.controllers.sessions
        assert agent.governance_ui.controllers.sessions is not None

    def test_sessions_detail_loaders_importable(self):
        import agent.governance_ui.controllers.sessions_detail_loaders
        assert agent.governance_ui.controllers.sessions_detail_loaders is not None

    def test_tests_importable(self):
        import agent.governance_ui.controllers.tests
        assert agent.governance_ui.controllers.tests is not None

    def test_trust_importable(self):
        import agent.governance_ui.controllers.trust
        assert agent.governance_ui.controllers.trust is not None
