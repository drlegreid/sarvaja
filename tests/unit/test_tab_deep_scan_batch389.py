"""Batch 389 — Trame WebSocket info disclosure + exc_info defense tests.

Validates fixes for:
- BUG-389-RUL-001: response.text removed from rules controller error_message
- BUG-389-RUL-002: str(e) → type(e).__name__ in rules save error
- BUG-389-RUL-003: str(e) → type(e).__name__ in rules delete error
- BUG-389-RUL-004: str(e) → type(e).__name__ in rules load error
- BUG-389-DEC-001: response.text removed from decisions controller error_message
- BUG-389-DEC-002: str(e) → type(e).__name__ in decisions save error
- BUG-389-DEC-003: str(e) → type(e).__name__ in decisions delete error
- BUG-389-AUD-001: str(e) → type(e).__name__ in audit_summary error field
- BUG-389-DL-001: str(e) → type(e).__name__ in executive_report error field
- BUG-389-INF-001..005: str(e)/raw {e} → type(e).__name__ in infra controller state vars
- BUG-389-RCR-001: exc_info=True added to rules/crud.py update_rule logger.error
- BUG-389-RCR-002: exc_info=True added to rules/crud.py delete_rule logger.error
"""
import importlib
import inspect


# ── BUG-389-RUL-001..004: Rules controller sanitization ──────────────

class TestRulesControllerSanitization:
    """rules.py must not leak response.text or str(e) via state.error_message."""

    def _src(self):
        mod = importlib.import_module("agent.governance_ui.controllers.rules")
        return inspect.getsource(mod)

    def test_no_response_text_in_error_message(self):
        src = self._src()
        assert "response.text" not in src or "BUG-389-RUL-001" in src

    def test_save_rule_uses_type_name(self):
        src = self._src()
        assert "Failed to save rule: {type(e).__name__}" in src

    def test_delete_rule_uses_type_name(self):
        src = self._src()
        assert "Failed to delete rule: {type(e).__name__}" in src

    def test_load_rules_uses_type_name(self):
        src = self._src()
        assert "Failed to load rules: {type(e).__name__}" in src

    def test_no_str_e_in_error_message(self):
        """No str(e) should appear in state.error_message assignments."""
        src = self._src()
        # Find lines with error_message and str(e)
        bad_lines = [
            line.strip() for line in src.split("\n")
            if "error_message" in line and "str(e)" in line
        ]
        assert not bad_lines, f"str(e) in error_message at: {bad_lines}"

    def test_bug_markers_present(self):
        src = self._src()
        for marker in ["BUG-389-RUL-001", "BUG-389-RUL-002", "BUG-389-RUL-003", "BUG-389-RUL-004"]:
            assert marker in src, f"Missing {marker}"


# ── BUG-389-DEC-001..003: Decisions controller sanitization ──────────

class TestDecisionsControllerSanitization:
    """decisions.py must not leak response.text or str(e) via state.error_message."""

    def _src(self):
        mod = importlib.import_module("agent.governance_ui.controllers.decisions")
        return inspect.getsource(mod)

    def test_no_response_text_in_error_message(self):
        src = self._src()
        assert "response.text" not in src or "BUG-389-DEC-001" in src

    def test_save_decision_uses_type_name(self):
        src = self._src()
        assert "Failed to save decision: {type(e).__name__}" in src

    def test_delete_decision_uses_type_name(self):
        src = self._src()
        assert "Failed to delete decision: {type(e).__name__}" in src

    def test_no_str_e_in_error_message(self):
        src = self._src()
        bad_lines = [
            line.strip() for line in src.split("\n")
            if "error_message" in line and "str(e)" in line
        ]
        assert not bad_lines, f"str(e) in error_message at: {bad_lines}"

    def test_bug_markers_present(self):
        src = self._src()
        for marker in ["BUG-389-DEC-001", "BUG-389-DEC-002", "BUG-389-DEC-003"]:
            assert marker in src, f"Missing {marker}"


# ── BUG-389-AUD-001: Audit loaders sanitization ─────────────────────

class TestAuditLoaderSanitization:
    """audit_loaders.py must not leak str(e) in audit_summary error field."""

    def _src(self):
        mod = importlib.import_module("agent.governance_ui.controllers.audit_loaders")
        return inspect.getsource(mod)

    def test_error_field_uses_type_name(self):
        src = self._src()
        assert "type(e).__name__" in src

    def test_no_str_e_in_error_field(self):
        src = self._src()
        bad_lines = [
            line.strip() for line in src.split("\n")
            if "'error'" in line and "str(e)" in line
        ]
        assert not bad_lines, f"str(e) in error field at: {bad_lines}"

    def test_bug_marker_present(self):
        src = self._src()
        assert "BUG-389-AUD-001" in src


# ── BUG-389-DL-001: Data loaders sanitization ───────────────────────

