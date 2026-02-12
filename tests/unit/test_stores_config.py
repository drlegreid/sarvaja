"""
Unit tests for Governance Stores - TypeDB Configuration.

Per DOC-SIZE-01-v1: Tests for stores/config.py module.
Tests: USE_TYPEDB toggle, get_typedb_client().
"""

import pytest
from unittest.mock import patch, MagicMock


class TestUseTypedbToggle:
    """Tests for USE_TYPEDB environment variable."""

    @patch.dict("os.environ", {"USE_TYPEDB": "true"})
    def test_true(self):
        import importlib
        import governance.stores.config as mod
        importlib.reload(mod)
        assert mod.USE_TYPEDB is True

    @patch.dict("os.environ", {"USE_TYPEDB": "false"})
    def test_false(self):
        import importlib
        import governance.stores.config as mod
        importlib.reload(mod)
        assert mod.USE_TYPEDB is False

    @patch.dict("os.environ", {"USE_TYPEDB": "TRUE"})
    def test_case_insensitive(self):
        import importlib
        import governance.stores.config as mod
        importlib.reload(mod)
        assert mod.USE_TYPEDB is True

    @patch.dict("os.environ", {}, clear=False)
    def test_default_is_true(self):
        import importlib
        import os
        os.environ.pop("USE_TYPEDB", None)
        import governance.stores.config as mod
        importlib.reload(mod)
        # Default is "true" per os.getenv("USE_TYPEDB", "true")
        assert mod.USE_TYPEDB is True


class TestGetTypedbClient:
    """Tests for get_typedb_client()."""

    @patch("governance.stores.config.USE_TYPEDB", False)
    @patch("governance.stores.config.get_client")
    def test_disabled_returns_none(self, mock_get):
        from governance.stores.config import get_typedb_client
        result = get_typedb_client()
        assert result is None
        mock_get.assert_not_called()

    @patch("governance.stores.config.USE_TYPEDB", True)
    @patch("governance.stores.config.get_client")
    def test_connected_returns_client(self, mock_get):
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_get.return_value = mock_client
        from governance.stores.config import get_typedb_client
        result = get_typedb_client()
        assert result is mock_client

    @patch("governance.stores.config.USE_TYPEDB", True)
    @patch("governance.stores.config.get_client")
    def test_not_connected_returns_none(self, mock_get):
        mock_client = MagicMock()
        mock_client.is_connected.return_value = False
        mock_get.return_value = mock_client
        from governance.stores.config import get_typedb_client
        result = get_typedb_client()
        assert result is None

    @patch("governance.stores.config.USE_TYPEDB", True)
    @patch("governance.stores.config.get_client")
    def test_null_client_returns_none(self, mock_get):
        mock_get.return_value = None
        from governance.stores.config import get_typedb_client
        result = get_typedb_client()
        assert result is None

    @patch("governance.stores.config.USE_TYPEDB", True)
    @patch("governance.stores.config.get_client", side_effect=Exception("conn fail"))
    def test_exception_returns_none(self, mock_get):
        from governance.stores.config import get_typedb_client
        result = get_typedb_client()
        assert result is None
