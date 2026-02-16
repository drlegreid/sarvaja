"""
Tests for dark theme support across all UI components.

Per PLAN-UI-OVERHAUL-001 Task 0.1: Dark Theme Fix
TDD: Tests written before implementation.
"""

import pytest


class TestDarkThemeSupport:
    """Verify dark theme is properly wired across all views."""

    def test_initial_state_has_dark_mode(self):
        """dark_mode state variable exists and defaults to True."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert 'dark_mode' in state
        assert state['dark_mode'] is True

    def test_mermaid_uses_dynamic_theme(self):
        """Mermaid component should use dark_mode-aware theme, not hardcoded 'default'."""
        from agent.governance_ui.components import mermaid
        import inspect
        source = inspect.getsource(mermaid.inject_mermaid_script)
        # Should NOT have hardcoded theme: 'default'
        assert "theme: 'default'" not in source, (
            "Mermaid theme is hardcoded to 'default'. "
            "Should use dynamic theme based on dark_mode state."
        )

    def test_mermaid_container_no_hardcoded_light_bg(self):
        """Mermaid container should not hardcode light background."""
        from agent.governance_ui.components import mermaid
        import inspect
        source = inspect.getsource(mermaid.build_mermaid_diagram)
        assert '#f8f9fa' not in source, (
            "Mermaid container has hardcoded light background #f8f9fa"
        )

    def test_no_hardcoded_light_backgrounds_in_views(self):
        """No view files should have hardcoded light-only background colors."""
        from pathlib import Path
        import re

        views_dir = Path(__file__).parent.parent.parent / "agent" / "governance_ui" / "views"
        # Light-only background colors that break dark theme
        light_bg_pattern = re.compile(
            r'background:\s*#(?:f[0-9a-f]{5}|e[0-9a-f]{5}|d[0-9a-f]{5}|fff)',
            re.IGNORECASE
        )

        violations = []
        for py_file in views_dir.rglob("*.py"):
            content = py_file.read_text()
            matches = light_bg_pattern.findall(content)
            if matches:
                violations.append(f"{py_file.name}: {matches}")

        assert not violations, (
            f"Hardcoded light backgrounds found in views (breaks dark theme):\n"
            + "\n".join(violations)
        )

    def test_mermaid_summary_no_hardcoded_color(self):
        """Mermaid summary link should not use hardcoded text color."""
        from agent.governance_ui.components import mermaid
        import inspect
        source = inspect.getsource(mermaid.build_mermaid_with_fallback)
        assert 'color: #666' not in source, (
            "Mermaid summary has hardcoded color #666 - invisible in dark theme"
        )