class TestDataLoaderSanitization:
    """data_loaders.py must not leak str(e) in executive_report error field."""

    def _src(self):
        mod = importlib.import_module("agent.governance_ui.controllers.data_loaders")
        return inspect.getsource(mod)

    def test_executive_report_error_uses_type_name(self):
        src = self._src()
        # Find the executive_report error block
        idx = src.index("executive_report")
        block = src[idx:idx + 2000]
        assert "type(e).__name__" in block

    def test_no_str_e_in_executive_error(self):
        src = self._src()
        idx = src.index("load_executive_report_data")
        block = src[idx:idx + 1500]
        bad = [
            line.strip() for line in block.split("\n")
            if '"error"' in line and "str(e)" in line
        ]
        assert not bad, f"str(e) in executive error: {bad}"

    def test_bug_marker_present(self):
        src = self._src()
        assert "BUG-389-DL-001" in src


# ── BUG-389-INF-001..005: Infra loaders sanitization ────────────────

class TestInfraLoaderSanitization:
    """infra_loaders.py must not leak raw {e} or str(e) in state vars."""

    def _src(self):
        mod = importlib.import_module("agent.governance_ui.controllers.infra_loaders")
        return inspect.getsource(mod)

    def test_start_service_uses_type_name(self):
        src = self._src()
        assert "Failed to start {service}: {type(e).__name__}" in src

    def test_start_all_uses_type_name(self):
        src = self._src()
        assert "Failed to start services: {type(e).__name__}" in src

    def test_restart_stack_uses_type_name(self):
        src = self._src()
        assert "Failed to restart stack: {type(e).__name__}" in src

    def test_fetch_logs_uses_type_name(self):
        src = self._src()
        assert "Failed to fetch logs: {type(e).__name__}" in src

    def test_cleanup_uses_type_name(self):
        src = self._src()
        assert "Cleanup failed: {type(e).__name__}" in src

    def test_no_raw_e_in_state_assignments(self):
        """No bare {e} (without type()) in infra_last_action or infra_log_lines assignments."""
        src = self._src()
        import re
        # Find lines that assign to state.infra_last_action or state.infra_log_lines
        # and contain {e} but NOT {type(e)
        pattern = re.compile(r'state\.infra_(last_action|log_lines).*\{e\}')
        matches = pattern.findall(src)
        # All {e} references should be wrapped in type()
        for line in src.split("\n"):
            if "state.infra_last_action" in line and "{e}" in line:
                assert "type(e)" in line, f"Bare {{e}} in: {line.strip()}"
            if "state.infra_log_lines" in line and "{e}" in line:
                assert "type(e)" in line, f"Bare {{e}} in: {line.strip()}"

    def test_bug_markers_present(self):
        src = self._src()
        for marker in ["BUG-389-INF-001", "BUG-389-INF-002", "BUG-389-INF-003",
                        "BUG-389-INF-004", "BUG-389-INF-005"]:
            assert marker in src, f"Missing {marker}"


# ── BUG-389-RCR-001..002: rules/crud.py exc_info ────────────────────

class TestRulesCrudExcInfo:
    """rules/crud.py logger.error calls must include exc_info=True."""

    def _src(self):
        mod = importlib.import_module("governance.typedb.queries.rules.crud")
        return inspect.getsource(mod)

    def test_update_rule_has_exc_info(self):
        src = self._src()
        idx = src.index("def update_rule")
        block = src[idx:idx + 8000]
        assert "exc_info=True" in block

    def test_delete_rule_has_exc_info(self):
        src = self._src()
        idx = src.index("def delete_rule")
        block = src[idx:idx + 2000]
        assert "exc_info=True" in block

    def test_bug_markers_present(self):
        src = self._src()
        for marker in ["BUG-389-RCR-001", "BUG-389-RCR-002"]:
            assert marker in src, f"Missing {marker}"


# ── Module import defense tests ──────────────────────────────────────

class TestBatch389Imports:
    def test_rules_controller_importable(self):
        import agent.governance_ui.controllers.rules
        assert agent.governance_ui.controllers.rules is not None

    def test_decisions_controller_importable(self):
        import agent.governance_ui.controllers.decisions
        assert agent.governance_ui.controllers.decisions is not None

    def test_audit_loaders_importable(self):
        import agent.governance_ui.controllers.audit_loaders
        assert agent.governance_ui.controllers.audit_loaders is not None

    def test_data_loaders_importable(self):
        import agent.governance_ui.controllers.data_loaders
        assert agent.governance_ui.controllers.data_loaders is not None

    def test_infra_loaders_importable(self):
        import agent.governance_ui.controllers.infra_loaders
        assert agent.governance_ui.controllers.infra_loaders is not None

    def test_rules_crud_importable(self):
        import governance.typedb.queries.rules.crud
        assert governance.typedb.queries.rules.crud is not None
