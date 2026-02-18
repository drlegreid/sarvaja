"""Batch 260 — UI controller None guard tests.

Validates fixes for:
- BUG-260-SESSION-001: state.sessions iterated with or [] guard
- BUG-260-SESSION-002: state.rules iterated with or [] guard
- BUG-260-SESSION-003: state.decisions iterated with or [] guard
- BUG-260-TRUST-001: list(state.agents or []) guard in trust.py
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-260-SESSION-001: state.sessions guard ───────────────────────

class TestSessionsNoneGuard:
    """select_session must guard against None state.sessions."""

    def test_sessions_or_empty(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        idx = src.index("def select_session")
        block = src[idx:idx + 800]
        assert "(state.sessions or [])" in block

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        assert "BUG-260-SESSION-001" in src


# ── BUG-260-SESSION-002: state.rules guard ──────────────────────────

class TestRulesNoneGuard:
    """navigate_to_rule must guard against None state.rules."""

    def test_rules_or_empty(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        idx = src.index("def navigate_to_rule_from_session")
        block = src[idx:idx + 800]
        assert "(state.rules or [])" in block

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        assert "BUG-260-SESSION-002" in src


# ── BUG-260-SESSION-003: state.decisions guard ──────────────────────

class TestDecisionsNoneGuard:
    """navigate_to_decision must guard against None state.decisions."""

    def test_decisions_or_empty(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        idx = src.index("def navigate_to_decision_from_session")
        block = src[idx:idx + 800]
        assert "(state.decisions or [])" in block

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        assert "BUG-260-SESSION-003" in src


# ── BUG-260-TRUST-001: state.agents guard ───────────────────────────

class TestAgentsNoneGuard:
    """toggle_agent_pause must guard against None state.agents."""

    def test_agents_or_empty_in_list(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        idx = src.index("def toggle_agent_pause")
        block = src[idx:idx + 1200]
        assert "state.agents or []" in block

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        assert "BUG-260-TRUST-001" in src


# ── No bare iteration without guard ─────────────────────────────────

class TestNoBareSessions:
    """No bare 'for x in state.sessions:' should exist (must use or [])."""

    def test_no_bare_sessions_iteration(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        # Find all lines with 'for ... in state.sessions' and ensure they have 'or []'
        lines = src.split("\n")
        bare = [
            i + 1 for i, line in enumerate(lines)
            if "in state.sessions" in line and "or []" not in line
            and line.strip().startswith("for ")
        ]
        assert not bare, f"Bare state.sessions iteration at lines: {bare}"

    def test_no_bare_rules_iteration(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        lines = src.split("\n")
        bare = [
            i + 1 for i, line in enumerate(lines)
            if "in state.rules" in line and "or []" not in line
            and line.strip().startswith("for ")
        ]
        assert not bare, f"Bare state.rules iteration at lines: {bare}"

    def test_no_bare_decisions_iteration(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        lines = src.split("\n")
        bare = [
            i + 1 for i, line in enumerate(lines)
            if "in state.decisions" in line and "or []" not in line
            and line.strip().startswith("for ")
        ]
        assert not bare, f"Bare state.decisions iteration at lines: {bare}"


# ── Module import defense tests ──────────────────────────────────────

class TestBatch260Imports:
    def test_sessions_controller_importable(self):
        import agent.governance_ui.controllers.sessions
        assert agent.governance_ui.controllers.sessions is not None

    def test_trust_controller_importable(self):
        import agent.governance_ui.controllers.trust
        assert agent.governance_ui.controllers.trust is not None
