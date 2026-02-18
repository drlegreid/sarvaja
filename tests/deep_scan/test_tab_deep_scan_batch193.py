"""Deep scan batch 193: UI state management layer.

Batch 193 findings: 18 total, 2 confirmed fixes, 16 deferred/rejected.
- BUG-193-004: audit_loading not in finally block.
- BUG-193-010: get_governance_stats() unguarded call.
"""
import pytest
from pathlib import Path


# ── Audit loading safety defense ──────────────


class TestAuditLoadingSafety:
    """Verify audit_loading uses finally block."""

    def test_audit_loading_in_finally(self):
        """audit_loading reset is inside a finally block."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/audit_loaders.py").read_text()
        start = src.index("def load_audit_trail")
        rest = src[start:]
        end = rest.index("\n    @ctrl", 10) if "\n    @ctrl" in rest[10:] else len(rest)
        func = rest[:end]
        assert "finally:" in func
        # The audit_loading = False should be after 'finally:'
        finally_idx = func.index("finally:")
        assert "audit_loading = False" in func[finally_idx:]


# ── Governance stats guard defense ──────────────


class TestGovernanceStatsGuard:
    """Verify get_governance_stats is wrapped in try-except."""

    def test_governance_stats_has_try_except(self):
        """get_governance_stats call is wrapped in try-except."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/data_loaders.py").read_text()
        # Find the CALL (with opening paren), not the import
        idx = src.index("governance_stats = get_governance_stats(")
        before = src[max(0, idx - 60):idx]
        after = src[idx:idx + 200]
        assert "try:" in before
        assert "except Exception" in after


# ── Controller structure defense ──────────────


class TestControllerStructureDefense:
    """Verify controller modules exist and are importable."""

    def test_audit_loaders_importable(self):
        """audit_loaders module is importable."""
        from agent.governance_ui.controllers import audit_loaders
        assert audit_loaders is not None

    def test_data_loaders_importable(self):
        """data_loaders module is importable."""
        from agent.governance_ui.controllers import data_loaders
        assert data_loaders is not None

    def test_sessions_pagination_importable(self):
        """sessions_pagination module is importable."""
        from agent.governance_ui.controllers import sessions_pagination
        assert sessions_pagination is not None

    def test_workflow_loaders_importable(self):
        """workflow_loaders module is importable."""
        from agent.governance_ui.controllers import workflow_loaders
        assert workflow_loaders is not None

    def test_backlog_importable(self):
        """backlog module is importable."""
        from agent.governance_ui.controllers import backlog
        assert backlog is not None

    def test_projects_importable(self):
        """projects module is importable."""
        from agent.governance_ui.controllers import projects
        assert projects is not None
