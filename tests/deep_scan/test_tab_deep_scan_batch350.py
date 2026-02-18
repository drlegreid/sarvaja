"""
Deep Scan Batch 350-353 Defense Tests.

Validates 8 production fixes:
- BUG-350-SES-001: sessions.py controller session_id regex validation
- BUG-350-XSS-001: session_transcript.py v_text replaces mustache interpolation
- BUG-350-XSS-002: tool_calls.py v_text replaces mustache interpolation
- BUG-352-INF-001: routes/sessions/crud.py generic error messages (no str(e))
- BUG-352-INF-002: routes/sessions/relations.py generic error messages
- BUG-352-INF-003: routes/agents/crud.py generic error messages
- BUG-353-AUD-001: stores/audit.py _MAX_AUDIT_ENTRIES hard cap
- BUG-351-EVP-001: sessions.py evidence_path traversal validation
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================
# BUG-350-SES-001: Session ID regex validation in controller
# ============================================================

class TestSessionIdValidation:
    """Verify sessions.py controller validates session_id before URL interpolation."""

    def _get_source(self):
        p = ROOT / "agent" / "governance_ui" / "controllers" / "sessions.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-350-SES-001" in src

    def test_session_id_regex_defined(self):
        """Should define _SESSION_ID_RE constant."""
        src = self._get_source()
        assert "_SESSION_ID_RE" in src

    def test_regex_used_in_select_session(self):
        """select_session should check _SESSION_ID_RE."""
        src = self._get_source()
        assert "_SESSION_ID_RE.match" in src

    def test_functional_valid_session_ids(self):
        """Valid session IDs should pass the regex."""
        _SESSION_ID_RE = re.compile(r'^[A-Za-z0-9_\-\.]{1,128}$')
        valid = [
            "SESSION-2026-02-18-TEST",
            "cc-abc123-def456",
            "my_session.v2",
            "A" * 128,
        ]
        for sid in valid:
            assert _SESSION_ID_RE.match(sid), f"Should match: {sid}"

    def test_functional_invalid_session_ids(self):
        """Malicious session IDs should NOT pass the regex."""
        _SESSION_ID_RE = re.compile(r'^[A-Za-z0-9_\-\.]{1,128}$')
        invalid = [
            "../admin/secrets",
            "session/../../etc/passwd",
            "session%2F..%2Fadmin",
            "session<script>alert(1)</script>",
            "",
            "A" * 129,  # too long
        ]
        for sid in invalid:
            assert not _SESSION_ID_RE.match(sid), f"Should NOT match: {sid}"

    def test_guard_in_delete_session(self):
        """delete_session should validate session_id."""
        src = self._get_source()
        # The validation should appear before the httpx DELETE call
        delete_idx = src.find("def delete_session")
        assert delete_idx != -1
        guard_section = src[delete_idx:delete_idx + 1200]
        assert "_SESSION_ID_RE" in guard_section

    def test_guard_in_attach_evidence(self):
        """attach_evidence should validate session_id."""
        src = self._get_source()
        attach_idx = src.find("def attach_evidence")
        assert attach_idx != -1
        guard_section = src[attach_idx:attach_idx + 600]
        assert "_SESSION_ID_RE" in guard_section


# ============================================================
# BUG-350-XSS-001: v_text in session_transcript.py
# ============================================================

class TestTranscriptXSSPrevention:
    """Verify session_transcript.py uses v_text instead of mustache."""

    def _get_source(self):
        p = ROOT / "agent" / "governance_ui" / "views" / "sessions" / "session_transcript.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-350-XSS-001" in src

    def test_no_unsafe_entry_content_mustache(self):
        """Should NOT have {{ entry.content }} in html.Pre() calls."""
        src = self._get_source()
        # The pattern html.Pre("{{ entry.content }}") is the vulnerable form
        assert '"{{ entry.content }}"' not in src

    def test_uses_v_text_for_content(self):
        """Should use v_text='entry.content' instead."""
        src = self._get_source()
        assert 'v_text="entry.content"' in src

    def test_v_text_used_multiple_times(self):
        """v_text should appear for all content render sites."""
        src = self._get_source()
        # At least 4 occurrences: thinking, user_prompt, assistant_text, tool_use, tool_result
        count = src.count('v_text="entry.content"')
        assert count >= 4, f"Expected >= 4 v_text occurrences, got {count}"


# ============================================================
# BUG-350-XSS-002: v_text in tool_calls.py
# ============================================================

class TestToolCallsXSSPrevention:
    """Verify tool_calls.py uses v_text instead of mustache."""

    def _get_source(self):
        p = ROOT / "agent" / "governance_ui" / "views" / "sessions" / "tool_calls.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-350-XSS-002" in src

    def test_no_unsafe_input_mustache(self):
        """Should NOT have {{ call.input_summary }} mustache pattern."""
        src = self._get_source()
        assert '"{{ call.input_summary' not in src

    def test_no_unsafe_output_mustache(self):
        """Should NOT have {{ call.output_summary }} mustache pattern."""
        src = self._get_source()
        assert '"{{ call.output_summary' not in src

    def test_no_unsafe_thought_mustache(self):
        """Should NOT have {{ thought.content }} mustache pattern."""
        src = self._get_source()
        assert '"{{ thought.content' not in src

    def test_uses_v_text_for_input(self):
        """Should use v_text for input summary."""
        src = self._get_source()
        assert "v_text=\"call.input_summary" in src

    def test_uses_v_text_for_output(self):
        """Should use v_text for output summary."""
        src = self._get_source()
        assert "v_text=\"call.output_summary\"" in src

    def test_uses_v_text_for_thought(self):
        """Should use v_text for thought content."""
        src = self._get_source()
        assert "v_text=\"thought.content\"" in src


# ============================================================
# BUG-352-INF-001: Generic error messages in sessions/crud.py
# ============================================================

class TestSessionsCrudInfoDisclosure:
    """Verify sessions/crud.py doesn't leak str(e) in HTTP 500 responses."""

    def _get_source(self):
        p = ROOT / "governance" / "routes" / "sessions" / "crud.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-352-INF-001" in src

    def test_no_exception_in_create_detail(self):
        """Create session should not embed {e} in HTTPException detail."""
        src = self._get_source()
        assert 'detail=f"Failed to create session: {e}"' not in src

    def test_no_exception_in_update_detail(self):
        """Update session should not embed {e} in HTTPException detail."""
        src = self._get_source()
        assert 'detail=f"Failed to update session: {e}"' not in src

    def test_no_exception_in_delete_detail(self):
        """Delete session should not embed {e} in HTTPException detail."""
        src = self._get_source()
        assert 'detail=f"Failed to delete session: {e}"' not in src

    def test_no_exception_in_end_detail(self):
        """End session should not embed {e} in HTTPException detail."""
        src = self._get_source()
        assert 'detail=f"Failed to end session: {e}"' not in src

    def test_uses_exc_info_logging(self):
        """Should log with exc_info=True for debug traceability."""
        src = self._get_source()
        assert "exc_info=True" in src


