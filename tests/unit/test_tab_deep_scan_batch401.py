"""Batch 401 — Route protection, info disclosure, client safety tests.

Validates fixes for:
- BUG-398-RUL-001..005: rules/crud.py str(e) → generic messages in HTTP responses
- BUG-398-OBS-001..008: observability.py unprotected service calls
- BUG-401-TRU-001: trust.py client allocation safety
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-398-RUL-001..005: rules/crud.py str(e) sanitization ─────────

class TestRulesCrudInfoDisclosure:
    """ValueError/KeyError handlers must NOT use str(e) in HTTPException detail."""

    def _check_no_str_e(self, src, handler_name):
        """Find handler and verify no str(e) in its except ValueError/KeyError blocks."""
        idx = src.index(f"def {handler_name}")
        # Find next def or EOF
        next_def = src.find("\ndef ", idx + 10)
        block = src[idx:next_def] if next_def != -1 else src[idx:]
        # Check all lines with 'detail=str(e)'
        lines = block.split("\n")
        violations = [i for i, line in enumerate(lines) if "detail=str(e)" in line]
        assert not violations, f"{handler_name} has str(e) in detail at relative lines: {violations}"

    def test_get_rule_no_str_e(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        self._check_no_str_e(src, "get_rule")

    def test_create_rule_no_str_e(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        self._check_no_str_e(src, "create_rule")

    def test_update_rule_no_str_e(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        self._check_no_str_e(src, "update_rule")

    def test_delete_rule_no_str_e(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        self._check_no_str_e(src, "delete_rule")

    def test_create_dependency_no_str_e(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        self._check_no_str_e(src, "create_rule_dependency")

    def test_bug_markers_present(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        for marker in ["BUG-398-RUL-001", "BUG-398-RUL-002", "BUG-398-RUL-003",
                        "BUG-398-RUL-004", "BUG-398-RUL-005"]:
            assert marker in src, f"Missing {marker}"

    def test_value_error_handlers_log_with_exc_info(self):
        """All ValueError handlers should log with exc_info=True."""
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        lines = src.split("\n")
        for i, line in enumerate(lines):
            if "except ValueError" in line:
                # Next few lines should contain exc_info=True
                block = "\n".join(lines[i:i + 4])
                assert "exc_info=True" in block, f"ValueError handler at line {i+1} missing exc_info"


# ── BUG-398-OBS-001..008: observability.py try/except wrappers ───────

class TestObservabilityProtection:
    """All service calls in observability.py must be wrapped in try/except."""

    def _get_handler_block(self, src, handler_name):
        idx = src.index(f"def {handler_name}")
        next_def = src.find("\ndef ", idx + 10)
        return src[idx:next_def] if next_def != -1 else src[idx:]

    def test_status_summary_protected(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        block = self._get_handler_block(src, "get_agents_status_summary")
        assert "try:" in block
        assert "except Exception" in block

    def test_stuck_agents_protected(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        block = self._get_handler_block(src, "get_stuck_agents")
        assert "try:" in block
        assert "except Exception" in block

    def test_stale_locks_protected(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        block = self._get_handler_block(src, "get_stale_locks")
        assert "try:" in block
        assert "except Exception" in block

    def test_heartbeat_protected(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        block = self._get_handler_block(src, "agent_heartbeat")
        assert "try:" in block
        assert "BUG-398-OBS-006" in block

    def test_acquire_lock_protected(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        block = self._get_handler_block(src, "acquire_lock")
        assert "try:" in block
        assert "BUG-398-OBS-007" in block

    def test_release_lock_protected(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        block = self._get_handler_block(src, "release_lock")
        assert "try:" in block
        assert "BUG-398-OBS-008" in block

    def test_conflicts_protected(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        block = self._get_handler_block(src, "get_merge_conflicts")
        assert "try:" in block
        assert "except Exception" in block

    def test_monitor_events_protected(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        block = self._get_handler_block(src, "get_monitor_events")
        assert "try:" in block
        assert "BUG-398-OBS-005" in block

    def test_all_error_responses_use_type_name(self):
        """Error detail strings should use type(e).__name__, not str(e)."""
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        assert "detail=str(e)" not in src
        assert "type(e).__name__" in src

    def test_bug_markers_present(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        for i in range(1, 9):
            assert f"BUG-398-OBS-00{i}" in src, f"Missing BUG-398-OBS-00{i}"


# ── BUG-401-TRU-001: trust.py client allocation safety ───────────────

class TestTrustClientAllocation:
    """Client must be allocated inside try to prevent NameError on finally."""

    def test_client_none_before_try(self):
        src = (SRC / "governance/mcp_tools/trust.py").read_text()
        idx = src.index("def governance_get_trust_score")
        block = src[idx:idx + 800]
        assert "client = None" in block

    def test_client_allocated_inside_try(self):
        src = (SRC / "governance/mcp_tools/trust.py").read_text()
        idx = src.index("def governance_get_trust_score")
        block = src[idx:idx + 800]
        # client = get_typedb_client() should be AFTER try:
        try_idx = block.index("try:")
        alloc_idx = block.index("client = get_typedb_client()")
        assert alloc_idx > try_idx, "Client allocation must be inside try block"

    def test_finally_guards_client(self):
        src = (SRC / "governance/mcp_tools/trust.py").read_text()
        assert "if client is not None:" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/trust.py").read_text()
        assert "BUG-401-TRU-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch401Imports:
    def test_rules_crud_route_importable(self):
        import governance.routes.rules.crud
        assert governance.routes.rules.crud is not None

    def test_trust_mcp_importable(self):
        import governance.mcp_tools.trust
        assert governance.mcp_tools.trust is not None
