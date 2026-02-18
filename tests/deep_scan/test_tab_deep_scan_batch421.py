"""Batch 421 — XSS guard, monitor exc_info, lifecycle exc_info,
evidence log level, persistence exc_info tests.

Validates fixes for:
- BUG-418-XSS-001..002: session_transcript.py v_text guards on tool_name
- BUG-420-MON-001..005: exc_info additions across 5 monitor helpers
- BUG-420-SLC-001: sessions_lifecycle.py auto-evidence exc_info
- BUG-420-EVD-001: session_evidence.py debug→warning + exc_info
- BUG-421-PER-001: session_persistence.py load warning exc_info
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


def _check_exc_info(src, fragment):
    """Find logger line containing fragment, verify exc_info=True."""
    idx = src.index(fragment)
    block = src[idx:idx + 300]
    assert "exc_info=True" in block, f"Missing exc_info=True near: {fragment}"


def _check_warning_level(src, fragment):
    """Verify line containing fragment uses logger.warning (not debug)."""
    idx = src.index(fragment)
    line_start = src.rindex("\n", 0, idx) + 1
    line_end = src.index("\n", idx)
    line = src[line_start:line_end]
    assert "logger.warning" in line, f"Expected logger.warning in: {line.strip()}"


# ── BUG-418-XSS-001..002: session_transcript.py v_text guards ──────────

class TestSessionTranscriptXSSGuards:
    def test_tool_use_name_uses_v_text(self):
        src = (SRC / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        # Find tool_use card section (inbound)
        idx = src.index("entry.entry_type === 'tool_use'")
        block = src[idx:idx + 600]
        # tool_name should use v_text, not mustache
        assert "v_text=\"entry.tool_name\"" in block, "tool_use tool_name should use v_text binding"

    def test_tool_result_name_uses_v_text(self):
        src = (SRC / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        # Find tool_result card section (outbound)
        idx = src.index("entry.entry_type === 'tool_result'")
        block = src[idx:idx + 600]
        assert "v_text=\"entry.tool_name || 'Result'\"" in block, "tool_result tool_name should use v_text binding"

    def test_no_mustache_tool_name_in_spans(self):
        src = (SRC / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        # Ensure no remaining {{ entry.tool_name }} mustache usage
        assert "{{ entry.tool_name }}" not in src, "Raw mustache {{ entry.tool_name }} still present"

    def test_bug_markers_present(self):
        src = (SRC / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        assert "BUG-418-XSS-001" in src
        assert "BUG-418-XSS-002" in src


# ── BUG-420-MON-001..005: monitor helper exc_info additions ────────────

class TestMonitorExcInfoBatch421:
    def test_agents_monitor_exc_info(self):
        src = (SRC / "governance/services/agents.py").read_text()
        _check_exc_info(src, "Monitor event failed for agent")

    def test_sessions_monitor_exc_info(self):
        src = (SRC / "governance/services/sessions.py").read_text()
        _check_exc_info(src, "Monitor event failed for session")

    def test_sessions_lifecycle_monitor_exc_info(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        _check_exc_info(src, "Monitor event failed for session")

    def test_tasks_mutations_monitor_exc_info(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        _check_exc_info(src, "Monitor event failed for task")

    def test_tasks_monitor_exc_info(self):
        src = (SRC / "governance/services/tasks.py").read_text()
        _check_exc_info(src, "Monitor event failed for task")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/agents.py").read_text()
        assert "BUG-420-MON-001" in src
        src2 = (SRC / "governance/services/sessions.py").read_text()
        assert "BUG-420-MON-002" in src2
        src3 = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        assert "BUG-420-MON-003" in src3
        src4 = (SRC / "governance/services/tasks_mutations.py").read_text()
        assert "BUG-420-MON-004" in src4
        src5 = (SRC / "governance/services/tasks.py").read_text()
        assert "BUG-420-MON-005" in src5


# ── BUG-420-SLC-001: sessions_lifecycle.py auto-evidence exc_info ──────

class TestSessionsLifecycleExcInfo:
    def test_auto_evidence_exc_info(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        _check_exc_info(src, "Auto-evidence generation failed for")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        assert "BUG-420-SLC-001" in src


# ── BUG-420-EVD-001: session_evidence.py debug→warning + exc_info ──────

class TestSessionEvidenceLogLevel:
    def test_duration_parse_warning_level(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        _check_warning_level(src, "Duration parse failed")

    def test_duration_parse_exc_info(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        _check_exc_info(src, "Duration parse failed")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        assert "BUG-420-EVD-001" in src


# ── BUG-421-PER-001: session_persistence.py load warning exc_info ──────

class TestSessionPersistenceExcInfo:
    def test_load_persisted_exc_info(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        _check_exc_info(src, "Failed to load persisted session")

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert "BUG-421-PER-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch421Imports:
    def test_session_transcript_importable(self):
        import agent.governance_ui.views.sessions.session_transcript
        assert agent.governance_ui.views.sessions.session_transcript is not None

    def test_agents_importable(self):
        import governance.services.agents
        assert governance.services.agents is not None

    def test_sessions_importable(self):
        import governance.services.sessions
        assert governance.services.sessions is not None

    def test_sessions_lifecycle_importable(self):
        import governance.services.sessions_lifecycle
        assert governance.services.sessions_lifecycle is not None

    def test_tasks_mutations_importable(self):
        import governance.services.tasks_mutations
        assert governance.services.tasks_mutations is not None

    def test_tasks_importable(self):
        import governance.services.tasks
        assert governance.services.tasks is not None

    def test_session_evidence_importable(self):
        import governance.services.session_evidence
        assert governance.services.session_evidence is not None

    def test_session_persistence_importable(self):
        import governance.stores.session_persistence
        assert governance.stores.session_persistence is not None