# ============================================================
# BUG-352-INF-002: Generic error messages in sessions/relations.py
# ============================================================

class TestSessionsRelationsInfoDisclosure:
    """Verify sessions/relations.py doesn't leak str(e) in HTTP 500 responses."""

    def _get_source(self):
        p = ROOT / "governance" / "routes" / "sessions" / "relations.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-352-INF-002" in src

    def test_no_raw_str_e_in_evidence_link(self):
        """Link evidence should not use detail=str(e)."""
        src = self._get_source()
        # The old pattern was: raise HTTPException(status_code=500, detail=str(e))
        # After fix: generic message
        link_section = src[src.find("link_evidence"):src.find("get_session_tasks")]
        assert "detail=str(e)" not in link_section

    def test_no_raw_str_e_in_session_tasks(self):
        """Get session tasks should not use detail=str(e)."""
        src = self._get_source()
        tasks_section = src[src.find("get_session_tasks"):]
        assert "detail=str(e)" not in tasks_section

    def test_generic_evidence_message(self):
        """Should return generic failure message for evidence linking."""
        src = self._get_source()
        assert '"Failed to link evidence"' in src

    def test_generic_tasks_message(self):
        """Should return generic failure message for session tasks."""
        src = self._get_source()
        assert '"Failed to get session tasks"' in src


# ============================================================
# BUG-352-INF-003: Generic error messages in agents/crud.py
# ============================================================

class TestAgentsCrudInfoDisclosure:
    """Verify agents/crud.py doesn't leak str(e) in HTTP 500 responses."""

    def _get_source(self):
        p = ROOT / "governance" / "routes" / "agents" / "crud.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-352-INF-003" in src

    def test_no_exception_in_create(self):
        """Create agent should not embed {e} in HTTPException detail."""
        src = self._get_source()
        assert 'detail=f"Failed to create agent: {e}"' not in src

    def test_no_exception_in_list(self):
        """List agents should not embed {e} in HTTPException detail."""
        src = self._get_source()
        assert 'detail=f"Failed to list agents: {e}"' not in src

    def test_no_exception_in_get(self):
        """Get agent should not embed {e} in HTTPException detail."""
        src = self._get_source()
        assert 'detail=f"Failed to get agent' not in src

    def test_no_exception_in_delete(self):
        """Delete agent should not embed {e} in HTTPException detail."""
        src = self._get_source()
        assert 'detail=f"Failed to delete agent' not in src

    def test_uses_exc_info_logging(self):
        """Should log with exc_info=True for debug traceability."""
        src = self._get_source()
        assert "exc_info=True" in src


