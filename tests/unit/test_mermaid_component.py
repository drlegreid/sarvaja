"""
Tests for Mermaid diagram rendering component.

Batch 168: New coverage for agent/governance_ui/components/mermaid.py (0->10 tests).
"""
import inspect

import pytest


class TestMermaidComponents:
    def test_inject_mermaid_script_callable(self):
        from agent.governance_ui.components.mermaid import inject_mermaid_script
        assert callable(inject_mermaid_script)

    def test_build_mermaid_diagram_callable(self):
        from agent.governance_ui.components.mermaid import build_mermaid_diagram
        assert callable(build_mermaid_diagram)

    def test_build_mermaid_with_fallback_callable(self):
        from agent.governance_ui.components.mermaid import build_mermaid_with_fallback
        assert callable(build_mermaid_with_fallback)


class TestMermaidContent:
    def test_has_cdn_url(self):
        from agent.governance_ui.components.mermaid import MERMAID_CDN
        assert "cdn.jsdelivr.net" in MERMAID_CDN
        assert "mermaid" in MERMAID_CDN

    def test_has_mermaid_source_class(self):
        from agent.governance_ui.components import mermaid
        source = inspect.getsource(mermaid)
        assert "mermaid-source" in source

    def test_has_mermaid_container_class(self):
        from agent.governance_ui.components import mermaid
        source = inspect.getsource(mermaid)
        assert "mermaid-container" in source

    def test_has_render_function(self):
        from agent.governance_ui.components import mermaid
        source = inspect.getsource(mermaid)
        assert "renderMermaidDiagrams" in source

    def test_has_dark_theme_support(self):
        from agent.governance_ui.components import mermaid
        source = inspect.getsource(mermaid)
        assert "dark" in source

    def test_has_view_source_fallback(self):
        from agent.governance_ui.components import mermaid
        source = inspect.getsource(mermaid)
        assert "View Source" in source

    def test_has_data_testid(self):
        from agent.governance_ui.components import mermaid
        source = inspect.getsource(mermaid)
        assert "data-testid" in source
