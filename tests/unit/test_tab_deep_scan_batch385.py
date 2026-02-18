"""
Deep Scan Batch 385 — Defense Tests
====================================
Verifies BUG-385-SES-001 through BUG-385-INF-002.

Batch 382-385 findings:
- BUG-385-SES-001: controllers/sessions.py save error sanitized (1 fix)
- BUG-385-SES-002: controllers/sessions.py delete error sanitized (1 fix)
- BUG-385-SES-003: controllers/sessions.py attach evidence error sanitized (1 fix)
- BUG-385-TRS-001: controllers/trust.py toggle_agent_pause error sanitized (1 fix)
- BUG-385-TRS-002: controllers/trust.py register_agent error sanitized (1 fix)
- BUG-385-HND-001: mcp_tools/handoff.py handoff_create path redacted (1 fix)
- BUG-385-HND-002: mcp_tools/handoff.py handoff_get path redacted (1 fix)
- BUG-385-LCY-001: sessions_lifecycle.py dict/dataclass dual guard (1 fix)
- BUG-385-REL-001: tasks/relationships.py control char stripping (8 escape sites)
- BUG-385-INF-001: rules/inference.py control char stripping (5 escape sites)
- BUG-385-INF-002: rules/inference.py exc_info=True added (4 logger.error calls)

Total: 22 production fixes, verified by source introspection tests.
"""

import importlib
import inspect
import re

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_source(module_path: str) -> str:
    """Get source code of a module by dotted path."""
    mod = importlib.import_module(module_path)
    return inspect.getsource(mod)


# ===========================================================================
# BUG-385-SES-001/002/003: controllers/sessions.py — str(e) sanitized
# ===========================================================================

class TestSessionsControllerSanitization:
    """Verify sessions controller no longer leaks str(e) in state.error_message."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("agent.governance_ui.controllers.sessions")

    def test_bug_ses_001_marker(self):
        assert "BUG-385-SES-001" in self.source

    def test_bug_ses_002_marker(self):
        assert "BUG-385-SES-002" in self.source

    def test_bug_ses_003_marker(self):
        assert "BUG-385-SES-003" in self.source

    def test_no_str_e_in_error_message(self):
        """state.error_message assignments should not use str(e) or {e}."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "error_message" in stripped and "str(e)" in stripped:
                # Skip comments
                if stripped.startswith("#"):
                    continue
                pytest.fail(f"str(e) in error_message: {stripped}")

    def test_save_session_uses_type_name(self):
        """save session error should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Failed to save session" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "save session error should use type(e).__name__"

    def test_delete_session_uses_type_name(self):
        """delete session error should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Failed to delete session" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "delete session error should use type(e).__name__"

    def test_attach_evidence_uses_type_name(self):
        """attach evidence error should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Failed to attach evidence" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "attach evidence error should use type(e).__name__"


# ===========================================================================
# BUG-385-TRS-001/002: controllers/trust.py — str(e) sanitized
# ===========================================================================

class TestTrustControllerSanitization:
    """Verify trust controller no longer leaks str(e) in status_message."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("agent.governance_ui.controllers.trust")

    def test_bug_trs_001_marker(self):
        assert "BUG-385-TRS-001" in self.source

    def test_bug_trs_002_marker(self):
        assert "BUG-385-TRS-002" in self.source

    def test_no_raw_e_in_status_message(self):
        """status_message should not use raw {e} or str(e)."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "status_message" in stripped:
                if "str(e)" in stripped:
                    pytest.fail(f"str(e) in status_message: {stripped}")
                # Check for raw f-string {e} without type()
                if re.search(r'\{e\}', stripped) and "type(e)" not in stripped:
                    pytest.fail(f"Raw {{e}} in status_message: {stripped}")

    def test_toggle_agent_uses_type_name(self):
        """toggle agent error should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Error toggling agent" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "toggle agent error should use type(e).__name__"

    def test_register_agent_uses_type_name(self):
        """register agent error should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Registration failed" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "register agent error should use type(e).__name__"


# ===========================================================================
# BUG-385-HND-001/002: mcp_tools/handoff.py — path redacted
# ===========================================================================

class TestHandoffPathRedaction:
    """Verify handoff MCP tools no longer expose absolute paths."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.mcp_tools.handoff")

    def test_bug_hnd_001_marker(self):
        assert "BUG-385-HND-001" in self.source

    def test_bug_hnd_002_marker(self):
        assert "BUG-385-HND-002" in self.source

    def test_no_str_filepath_in_result(self):
        """evidence_file should use filepath.name, not str(filepath)."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "evidence_file" in stripped and "str(filepath)" in stripped:
                pytest.fail(f"str(filepath) in evidence_file: {stripped}")

    def test_handoff_create_uses_name(self):
        """handoff_create evidence_file should use filepath.name."""
        found = False
        for line in self.source.splitlines():
            if "evidence_file" in line and "filepath.name" in line:
                found = True
                break
        assert found, "evidence_file should use filepath.name"

    def test_handoff_get_uses_name(self):
        """handoff_get evidence_file should use filepath.name."""
        count = self.source.count("filepath.name")
        assert count >= 2, f"Expected >=2 filepath.name usages, found {count}"


# ===========================================================================
# BUG-385-LCY-001: sessions_lifecycle.py — dict/dataclass dual guard
# ===========================================================================

class TestSessionsLifecycleDualGuard:
    """Verify end_session handles both dict and dataclass session objects."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.services.sessions_lifecycle")

    def test_bug_marker_present(self):
        assert "BUG-385-LCY-001" in self.source

    def test_isinstance_check_present(self):
        """Status check should use isinstance(session, dict) guard."""
        found = False
        for line in self.source.splitlines():
            if "isinstance(session, dict)" in line and "get" in line:
                found = True
                break
        assert found, "end_session should check isinstance(session, dict)"

    def test_both_dict_and_getattr_paths(self):
        """Both .get() and getattr() should be present in the guard."""
        found = False
        for line in self.source.splitlines():
            if "session.get" in line and "getattr" in line and "status" in line:
                found = True
                break
        assert found, "Dual path (dict .get + dataclass getattr) must exist"


