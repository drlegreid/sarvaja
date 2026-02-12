"""
Unit tests for Data Router Main Class.

Per DOC-SIZE-01-v1: Tests for router/router.py module.
Tests: DataRouter init, _execute_typeql, _escape, factory.
"""

from unittest.mock import patch, MagicMock

import pytest

_P_PIPELINE = "governance.router.router.create_embedding_pipeline"


@pytest.fixture()
def router():
    with patch(_P_PIPELINE) as mock_pipe:
        mock_pipe.return_value = MagicMock()
        from governance.router.router import DataRouter
        r = DataRouter(dry_run=True, embed=True)
        yield r


class TestInit:
    def test_defaults(self, router):
        assert router.dry_run is True
        assert router.embed is True
        assert router.typedb_host == "localhost"
        assert router.typedb_port == 1729
        assert router.database == "sim-ai-governance"

    def test_no_embed(self):
        with patch(_P_PIPELINE) as mock_pipe:
            from governance.router.router import DataRouter
            r = DataRouter(dry_run=True, embed=False)
            assert r.embedding_pipeline is None
            mock_pipe.assert_not_called()

    def test_custom_params(self):
        with patch(_P_PIPELINE):
            from governance.router.router import DataRouter
            hook_pre = MagicMock()
            hook_post = MagicMock()
            r = DataRouter(
                dry_run=False, embed=True,
                typedb_host="db.example.com",
                typedb_port=2729,
                database="test-db",
                pre_route_hook=hook_pre,
                post_route_hook=hook_post,
            )
            assert r.typedb_host == "db.example.com"
            assert r.typedb_port == 2729
            assert r.database == "test-db"
            assert r.pre_route_hook is hook_pre
            assert r.post_route_hook is hook_post


class TestExecuteTypeQL:
    def test_dry_run_returns_true(self, router):
        assert router._execute_typeql("insert $x isa rule;") is True

    def test_import_error(self):
        with patch(_P_PIPELINE):
            from governance.router.router import DataRouter
            r = DataRouter(dry_run=False, embed=False)

        with patch.dict("sys.modules", {"typedb": None, "typedb.driver": None}):
            # Force ImportError
            result = r._execute_typeql("insert $x isa rule;")
            assert result is False

    def test_exception_returns_false(self):
        with patch(_P_PIPELINE):
            from governance.router.router import DataRouter
            r = DataRouter(dry_run=False, embed=False)

        with patch("governance.router.router.DataRouter._execute_typeql",
                    return_value=False):
            assert r._execute_typeql("bad query") is False


class TestEscape:
    def test_empty_string(self):
        from governance.router.router import DataRouter
        assert DataRouter._escape("") == ""

    def test_no_special_chars(self):
        from governance.router.router import DataRouter
        assert DataRouter._escape("hello world") == "hello world"

    def test_backslash(self):
        from governance.router.router import DataRouter
        assert DataRouter._escape("path\\to") == "path\\\\to"

    def test_double_quote(self):
        from governance.router.router import DataRouter
        assert DataRouter._escape('say "hi"') == 'say \\"hi\\"'

    def test_newline(self):
        from governance.router.router import DataRouter
        assert DataRouter._escape("line1\nline2") == "line1\\nline2"

    def test_combined(self):
        from governance.router.router import DataRouter
        result = DataRouter._escape('a\\b"c\nd')
        assert result == 'a\\\\b\\"c\\nd'


class TestFactory:
    def test_create_data_router(self):
        with patch(_P_PIPELINE):
            from governance.router.router import create_data_router
            r = create_data_router(dry_run=True, embed=True)
            assert r.dry_run is True

    def test_factory_passes_kwargs(self):
        with patch(_P_PIPELINE):
            from governance.router.router import create_data_router
            r = create_data_router(dry_run=False, embed=False, typedb_port=3000)
            assert r.typedb_port == 3000
