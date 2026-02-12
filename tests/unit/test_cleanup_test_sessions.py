"""
Unit tests for Cleanup Test Sessions Script.

Per DOC-SIZE-01-v1: Tests for scripts/cleanup_test_sessions.py.
Tests: _is_test_session, _TEST_PATTERNS.
"""

from scripts.cleanup_test_sessions import _is_test_session, _TEST_PATTERNS


# ── _TEST_PATTERNS ────────────────────────────────────


class TestTestPatterns:
    def test_has_patterns(self):
        assert len(_TEST_PATTERNS) >= 20

    def test_all_start_with_chat(self):
        for pattern in _TEST_PATTERNS:
            assert pattern.startswith("CHAT-")


# ── _is_test_session ─────────────────────────────────


class TestIsTestSession:
    def test_agent_1_is_test(self):
        session = {"agent_id": "agent-1", "session_id": "S-1"}
        assert _is_test_session(session) is True

    def test_real_agent_not_test(self):
        session = {"agent_id": "code-agent", "session_id": "SESSION-2026-02-11-REAL"}
        assert _is_test_session(session) is False

    def test_chat_test_pattern(self):
        session = {"session_id": "SESSION-2026-02-11-CHAT-TEST", "agent_id": ""}
        assert _is_test_session(session) is True

    def test_chat_cvp_pattern(self):
        session = {"session_id": "SESSION-2026-02-11-CHAT-CVP-SWEEP", "agent_id": ""}
        assert _is_test_session(session) is True

    def test_chat_fallback_pattern(self):
        session = {"session_id": "SESSION-2026-02-11-CHAT-FALLBACK-END-TEST",
                    "agent_id": ""}
        assert _is_test_session(session) is True

    def test_chat_heuristic_pattern(self):
        session = {"session_id": "SESSION-2026-02-11-CHAT-HEURISTIC-CHECK",
                    "agent_id": ""}
        assert _is_test_session(session) is True

    def test_chat_with_test_in_description(self):
        session = {"session_id": "SESSION-2026-02-11-CHAT-RANDOM",
                    "agent_id": "", "description": "Test session for debugging"}
        assert _is_test_session(session) is True

    def test_chat_without_test_in_description(self):
        session = {"session_id": "SESSION-2026-02-11-CHAT-RANDOM",
                    "agent_id": "", "description": "Real work session"}
        assert _is_test_session(session) is False

    def test_non_chat_session(self):
        session = {"session_id": "SESSION-2026-02-11-BUGFIX",
                    "agent_id": "code-agent"}
        assert _is_test_session(session) is False

    def test_missing_fields(self):
        session = {}
        assert _is_test_session(session) is False

    def test_none_agent_id(self):
        session = {"agent_id": None, "session_id": "SESSION-2026-02-11-WORK"}
        assert _is_test_session(session) is False

    def test_each_pattern_detected(self):
        for pattern in _TEST_PATTERNS:
            session = {"session_id": f"SESSION-2026-02-11-{pattern}", "agent_id": ""}
            assert _is_test_session(session) is True, f"Pattern not detected: {pattern}"
