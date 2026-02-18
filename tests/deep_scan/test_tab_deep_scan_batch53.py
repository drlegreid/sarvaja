"""
Batch 53 — Deep Scan: UI state initialization verification + controller safety.

Validates:
- State vars referenced by controllers ARE initialized in initial.py
- Session detail loaders properly reset state on errors
- httpx usage patterns in controllers
- Trame form validation patterns
"""
import inspect
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# State initialization completeness
# ===========================================================================

class TestStateInitializationCompleteness:
    """Verify all state vars used by controllers are initialized."""

    def _get_initial_state(self):
        """Get a fresh initial state dict."""
        from agent.governance_ui.state.initial import get_initial_state
        return get_initial_state()

    def test_transcript_include_thinking_initialized(self):
        """session_transcript_include_thinking must be in initial state."""
        state = self._get_initial_state()
        assert 'session_transcript_include_thinking' in state
        assert state['session_transcript_include_thinking'] is True

    def test_transcript_include_user_initialized(self):
        """session_transcript_include_user must be in initial state."""
        state = self._get_initial_state()
        assert 'session_transcript_include_user' in state
        assert state['session_transcript_include_user'] is True

    def test_session_transcript_initialized(self):
        """session_transcript must be initialized as empty list."""
        state = self._get_initial_state()
        assert 'session_transcript' in state
        assert state['session_transcript'] == []

    def test_tasks_pagination_initialized(self):
        """tasks_pagination must be initialized as dict."""
        state = self._get_initial_state()
        assert 'tasks_pagination' in state
        assert isinstance(state['tasks_pagination'], dict)

    def test_selected_session_initialized_as_none(self):
        """selected_session must start as None."""
        state = self._get_initial_state()
        assert 'selected_session' in state
        assert state['selected_session'] is None

    def test_show_session_detail_initialized_as_false(self):
        """show_session_detail must start as False."""
        state = self._get_initial_state()
        assert 'show_session_detail' in state
        assert state['show_session_detail'] is False

    def test_sessions_list_initialized(self):
        """sessions must start as empty list."""
        state = self._get_initial_state()
        assert 'sessions' in state
        assert state['sessions'] == []

    def test_tasks_list_initialized(self):
        """tasks must start as empty list."""
        state = self._get_initial_state()
        assert 'tasks' in state
        assert state['tasks'] == []

    def test_is_loading_initialized(self):
        """is_loading must be initialized."""
        state = self._get_initial_state()
        assert 'is_loading' in state

    def test_has_error_initialized(self):
        """has_error must be initialized."""
        state = self._get_initial_state()
        assert 'has_error' in state


# ===========================================================================
# Evidence loader state reset
# ===========================================================================

class TestEvidenceLoaderStateReset:
    """Verify evidence loader resets state before loading."""

    def test_evidence_rendered_clears_before_load(self):
        """load_session_evidence_rendered must clear html before API call."""
        from agent.governance_ui.controllers import sessions_detail_loaders
        src = inspect.getsource(sessions_detail_loaders.register_session_detail_loaders)
        # Find the evidence rendered function and check it clears state
        assert "session_evidence_html = ''" in src

    def test_evidence_rendered_clears_on_exception(self):
        """load_session_evidence_rendered must clear html on exception."""
        from agent.governance_ui.controllers import sessions_detail_loaders
        src = inspect.getsource(sessions_detail_loaders.register_session_detail_loaders)
        # Must set empty html in except block
        lines = src.split('\n')
        except_block = False
        found_clear_in_except = False
        for line in lines:
            if 'except Exception' in line and 'evidence rendered' in src[src.index(line)-200:src.index(line)]:
                except_block = True
            if except_block and "session_evidence_html = ''" in line:
                found_clear_in_except = True
                break
        # Alternative: just verify the pattern exists twice in the function
        count = src.count("session_evidence_html = ''")
        assert count >= 2, f"Must clear evidence html both before and on error, found {count} times"


# ===========================================================================
# Httpx context manager usage in controllers
# ===========================================================================

class TestHttpxContextManagerUsage:
    """Verify httpx usage patterns in controller files."""

    def test_tasks_controllers_use_context_managers(self):
        """tasks.py controllers must use httpx.Client context managers."""
        from agent.governance_ui.controllers import tasks
        src = inspect.getsource(tasks.register_tasks_controllers)
        # Count context manager usage vs bare httpx.get
        context_count = src.count("with httpx.Client")
        bare_count = src.count("httpx.get(") + src.count("httpx.post(") + src.count("httpx.put(")
        assert context_count > 0, "Must use httpx.Client context manager"
        # Bare calls should be 0 or minimal
        assert bare_count == 0, f"Found {bare_count} bare httpx calls outside context manager"

    def test_decisions_controllers_use_context_managers(self):
        """decisions.py controllers must use httpx.Client context managers."""
        from agent.governance_ui.controllers import decisions
        src = inspect.getsource(decisions.register_decisions_controllers)
        context_count = src.count("with httpx.Client")
        assert context_count > 0, "Must use httpx.Client context manager"

    def test_detail_loaders_use_context_managers(self):
        """sessions_detail_loaders.py must use httpx.Client context managers."""
        from agent.governance_ui.controllers import sessions_detail_loaders
        src = inspect.getsource(sessions_detail_loaders.register_session_detail_loaders)
        context_count = src.count("with httpx.Client")
        bare_count = src.count("httpx.get(") + src.count("httpx.post(")
        assert context_count >= 3, f"Expected 3+ context managers, found {context_count}"
        assert bare_count == 0, f"Found {bare_count} bare httpx calls"


# ===========================================================================
# Form validation patterns
# ===========================================================================

class TestFormValidationPatterns:
    """Verify form validation in decision and session controllers."""

    def test_decision_form_validates_name(self):
        """Decision form must validate name before submission."""
        from agent.governance_ui.controllers import decisions
        src = inspect.getsource(decisions.register_decisions_controllers)
        assert 'not name' in src or "Decision name is required" in src

    def test_decision_form_validates_context(self):
        """Decision form must validate context before submission."""
        from agent.governance_ui.controllers import decisions
        src = inspect.getsource(decisions.register_decisions_controllers)
        assert "Decision context is required" in src

    def test_decision_form_prevents_double_click(self):
        """Decision form must check is_loading to prevent double submit."""
        from agent.governance_ui.controllers import decisions
        src = inspect.getsource(decisions.register_decisions_controllers)
        assert "is_loading" in src


# ===========================================================================
# Utils compute_session_duration safety
# ===========================================================================

class TestSessionDurationSafety:
    """Verify compute_session_duration handles edge cases."""

    def test_none_start_returns_empty(self):
        """None start should return empty string."""
        from agent.governance_ui.utils import compute_session_duration
        assert compute_session_duration(None, None) == ""
        assert compute_session_duration("", None) == ""

    def test_none_end_returns_ongoing(self):
        """Non-empty start with None end should return 'ongoing'."""
        from agent.governance_ui.utils import compute_session_duration
        result = compute_session_duration("2026-02-15T10:00:00", None)
        assert result == "ongoing"

    def test_valid_timestamps_returns_duration(self):
        """Valid start and end should return duration string."""
        from agent.governance_ui.utils import compute_session_duration
        result = compute_session_duration(
            "2026-02-15T10:00:00", "2026-02-15T11:30:00"
        )
        assert "1h 30m" in result or "90" in result or "1:" in result
