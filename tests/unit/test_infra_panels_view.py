"""
Tests for infrastructure operational panels.

Per GAP-INFRA-004: DSP alerts, process viewer, logs, recovery actions.
Batch 162: New coverage for views/infra/panels.py (0→12 tests).
"""
import inspect

import pytest


class TestInfraPanelComponents:
    def test_build_dsp_alert_callable(self):
        from agent.governance_ui.views.infra.panels import build_dsp_alert
        assert callable(build_dsp_alert)

    def test_build_python_procs_callable(self):
        from agent.governance_ui.views.infra.panels import build_python_procs_panel
        assert callable(build_python_procs_panel)

    def test_build_logs_callable(self):
        from agent.governance_ui.views.infra.panels import build_logs_panel
        assert callable(build_logs_panel)

    def test_build_recovery_callable(self):
        from agent.governance_ui.views.infra.panels import build_recovery_panel
        assert callable(build_recovery_panel)


class TestInfraPanelContent:
    def test_has_dsp_alert_testid(self):
        from agent.governance_ui.views.infra import panels
        source = inspect.getsource(panels)
        assert "infra-dsp-alert" in source

    def test_has_python_procs_testid(self):
        from agent.governance_ui.views.infra import panels
        source = inspect.getsource(panels)
        assert "infra-python-procs-panel" in source

    def test_has_logs_panel_testid(self):
        from agent.governance_ui.views.infra import panels
        source = inspect.getsource(panels)
        assert "infra-logs-panel" in source

    def test_has_recovery_testid(self):
        from agent.governance_ui.views.infra import panels
        source = inspect.getsource(panels)
        assert "infra-recovery" in source

    def test_has_start_all_button(self):
        from agent.governance_ui.views.infra import panels
        source = inspect.getsource(panels)
        assert "infra-start-all" in source

    def test_has_restart_button(self):
        from agent.governance_ui.views.infra import panels
        source = inspect.getsource(panels)
        assert "infra-restart" in source

    def test_has_cleanup_button(self):
        from agent.governance_ui.views.infra import panels
        source = inspect.getsource(panels)
        assert "infra-cleanup" in source

    def test_has_logs_refresh_button(self):
        from agent.governance_ui.views.infra import panels
        source = inspect.getsource(panels)
        assert "logs-refresh-btn" in source
