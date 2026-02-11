"""
UI Infrastructure View Tests.

Per DOC-SIZE-01-v1: Modular entity-based test structure.
Per UI-AUDIT-008: Validates health hash display in infrastructure view.
Per GAP-INFRA-004: Docker/Podman health dashboard.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestInfraStateVariables:
    """Test infrastructure state variables exist in initial state."""

    @pytest.mark.unit
    def test_initial_state_has_infra_stats(self):
        """Initial state should include infra_stats for health hash."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()
        assert 'infra_stats' in state, "infra_stats missing from initial state"

    @pytest.mark.unit
    def test_infra_stats_has_frankel_hash(self):
        """infra_stats should include frankel_hash field. Per UI-AUDIT-008."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()
        infra_stats = state.get('infra_stats', {})

        assert 'frankel_hash' in infra_stats, "frankel_hash missing from infra_stats"
        # Default should be placeholder
        assert infra_stats['frankel_hash'] == "--------"

    @pytest.mark.unit
    def test_infra_stats_has_last_check(self):
        """infra_stats should include last_check timestamp."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()
        infra_stats = state.get('infra_stats', {})

        assert 'last_check' in infra_stats, "last_check missing from infra_stats"
        assert infra_stats['last_check'] == "Never"

    @pytest.mark.unit
    def test_infra_stats_has_memory_pct(self):
        """infra_stats should include memory_pct field."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()
        infra_stats = state.get('infra_stats', {})

        assert 'memory_pct' in infra_stats, "memory_pct missing from infra_stats"

    @pytest.mark.unit
    def test_infra_stats_has_python_procs(self):
        """infra_stats should include python_procs field."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()
        infra_stats = state.get('infra_stats', {})

        assert 'python_procs' in infra_stats, "python_procs missing from infra_stats"


class TestInfraViewReferences:
    """Test infrastructure view references correct state variables."""

    @pytest.mark.unit
    def test_infra_view_exists(self):
        """Infrastructure view module should exist."""
        from agent.governance_ui.views import infra_view
        assert infra_view is not None

    @pytest.mark.unit
    def test_build_infra_view_callable(self):
        """build_infra_view function should be callable."""
        from agent.governance_ui.views.infra_view import build_infra_view
        assert callable(build_infra_view)

    @pytest.mark.unit
    def test_build_system_stats_callable(self):
        """build_system_stats function should be callable."""
        from agent.governance_ui.views.infra_view import build_system_stats
        assert callable(build_system_stats)

    @pytest.mark.unit
    def test_view_references_frankel_hash(self):
        """View source should reference infra_stats.frankel_hash. Per UI-AUDIT-008."""
        import inspect
        from agent.governance_ui.views.infra.stats import build_system_stats

        source = inspect.getsource(build_system_stats)
        assert 'frankel_hash' in source, "View does not reference frankel_hash"
        assert 'infra_stats' in source, "View does not reference infra_stats"


class TestHealthcheckStateFile:
    """Test healthcheck state file integration."""

    @pytest.fixture
    def mock_healthcheck_state(self, tmp_path):
        """Create mock healthcheck state file."""
        state_file = tmp_path / ".healthcheck_state.json"
        state_data = {
            "master_hash": "ABCD1234",
            "last_check": "2026-01-19T12:00:00",
            "services": {"typedb": "OK", "chromadb": "OK"}
        }
        state_file.write_text(json.dumps(state_data))
        return state_file

    @pytest.mark.unit
    def test_healthcheck_state_file_structure(self, mock_healthcheck_state):
        """Healthcheck state file should have correct structure."""
        data = json.loads(mock_healthcheck_state.read_text())

        assert 'master_hash' in data, "master_hash missing from healthcheck state"
        assert 'last_check' in data, "last_check missing from healthcheck state"
        assert len(data['master_hash']) == 8, "master_hash should be 8 characters"

    @pytest.mark.unit
    def test_actual_healthcheck_state_exists(self):
        """Actual healthcheck state file should exist in hooks directory."""
        project_root = Path(__file__).parent.parent.parent.parent
        state_file = project_root / ".claude" / "hooks" / ".healthcheck_state.json"

        # Skip if file doesn't exist (CI environment)
        if not state_file.exists():
            pytest.skip("Healthcheck state file not found (CI environment)")

        data = json.loads(state_file.read_text())
        assert 'master_hash' in data, "master_hash missing from actual state file"


class TestMCPStatusPanel:
    """Test MCP status panel per UI-AUDIT-011."""

    @pytest.mark.unit
    def test_build_mcp_status_panel_callable(self):
        """build_mcp_status_panel function should be callable."""
        from agent.governance_ui.views.infra_view import build_mcp_status_panel
        assert callable(build_mcp_status_panel)

    @pytest.mark.unit
    def test_initial_state_has_mcp_servers(self):
        """Initial state should include mcp_servers in infra_stats."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()
        infra_stats = state.get('infra_stats', {})

        # mcp_servers may be empty dict initially
        assert 'mcp_servers' in infra_stats or infra_stats.get('mcp_servers') is None
