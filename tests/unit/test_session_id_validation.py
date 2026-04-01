"""
Tests for session ID regex validation (EPIC-PERF-TELEM-V1 Phase 1).

BDD Scenarios:
  - IDs with parentheses are accepted
  - IDs with dots are accepted
  - Path traversal IDs are rejected
  - Both regexes (sessions.py + sessions_detail_loaders.py) are consistent
"""

import re

import pytest


def _get_sessions_regex():
    """Import the regex from sessions.py."""
    from agent.governance_ui.controllers.sessions import _SESSION_ID_RE
    return _SESSION_ID_RE


def _get_detail_loaders_regex():
    """Import the regex from sessions_detail_loaders.py."""
    from agent.governance_ui.controllers.sessions_detail_loaders import _SESSION_ID_RE
    return _SESSION_ID_RE


def _get_valid_session_id():
    """Import _valid_session_id from sessions_detail_loaders.py."""
    from agent.governance_ui.controllers.sessions_detail_loaders import _valid_session_id
    return _valid_session_id


class TestSessionIdWithParentheses:
    """Scenario: IDs with parentheses are accepted."""

    PAREN_IDS = [
        "SESSION-2026-03-26-CHECK-(RULE)",
        "SESSION-2026-03-26-FIX-(BUG-001)",
        "SESSION-(test)",
    ]

    @pytest.mark.parametrize("session_id", PAREN_IDS)
    def test_sessions_regex_accepts_parens(self, session_id):
        """sessions.py _SESSION_ID_RE accepts IDs with parentheses."""
        regex = _get_sessions_regex()
        assert regex.match(session_id), (
            f"sessions.py regex should accept '{session_id}'"
        )

    @pytest.mark.parametrize("session_id", PAREN_IDS)
    def test_detail_loaders_regex_accepts_parens(self, session_id):
        """sessions_detail_loaders.py _SESSION_ID_RE accepts IDs with parentheses."""
        regex = _get_detail_loaders_regex()
        assert regex.match(session_id), (
            f"sessions_detail_loaders.py regex should accept '{session_id}'"
        )

    @pytest.mark.parametrize("session_id", PAREN_IDS)
    def test_valid_session_id_accepts_parens(self, session_id):
        """_valid_session_id() returns True for IDs with parentheses."""
        valid_fn = _get_valid_session_id()
        assert valid_fn(session_id) is True, (
            f"_valid_session_id should accept '{session_id}'"
        )


class TestSessionIdWithDots:
    """Scenario: IDs with dots are accepted."""

    DOT_IDS = [
        "SESSION-2026.03.26-TEST",
        "session.with.dots",
    ]

    @pytest.mark.parametrize("session_id", DOT_IDS)
    def test_sessions_regex_accepts_dots(self, session_id):
        regex = _get_sessions_regex()
        assert regex.match(session_id)

    @pytest.mark.parametrize("session_id", DOT_IDS)
    def test_detail_loaders_regex_accepts_dots(self, session_id):
        regex = _get_detail_loaders_regex()
        assert regex.match(session_id)


class TestPathTraversalRejected:
    """Scenario: Path traversal IDs are rejected."""

    INVALID_IDS = [
        "../../etc/passwd",
        "../secret",
        "session/../../etc",
        "session id with spaces",
        "",
        "a" * 201,  # exceeds 200 char limit
        'session"injection',
        "session;drop",
    ]

    @pytest.mark.parametrize("session_id", INVALID_IDS)
    def test_sessions_regex_rejects_traversal(self, session_id):
        """sessions.py regex rejects path traversal and injection."""
        regex = _get_sessions_regex()
        assert not regex.match(session_id), (
            f"sessions.py regex should reject '{session_id}'"
        )

    @pytest.mark.parametrize("session_id", INVALID_IDS)
    def test_valid_session_id_rejects_traversal(self, session_id):
        """_valid_session_id() returns False for invalid IDs."""
        valid_fn = _get_valid_session_id()
        assert valid_fn(session_id) is False, (
            f"_valid_session_id should reject '{session_id!r}'"
        )


class TestRegexConsistency:
    """Both regexes should accept the same character set."""

    NORMAL_IDS = [
        "SESSION-2026-03-26-WORK",
        "simple_id",
        "A",
        "session-with-hyphens",
    ]

    @pytest.mark.parametrize("session_id", NORMAL_IDS)
    def test_both_regexes_accept_normal_ids(self, session_id):
        """Both regexes accept standard session IDs."""
        r1 = _get_sessions_regex()
        r2 = _get_detail_loaders_regex()
        assert r1.match(session_id), f"sessions.py should accept '{session_id}'"
        assert r2.match(session_id), f"detail_loaders should accept '{session_id}'"

    def test_max_length_200(self):
        """Both regexes enforce 200-char max."""
        long_id = "A" * 200
        too_long = "A" * 201
        r1 = _get_sessions_regex()
        r2 = _get_detail_loaders_regex()
        assert r1.match(long_id)
        assert r2.match(long_id)
        assert not r1.match(too_long)
        assert not r2.match(too_long)
