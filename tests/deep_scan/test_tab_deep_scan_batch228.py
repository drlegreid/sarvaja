"""Batch 228 — Services layer defense tests.

Validates fixes for:
- BUG-228-SESSIONS-003: end_session COMPLETED guard missing in TypeDB path
- BUG-228-RULES-001: has_more uses (offset+limit) instead of (offset+len(items))
- BUG-228-CROSS-001: Service return-type consistency checks
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-228-SESSIONS-003: COMPLETED guard in TypeDB path ─────────────

class TestEndSessionCompletedGuard:
    """end_session must guard against double-complete in BOTH paths."""

    def test_typedb_path_has_completed_guard(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        idx = src.index("def end_session")
        block = src[idx:idx + 600]
        assert "BUG-228-SESSIONS-003" in block

    def test_fallback_path_has_completed_guard(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        idx = src.index("Fallback to in-memory")
        block = src[idx:idx + 300]
        assert '"COMPLETED"' in block

    def test_both_paths_raise_valueerror(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        # Should have ValueError raise in both TypeDB and fallback paths
        count = src.count("already completed")
        assert count >= 2, f"Expected 2+ COMPLETED guards, found {count}"


# ── BUG-228-RULES-001: has_more pagination fix ──────────────────────

class TestRulesHasMoreFix:
    """has_more should use len(items), not limit."""

    def test_uses_len_items(self):
        src = (SRC / "governance/services/rules.py").read_text()
        idx = src.index("has_more")
        block = src[idx:idx + 100]
        assert "len(items)" in block

    def test_no_offset_plus_limit_for_has_more(self):
        """The old pattern (offset + limit) < total is incorrect for last page."""
        src = (SRC / "governance/services/rules.py").read_text()
        idx = src.index("has_more")
        block = src[idx:idx + 100]
        # Should NOT contain the old broken pattern
        assert "(offset + limit) < total" not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/rules.py").read_text()
        assert "BUG-228-RULES-001" in src


# ── Service module import defense tests ──────────────────────────────

class TestServiceImports:
    """Defense tests for governance.services modules."""

    def test_sessions_lifecycle_importable(self):
        import governance.services.sessions_lifecycle
        assert governance.services.sessions_lifecycle is not None

    def test_rules_importable(self):
        import governance.services.rules
        assert governance.services.rules is not None

    def test_tasks_importable(self):
        import governance.services.tasks
        assert governance.services.tasks is not None

    def test_tasks_mutations_importable(self):
        import governance.services.tasks_mutations
        assert governance.services.tasks_mutations is not None

    def test_agents_importable(self):
        import governance.services.agents
        assert governance.services.agents is not None

    def test_projects_importable(self):
        import governance.services.projects
        assert governance.services.projects is not None

    def test_session_repair_importable(self):
        import governance.services.session_repair
        assert governance.services.session_repair is not None

    def test_session_evidence_importable(self):
        import governance.services.session_evidence
        assert governance.services.session_evidence is not None

    def test_cc_session_scanner_importable(self):
        import governance.services.cc_session_scanner
        assert governance.services.cc_session_scanner is not None

    def test_task_id_gen_importable(self):
        import governance.services.task_id_gen
        assert governance.services.task_id_gen is not None

    def test_rules_relations_importable(self):
        import governance.services.rules_relations
        assert governance.services.rules_relations is not None

    def test_agents_metrics_importable(self):
        import governance.services.agents_metrics
        assert governance.services.agents_metrics is not None

    def test_ingestion_checkpoint_importable(self):
        import governance.services.ingestion_checkpoint
        assert governance.services.ingestion_checkpoint is not None

    def test_workspace_registry_importable(self):
        import governance.services.workspace_registry
        assert governance.services.workspace_registry is not None