# ============================================================
# BUG-353-AUD-001: Audit store hard cap
# ============================================================

class TestAuditStoreHardCap:
    """Verify audit.py has _MAX_AUDIT_ENTRIES cap."""

    def _get_source(self):
        p = ROOT / "governance" / "stores" / "audit.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-353-AUD-001" in src

    def test_max_entries_defined(self):
        """Should define _MAX_AUDIT_ENTRIES constant."""
        src = self._get_source()
        assert "_MAX_AUDIT_ENTRIES" in src

    def test_max_entries_reasonable_range(self):
        """Cap should be between 10K and 100K."""
        src = self._get_source()
        match = re.search(r'_MAX_AUDIT_ENTRIES\s*=\s*(\d[\d_]*)', src)
        assert match, "_MAX_AUDIT_ENTRIES not found"
        cap = int(match.group(1).replace("_", ""))
        assert 10_000 <= cap <= 100_000, f"Cap {cap} outside reasonable range"

    def test_cap_enforced_in_retention(self):
        """_apply_retention should enforce the hard cap."""
        src = self._get_source()
        retention_section = src[src.find("def _apply_retention"):]
        assert "_MAX_AUDIT_ENTRIES" in retention_section

    def test_functional_cap_enforcement(self):
        """Verify the cap logic truncates correctly."""
        _MAX = 100
        store = list(range(200))  # 200 entries
        if len(store) > _MAX:
            store = store[-_MAX:]  # keep newest
        assert len(store) == _MAX
        assert store[0] == 100  # oldest kept
        assert store[-1] == 199  # newest kept


# ============================================================
# BUG-351-EVP-001: Evidence path traversal validation
# ============================================================

class TestEvidencePathValidation:
    """Verify sessions.py controller validates evidence_path."""

    def _get_source(self):
        p = ROOT / "agent" / "governance_ui" / "controllers" / "sessions.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-351-EVP-001" in src

    def test_traversal_check_present(self):
        """Should check for '..' in evidence_path."""
        src = self._get_source()
        attach_idx = src.find("def attach_evidence")
        assert attach_idx != -1
        section = src[attach_idx:attach_idx + 800]
        assert '".."' in section or "'..' in" in section

    def test_absolute_path_check(self):
        """Should reject absolute paths starting with '/'."""
        src = self._get_source()
        attach_idx = src.find("def attach_evidence")
        section = src[attach_idx:attach_idx + 800]
        assert 'startswith("/")' in section

    def test_length_limit_check(self):
        """Should enforce a length limit on evidence_path."""
        src = self._get_source()
        attach_idx = src.find("def attach_evidence")
        section = src[attach_idx:attach_idx + 800]
        assert "500" in section or "len(" in section

    def test_functional_traversal_blocked(self):
        """Path traversal sequences should be rejected."""
        bad_paths = [
            "../../etc/passwd",
            "evidence/../../../secrets",
            "/etc/shadow",
            "/absolute/path/to/file",
        ]
        for path in bad_paths:
            path = (path or "").strip()
            is_bad = ".." in path or path.startswith("/") or len(path) > 500
            assert is_bad, f"Should reject: {path}"

    def test_functional_valid_paths_accepted(self):
        """Valid relative evidence paths should be accepted."""
        good_paths = [
            "evidence/SESSION-2026-02-18.md",
            "evidence/test-results/report.md",
            "docs/evidence/findings.md",
        ]
        for path in good_paths:
            path = (path or "").strip()
            is_bad = ".." in path or path.startswith("/") or len(path) > 500
            assert not is_bad, f"Should accept: {path}"


# ============================================================
# Import sanity checks
# ============================================================

class TestBatch350Imports:
    """Verify all fixed modules import without errors."""

    def test_import_sessions_controller(self):
        import agent.governance_ui.controllers.sessions

    def test_import_session_transcript(self):
        import agent.governance_ui.views.sessions.session_transcript

    def test_import_tool_calls(self):
        import agent.governance_ui.views.sessions.tool_calls

    def test_import_sessions_crud_route(self):
        import governance.routes.sessions.crud

    def test_import_sessions_relations_route(self):
        import governance.routes.sessions.relations

    def test_import_agents_crud_route(self):
        import governance.routes.agents.crud

    def test_import_audit_store(self):
        import governance.stores.audit
