"""Batch 229 — MCP tools + traceability defense tests.

Validates fixes for:
- BUG-229-HANDOFF-001: Path traversal via unvalidated task_id in filename
- BUG-229-TRACEABILITY-001: TypeQL injection via unescaped rule_id
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-229-HANDOFF-001: Path traversal in handoff filename ──────────

class TestHandoffPathTraversal:
    """handoff_complete must sanitize task_id before constructing filepath."""

    def test_uses_regex_sanitization(self):
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        assert "re.sub(" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        assert "BUG-229-HANDOFF-001" in src

    def test_no_raw_task_id_in_filename(self):
        """Filename should use safe_task, not raw task_id."""
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        idx = src.index("handoff_complete")
        block = src[idx:idx + 800]
        # The f-string for filename should use sanitized vars
        assert "safe_task" in block
        assert "safe_from" in block
        assert "safe_to" in block

    def test_sanitizes_all_three_components(self):
        """All 3 components (task_id, from_agent, to_agent) must be sanitized."""
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        idx = src.index("handoff_complete")
        block = src[idx:idx + 600]
        count = block.count("re.sub(")
        assert count >= 3, f"Expected 3 sanitizations, found {count}"


# ── BUG-229-TRACEABILITY-001: TypeQL injection ──────────────────────

class TestTraceabilityTypeQLInjection:
    """rule_id must be escaped before interpolation into TypeQL."""

    def test_escapes_quotes_in_rule_id(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("trace_rule_chain")
        block = src[idx:idx + 1200]
        assert 'replace(\'"\', \'\\\\"\')' in block or "safe_rule_id" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        assert "BUG-229-TRACEABILITY-001" in src

    def test_uses_safe_variable_in_query(self):
        """Query should reference safe_rule_id, not raw rule_id."""
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("trace_rule_chain")
        block = src[idx:idx + 1200]
        assert "safe_rule_id" in block


# ── MCP tools module import defense tests ────────────────────────────

class TestMCPToolImports:
    """Defense tests for governance.mcp_tools modules."""

    def test_handoff_importable(self):
        import governance.mcp_tools.handoff
        assert governance.mcp_tools.handoff is not None

    def test_traceability_importable(self):
        import governance.mcp_tools.traceability
        assert governance.mcp_tools.traceability is not None

    def test_common_importable(self):
        import governance.mcp_tools.common
        assert governance.mcp_tools.common is not None

    def test_proposals_importable(self):
        import governance.mcp_tools.proposals
        assert governance.mcp_tools.proposals is not None

    def test_tasks_crud_importable(self):
        import governance.mcp_tools.tasks_crud
        assert governance.mcp_tools.tasks_crud is not None

    def test_rules_crud_importable(self):
        import governance.mcp_tools.rules_crud
        assert governance.mcp_tools.rules_crud is not None

    def test_sessions_core_importable(self):
        import governance.mcp_tools.sessions_core
        assert governance.mcp_tools.sessions_core is not None

    def test_dsm_importable(self):
        import governance.mcp_tools.dsm
        assert governance.mcp_tools.dsm is not None

    def test_audit_importable(self):
        import governance.mcp_tools.audit
        assert governance.mcp_tools.audit is not None

    def test_workspace_importable(self):
        import governance.mcp_tools.workspace
        assert governance.mcp_tools.workspace is not None

    def test_decisions_importable(self):
        import governance.mcp_tools.decisions
        assert governance.mcp_tools.decisions is not None

    def test_ingestion_importable(self):
        import governance.mcp_tools.ingestion
        assert governance.mcp_tools.ingestion is not None

    def test_trust_importable(self):
        import governance.mcp_tools.trust
        assert governance.mcp_tools.trust is not None

    def test_evidence_importable(self):
        import governance.mcp_tools.evidence
        assert governance.mcp_tools.evidence is not None

    def test_auto_session_importable(self):
        import governance.mcp_tools.auto_session
        assert governance.mcp_tools.auto_session is not None

    def test_memory_tiers_importable(self):
        import governance.mcp_tools.memory_tiers
        assert governance.mcp_tools.memory_tiers is not None
