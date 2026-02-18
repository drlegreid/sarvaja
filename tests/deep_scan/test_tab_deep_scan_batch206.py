"""Batch 206 — Session routes + chat endpoints defense tests.

Validates fixes for:
- BUG-206-RESPONSE-001: None guard on process_chat_command return
- BUG-206-CWD-001: __file__-based path in relations.py evidence fallback
- BUG-206-PURGE-001: _chat_gov_sessions cap to prevent memory leak
"""
from pathlib import Path
from unittest.mock import patch, MagicMock


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-206-RESPONSE-001: None response guard ───────────────────────

class TestChatResponseNoneGuard:
    """process_chat_command may return None — endpoints must guard."""

    def test_response_content_has_or_empty_guard(self):
        """endpoints.py must have `or ""` after process_chat_command."""
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        assert 'process_chat_command(request.content, agent_id) or ""' in src

    def test_response_content_never_none_in_record(self):
        """The result= kwarg in record_chat_tool_call must not slice None."""
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        # After the None guard, response_content is always a str
        assert "response_content[:500]" in src


# ── BUG-206-CWD-001: __file__-based path in relations.py ────────────

class TestRelationsEvidencePath:
    """_scan_evidence_filesystem must use __file__, not os.getcwd()."""

    def test_no_getcwd_in_scan_evidence(self):
        """relations.py must NOT use os.getcwd() for evidence dir."""
        src = (SRC / "governance/routes/sessions/relations.py").read_text()
        in_func = False
        found_getcwd = False
        for line in src.splitlines():
            if "def _scan_evidence_filesystem" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "getcwd()" in line:
                found_getcwd = True
        assert not found_getcwd, "_scan_evidence_filesystem must use __file__ not getcwd()"

    def test_uses_file_based_path(self):
        """relations.py must use __file__-based path for evidence dir."""
        src = (SRC / "governance/routes/sessions/relations.py").read_text()
        in_func = False
        found_file_ref = False
        for line in src.splitlines():
            if "def _scan_evidence_filesystem" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "__file__" in line:
                found_file_ref = True
        assert found_file_ref, "Must use __file__-based path"


# ── BUG-206-PURGE-001: _chat_gov_sessions cap ───────────────────────

class TestChatGovSessionsCap:
    """_chat_gov_sessions must have a size cap."""

    def test_cap_exists_in_endpoints(self):
        """endpoints.py must cap _chat_gov_sessions size."""
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        assert "len(_chat_gov_sessions)" in src and "200" in src

    def test_chat_gov_sessions_is_dict(self):
        """_chat_gov_sessions should be a dict."""
        from governance.routes.chat.endpoints import _chat_gov_sessions
        assert isinstance(_chat_gov_sessions, dict)


# ── Session detail routes defense ───────────────────────────────────

class TestSessionDetailDefense:
    """Defense tests for session detail routes."""

    def test_detail_route_exists(self):
        from governance.routes.sessions.detail import session_detail
        assert callable(session_detail)

    def test_tools_route_exists(self):
        from governance.routes.sessions.detail import session_tools
        assert callable(session_tools)

    def test_thoughts_route_exists(self):
        from governance.routes.sessions.detail import session_thoughts
        assert callable(session_thoughts)

    def test_evidence_rendered_route_exists(self):
        from governance.routes.sessions.detail import session_evidence_rendered
        assert callable(session_evidence_rendered)

    def test_evidence_rendered_uses_file_based_path(self):
        """detail.py must use __file__ not getcwd() for project_root."""
        src = (SRC / "governance/routes/sessions/detail.py").read_text()
        assert "os.path.dirname(__file__)" in src


# ── Relations route defense ─────────────────────────────────────────

class TestRelationsDefense:
    """Defense tests for session relations routes."""

    def test_link_evidence_route_exists(self):
        from governance.routes.sessions.relations import link_evidence_to_session
        assert callable(link_evidence_to_session)

    def test_get_session_tasks_route_exists(self):
        from governance.routes.sessions.relations import get_session_tasks
        assert callable(get_session_tasks)

    def test_get_session_evidence_route_exists(self):
        from governance.routes.sessions.relations import get_session_evidence
        assert callable(get_session_evidence)

    def test_scan_evidence_returns_list(self):
        """_scan_evidence_filesystem returns a list even if dir missing."""
        from governance.routes.sessions.relations import _scan_evidence_filesystem
        result = _scan_evidence_filesystem("NONEXISTENT-SESSION-999")
        assert isinstance(result, list)


# ── Transcript route defense ────────────────────────────────────────

class TestTranscriptDefense:
    """Defense tests for transcript routes."""

    def test_transcript_route_exists(self):
        from governance.routes.sessions.transcript import session_transcript
        assert callable(session_transcript)

    def test_transcript_entry_route_exists(self):
        from governance.routes.sessions.transcript import session_transcript_entry
        assert callable(session_transcript_entry)

    def test_per_page_bounded(self):
        """Main transcript endpoint must have le=200 bound."""
        src = (SRC / "governance/routes/sessions/transcript.py").read_text()
        assert "le=200" in src
