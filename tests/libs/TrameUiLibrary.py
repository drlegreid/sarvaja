"""
RF-004: Robot Framework Library for Trame UI Tests.

Wraps tests/test_trame_ui.py for Robot Framework tests.
Per Phase 6: Use Trame for Python-native web UI.
"""

import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TrameUiLibrary:
    """Robot Framework library for Trame UI tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def trame_ui_importable(self) -> Dict[str, Any]:
        """Check if Trame UI module can be imported."""
        try:
            from agent.trame_ui import SimAITrameUI
            return {"importable": True, "class_exists": SimAITrameUI is not None}
        except ImportError as e:
            return {"importable": False, "error": str(e)}

    def create_trame_app_importable(self) -> Dict[str, Any]:
        """Check if factory function can be imported."""
        try:
            from agent.trame_ui import create_trame_app
            return {
                "importable": True,
                "exists": create_trame_app is not None,
                "callable": callable(create_trame_app)
            }
        except ImportError as e:
            return {"importable": False, "error": str(e)}

    def _mock_trame_modules(self):
        """Get mock modules for Trame."""
        return {
            'trame': MagicMock(),
            'trame.app': MagicMock(),
            'trame.ui.vuetify3': MagicMock(),
            'trame.widgets': MagicMock(),
            'trame.widgets.vuetify3': MagicMock(),
            'trame.widgets.html': MagicMock(),
        }

    def create_app_with_default_agents(self) -> Dict[str, Any]:
        """Test factory creates app with default agents."""
        try:
            from agent.trame_ui import create_trame_app
            app = create_trame_app()
            return {
                "created": app is not None,
                "has_agents": hasattr(app, 'agents'),
                "agent_count": len(app.agents) if hasattr(app, 'agents') else 0
            }
        except ImportError as e:
            return {"skip": True, "reason": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def create_app_with_custom_agents(self) -> Dict[str, Any]:
        """Test factory creates app with custom agents."""
        try:
            from agent.trame_ui import create_trame_app
            custom_agents = {"test_agent": "Test Agent"}
            app = create_trame_app(agents=custom_agents)
            return {
                "created": app is not None,
                "agents_match": app.agents == custom_agents if hasattr(app, 'agents') else False
            }
        except ImportError as e:
            return {"skip": True, "reason": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def create_app_with_custom_api_base(self) -> Dict[str, Any]:
        """Test factory accepts custom API base URL."""
        try:
            from agent.trame_ui import create_trame_app
            custom_url = "http://custom:9999"
            app = create_trame_app(api_base=custom_url)
            return {
                "created": app is not None,
                "api_base_match": app.api_base == custom_url if hasattr(app, 'api_base') else False
            }
        except ImportError as e:
            return {"skip": True, "reason": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def test_ui_class_init_agents(self) -> Dict[str, Any]:
        """Test SimAITrameUI initialization stores agents."""
        mock_server = MagicMock()
        mock_server.state = MagicMock()
        mock_server.controller = MagicMock()

        try:
            with patch('agent.trame_ui.get_server', return_value=mock_server):
                from agent.trame_ui import SimAITrameUI
                agents = {"agent1": MagicMock(), "agent2": MagicMock()}
                ui = SimAITrameUI(agents=agents)
                return {
                    "created": ui is not None,
                    "agents_stored": ui.agents == agents
                }
        except ImportError as e:
            return {"skip": True, "reason": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def test_ui_class_init_api_base(self) -> Dict[str, Any]:
        """Test SimAITrameUI initialization stores API base."""
        mock_server = MagicMock()
        mock_server.state = MagicMock()
        mock_server.controller = MagicMock()

        try:
            with patch('agent.trame_ui.get_server', return_value=mock_server):
                from agent.trame_ui import SimAITrameUI
                custom_url = "http://test:8080"
                ui = SimAITrameUI(agents={}, api_base=custom_url)
                return {
                    "created": ui is not None,
                    "api_base_stored": ui.api_base == custom_url
                }
        except ImportError as e:
            return {"skip": True, "reason": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def verify_trame_imports(self) -> Dict[str, bool]:
        """Verify all Trame imports work."""
        results = {}
        results["ui_class"] = self.trame_ui_importable().get("importable", False)
        results["factory"] = self.create_trame_app_importable().get("importable", False)
        return results
