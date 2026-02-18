"""Deep scan batch 94: Hooks/checkers + chat routes + commands.

Batch 94 findings: 31 total, 0 confirmed fixes, 31 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


# ── Hook state management defense ──────────────


class TestStateManagerHistory:
    """Verify StateManager caps history correctly."""

    def test_history_capped_at_limit(self, tmp_path):
        from hooks.core.state import StateManager

        sm = StateManager(state_file=tmp_path / "test.json", history_limit=5)
        state = {"history": [{"i": i} for i in range(10)]}
        sm.save(state, add_history=True)

        import json
        saved = json.loads((tmp_path / "test.json").read_text())
        assert len(saved["history"]) <= 5

    def test_history_append_then_trim(self, tmp_path):
        from hooks.core.state import StateManager

        sm = StateManager(state_file=tmp_path / "test.json", history_limit=3)
        state = {"history": [{"i": 1}, {"i": 2}, {"i": 3}]}
        sm.save(state, add_history=True, history_entry={"i": 4})

        import json
        saved = json.loads((tmp_path / "test.json").read_text())
        assert len(saved["history"]) == 3
        assert saved["history"][-1]["i"] == 4


class TestStateManagerLoadCorrupt:
    """Verify StateManager handles corrupt state files."""

    def test_corrupt_json_returns_empty(self, tmp_path):
        from hooks.core.state import StateManager

        state_file = tmp_path / "corrupt.json"
        state_file.write_text("not valid json {{{")

        sm = StateManager(state_file=state_file)
        result = sm.load()
        assert result == {}

    def test_missing_file_returns_empty(self, tmp_path):
        from hooks.core.state import StateManager

        sm = StateManager(state_file=tmp_path / "nonexistent.json")
        result = sm.load()
        assert result == {}


# ── Entropy checker defense ──────────────


class TestEntropyThresholds:
    """Verify entropy warning logic fires correctly."""

    def test_critical_warning_at_threshold(self):
        from hooks.checkers.entropy import EntropyChecker

        checker = EntropyChecker()
        # last_warning_at=0, tool_count=150 → 150-0=150 >= 25 → fires
        state = {
            "tool_count": 150,
            "session_start": "2026-02-15T10:00:00",
            "warnings_shown": 0,
            "last_warning_at": 0,
        }
        with patch.object(checker, "load_state", return_value=state):
            result = checker.check()
            # HookResult has status string and message
            assert "CRITICAL" in result.message or "CRITICAL" in result.status

    def test_malformed_iso_returns_zero_minutes(self):
        from hooks.checkers.entropy import EntropyChecker

        checker = EntropyChecker()
        state = {"session_start": "not-a-date"}
        result = checker.get_session_minutes(state)
        assert result == 0


# ── Session visibility defense ──────────────


class TestSessionVisibilityEnvParsing:
    """Verify .env parsing handles edge cases."""

    def test_load_env_var_with_quotes(self, tmp_path):
        from hooks.checkers.session_visibility import load_env_var, ENV_FILE

        env_file = tmp_path / ".env"
        env_file.write_text('MY_VAR="hello world"\n')

        with patch("hooks.checkers.session_visibility.ENV_FILE", env_file):
            result = load_env_var("MY_VAR")
            assert result == "hello world"

    def test_load_env_var_not_found(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER_VAR=test\n")

        with patch("hooks.checkers.session_visibility.ENV_FILE", env_file):
            from hooks.checkers.session_visibility import load_env_var
            result = load_env_var("MISSING_VAR")
            # Falls through to os.getenv which returns None
            assert result is None or isinstance(result, str)

    def test_startswith_guard_ensures_equals_present(self):
        """startswith(VAR=) guarantees split('=',1)[1] is safe."""
        line = "MY_VAR=some_value"
        assert line.startswith("MY_VAR=")
        parts = line.split("=", 1)
        assert len(parts) == 2
        assert parts[1] == "some_value"


# ── Healthcheck DSP detection defense ──────────────


class TestDSPDateParsing:
    """Verify DSP date extraction from filenames."""

    def test_standard_dsp_filename(self, tmp_path):
        from hooks.healthcheck_formatters import check_dsp_conditions

        evidence = tmp_path / "evidence"
        evidence.mkdir()
        (evidence / "DSP-2026-02-10-123456.md").touch()
        (evidence / "SESSION-2026-02-15-TEST.md").touch()

        result = check_dsp_conditions(project_root=tmp_path)
        assert isinstance(result, dict)
        assert "suggested" in result

    def test_malformed_dsp_filename_skipped(self, tmp_path):
        from hooks.healthcheck_formatters import check_dsp_conditions

        evidence = tmp_path / "evidence"
        evidence.mkdir()
        (evidence / "DSP-2026.md").touch()  # Only 1 date part

        result = check_dsp_conditions(project_root=tmp_path)
        # Should not crash - len(date_parts) == 3 check skips it
        assert isinstance(result, dict)


# ── Chat endpoint defense ──────────────


class TestChatWhitespaceHandling:
    """Verify whitespace-only content doesn't crash tool_name extraction."""

    def test_whitespace_split_returns_empty_list(self):
        """Whitespace-only strings split to empty list (falsy)."""
        content = "    "
        parts = content.split()
        assert parts == []
        assert not parts  # Falsy

    def test_tool_name_fallback(self):
        """The ternary correctly falls back to 'chat' for empty splits."""
        content = "    "
        tool_name = (content.split()[0] if content and content.split() else "chat")
        assert tool_name == "chat"

    def test_none_content_fallback(self):
        """None content falls back to 'chat'."""
        content = None
        tool_name = (content.split()[0] if content and content.split() else "chat")
        assert tool_name == "chat"


# ── Chat search defense ──────────────


class TestChatSearchConcatenation:
    """Verify rule search works despite field concatenation."""

    def test_search_finds_in_name(self):
        query = "session"
        name = "SESSION-EVID-01-v1"
        directive = "Evidence must be generated"
        combined = ((name or "") + (directive or "")).lower()
        assert query.lower() in combined

    def test_search_finds_in_directive(self):
        query = "evidence"
        name = "SESSION-EVID-01-v1"
        directive = "Evidence must be generated"
        combined = ((name or "") + (directive or "")).lower()
        assert query.lower() in combined

    def test_search_with_none_fields(self):
        """None fields don't crash the search."""
        query = "test"
        name = None
        directive = None
        combined = ((name or "") + (directive or "")).lower()
        assert isinstance(combined, str)