# ===========================================================================
# BUG-385-REL-001: tasks/relationships.py — control char stripping
# ===========================================================================

class TestRelationshipsControlCharStripping:
    """Verify TypeQL escaping includes control character stripping."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.typedb.queries.tasks.relationships")

    def test_bug_marker_present(self):
        assert "BUG-385-REL-001" in self.source

    def test_newline_stripping_in_write_escapes(self):
        """All write-path escape sites should strip newlines."""
        escape_lines = [
            l for l in self.source.splitlines()
            if "_esc = " in l or "tid = " in l
        ]
        for line in escape_lines:
            if "replace" in line:
                assert "'\\n'" in line or '"\\n"' in line, \
                    f"Missing newline strip: {line.strip()}"

    def test_carriage_return_stripping(self):
        """Escape sites should also strip carriage returns."""
        escape_lines = [
            l for l in self.source.splitlines()
            if ("_esc = " in l or "tid = " in l) and "replace" in l
        ]
        for line in escape_lines:
            assert "'\\r'" in line or '"\\r"' in line, \
                f"Missing carriage return strip: {line.strip()}"

    def test_tab_stripping(self):
        """Escape sites should also strip tabs."""
        escape_lines = [
            l for l in self.source.splitlines()
            if ("_esc = " in l or "tid = " in l) and "replace" in l
        ]
        for line in escape_lines:
            assert "'\\t'" in line or '"\\t"' in line, \
                f"Missing tab strip: {line.strip()}"

    def test_all_escape_sites_hardened(self):
        """All 8 escape sites should have control char stripping."""
        count = self.source.count("BUG-385-REL-001")
        assert count >= 8, f"Expected >=8 BUG-385-REL-001 markers, found {count}"


# ===========================================================================
# BUG-385-INF-001/002: rules/inference.py — control chars + exc_info
# ===========================================================================

class TestInferenceControlCharsAndExcInfo:
    """Verify inference.py has control char stripping and exc_info=True."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.typedb.queries.rules.inference")

    def test_bug_inf_001_marker(self):
        assert "BUG-385-INF-001" in self.source

    def test_bug_inf_002_marker(self):
        assert "BUG-385-INF-002" in self.source

    def test_all_escapes_strip_newlines(self):
        """All TypeQL escape sites should strip newlines."""
        for line in self.source.splitlines():
            if ("rid = " in line or "did = " in line or
                "dep_id_esc = " in line or "dep_on_esc = " in line):
                if "replace" in line:
                    assert "'\\n'" in line or '"\\n"' in line, \
                        f"Missing newline strip: {line.strip()}"

    def test_all_logger_error_have_exc_info(self):
        """All logger.error calls should have exc_info=True."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "logger.error(" in stripped and "query failed" in stripped:
                assert "exc_info=True" in stripped, \
                    f"Missing exc_info=True: {stripped}"

    def test_exc_info_count(self):
        """At least 4 logger.error calls should have exc_info=True."""
        count = sum(
            1 for l in self.source.splitlines()
            if "logger.error(" in l and "exc_info=True" in l
        )
        assert count >= 4, f"Expected >=4 exc_info=True, found {count}"


# ===========================================================================
# Import Verification
# ===========================================================================

class TestBatch385Imports:
    """Verify all modified modules import cleanly."""

    @pytest.mark.parametrize("module_path", [
        "agent.governance_ui.controllers.sessions",
        "agent.governance_ui.controllers.trust",
        "governance.mcp_tools.handoff",
        "governance.services.sessions_lifecycle",
        "governance.typedb.queries.tasks.relationships",
        "governance.typedb.queries.rules.inference",
    ])
    def test_module_imports(self, module_path):
        mod = importlib.import_module(module_path)
        assert mod is not None
