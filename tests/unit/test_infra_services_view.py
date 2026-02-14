"""
Tests for infrastructure services grid view.

Per GAP-INFRA-004: Service status cards.
Batch 164: New coverage for views/infra/services.py (0->10 tests).
"""
import inspect

import pytest


class TestInfraServicesComponents:
    def test_build_infra_header_callable(self):
        from agent.governance_ui.views.infra.services import build_infra_header
        assert callable(build_infra_header)

    def test_build_service_card_callable(self):
        from agent.governance_ui.views.infra.services import build_service_card
        assert callable(build_service_card)

    def test_build_services_grid_callable(self):
        from agent.governance_ui.views.infra.services import build_services_grid
        assert callable(build_services_grid)


class TestInfraHeaderContent:
    def test_has_refresh_btn(self):
        from agent.governance_ui.views.infra import services
        source = inspect.getsource(services)
        assert "infra-refresh-btn" in source

    def test_has_server_icon(self):
        from agent.governance_ui.views.infra import services
        source = inspect.getsource(services)
        assert "mdi-server" in source


class TestServiceCardContent:
    def test_has_podman_card(self):
        from agent.governance_ui.views.infra import services
        source = inspect.getsource(services)
        # f-string generates testid at runtime; check the service_id literal
        assert '"podman"' in source

    def test_has_typedb_card(self):
        from agent.governance_ui.views.infra import services
        source = inspect.getsource(services)
        assert "typedb" in source

    def test_has_chromadb_card(self):
        from agent.governance_ui.views.infra import services
        source = inspect.getsource(services)
        assert "chromadb" in source

    def test_has_start_button_pattern(self):
        from agent.governance_ui.views.infra import services
        source = inspect.getsource(services)
        assert "infra-start-" in source

    def test_has_port_display(self):
        from agent.governance_ui.views.infra import services
        source = inspect.getsource(services)
        assert "1729" in source
        assert "8001" in source
        assert "4000" in source
