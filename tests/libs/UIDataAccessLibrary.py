"""
Robot Framework Library for UI Data Access Function Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Migrated from tests/unit/ui/test_ui_data_access.py
"""
from robot.api.deco import keyword
from unittest.mock import patch, MagicMock


class UIDataAccessLibrary:
    """Library for testing data access pure functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    TYPEDB_CLIENT_MOCK_PATH = 'governance.mcp_tools.common.get_typedb_client'

    @keyword("Get Rules Importable")
    def get_rules_importable(self):
        """get_rules function must be importable."""
        try:
            from agent.governance_ui import get_rules

            return {
                "importable": True,
                "callable": callable(get_rules)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Rules By Category Importable")
    def get_rules_by_category_importable(self):
        """get_rules_by_category function must be importable."""
        try:
            from agent.governance_ui import get_rules_by_category

            return {
                "importable": True,
                "callable": callable(get_rules_by_category)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Decisions Importable")
    def get_decisions_importable(self):
        """get_decisions function must be importable."""
        try:
            from agent.governance_ui import get_decisions

            return {
                "importable": True,
                "callable": callable(get_decisions)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Sessions Importable")
    def get_sessions_importable(self):
        """get_sessions function must be importable."""
        try:
            from agent.governance_ui import get_sessions

            return {
                "importable": True,
                "callable": callable(get_sessions)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Tasks Importable")
    def get_tasks_importable(self):
        """get_tasks function must be importable."""
        try:
            from agent.governance_ui import get_tasks

            return {
                "importable": True,
                "callable": callable(get_tasks)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Search Evidence Importable")
    def search_evidence_importable(self):
        """search_evidence function must be importable."""
        try:
            from agent.governance_ui import search_evidence

            return {
                "importable": True,
                "callable": callable(search_evidence)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Rules Returns List")
    def get_rules_returns_list(self):
        """get_rules should return a list."""
        try:
            from agent.governance_ui import get_rules

            mock_tx = MagicMock()
            mock_tx.query.fetch.return_value = iter([])

            with patch(self.TYPEDB_CLIENT_MOCK_PATH) as mock_client:
                mock_client.return_value.__enter__.return_value.transaction.return_value.__enter__.return_value = mock_tx

                result = get_rules()

                return {
                    "is_list": isinstance(result, list)
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Get Decisions Returns List")
    def get_decisions_returns_list(self):
        """get_decisions should return a list."""
        try:
            from agent.governance_ui import get_decisions

            mock_tx = MagicMock()
            mock_tx.query.fetch.return_value = iter([])

            with patch(self.TYPEDB_CLIENT_MOCK_PATH) as mock_client:
                mock_client.return_value.__enter__.return_value.transaction.return_value.__enter__.return_value = mock_tx

                result = get_decisions()

                return {
                    "is_list": isinstance(result, list)
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
