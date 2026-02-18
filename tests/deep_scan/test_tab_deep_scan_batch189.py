"""Deep scan batch 189: Stores + TypeDB access layer.

Batch 189 findings: 10 total, 2 confirmed fixes, 8 rejected/deferred.
- BUG-189-001: dict(session) on Session dataclass → TypeError.
- BUG-189-007: Agent status not persisted in metrics file.
"""
import pytest
from pathlib import Path


# ── Session dataclass conversion defense ──────────────


class TestSessionDataclassConversion:
    """Verify sessions_lifecycle.py uses dataclasses.asdict."""

    def test_end_session_uses_asdict(self):
        """end_session uses dataclasses.asdict, not dict()."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/sessions_lifecycle.py").read_text()
        # Find the auto-evidence section
        start = src.index("Auto-generate evidence")
        section = src[start:start + 300]
        assert "dataclasses.asdict" in section
        # Should NOT have bare dict(session)
        assert "dict(session)" not in section

    def test_session_entity_is_dataclass(self):
        """Session entity is a proper dataclass."""
        import dataclasses
        from governance.typedb.entities import Session
        assert dataclasses.is_dataclass(Session)

    def test_session_entity_asdict(self):
        """Session entity can be converted with asdict."""
        import dataclasses
        from governance.typedb.entities import Session
        s = Session(id="TEST-001")
        d = dataclasses.asdict(s)
        assert isinstance(d, dict)
        assert d["id"] == "TEST-001"


# ── Agent metrics persistence defense ──────────────


class TestAgentMetricsPersistence:
    """Verify agent status is persisted in metrics."""

    def test_claim_persists_status(self):
        """_update_agent_metrics_on_claim persists status field."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/agents.py").read_text()
        start = src.index("def _update_agent_metrics_on_claim")
        end_marker = "\ndef "
        rest = src[start:]
        end = rest.index(end_marker, 10) if end_marker in rest[10:] else len(rest)
        func = rest[:end]
        # Should persist status
        assert '"status"' in func

    def test_agent_store_has_default_status(self):
        """Agent store entries include default status."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/agents.py").read_text()
        assert "PAUSED" in src


# ── Store structure defense ──────────────


class TestStoreStructureDefense:
    """Verify store modules exist and have key functions."""

    def test_typedb_access_importable(self):
        """typedb_access module importable."""
        from governance.stores import typedb_access
        assert typedb_access is not None

    def test_helpers_task_to_response(self):
        """helpers has task_to_response."""
        from governance.stores.helpers import task_to_response
        assert callable(task_to_response)

    def test_config_get_typedb_client(self):
        """config has get_typedb_client."""
        from governance.stores.config import get_typedb_client
        assert callable(get_typedb_client)

    def test_audit_store_importable(self):
        """audit store is importable."""
        from governance.stores import audit
        assert audit is not None

    def test_session_persistence_importable(self):
        """session_persistence is importable."""
        from governance.stores import session_persistence
        assert session_persistence is not None
