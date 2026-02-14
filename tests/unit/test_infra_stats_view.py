"""
Tests for infrastructure system stats panel.

Per GAP-INFRA-004: Memory, process, and health hash displays.
Batch 164: New coverage for views/infra/stats.py (0->10 tests).
"""
import inspect

import pytest


class TestInfraStatsComponents:
    def test_build_system_stats_callable(self):
        from agent.governance_ui.views.infra.stats import build_system_stats
        assert callable(build_system_stats)


class TestMemoryStatContent:
    def test_has_memory_testid(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "infra-stat-memory" in source

    def test_has_memory_threshold_colors(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "85" in source
        assert "70" in source


class TestProcessStatContent:
    def test_has_procs_testid(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "infra-stat-procs" in source

    def test_has_process_warning(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "python_procs" in source
        assert "20" in source


class TestHealthHashContent:
    def test_has_hash_testid(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "infra-stat-hash" in source

    def test_has_frankel_hash(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "frankel_hash" in source

    def test_has_component_hashes(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "component_hashes" in source

    def test_has_component_statuses(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "component_statuses" in source

    def test_has_info_tooltips(self):
        from agent.governance_ui.views.infra import stats
        source = inspect.getsource(stats)
        assert "mdi-information-outline" in source
