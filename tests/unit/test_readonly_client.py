"""
Unit tests for ChromaDB Read-Only Client.

Per DOC-SIZE-01-v1: Tests for readonly/client.py module.
Tests: ChromaReadOnly type detection, query, get, add redirect,
       delete deprecation, skip_connection mode, factory.
"""

import warnings
from unittest.mock import patch, MagicMock

import pytest

from governance.readonly.client import ChromaReadOnly, create_readonly_client


_P_ROUTER = "governance.readonly.client.create_data_router"


@pytest.fixture()
def client():
    with patch(_P_ROUTER) as mock_router:
        mock_router.return_value = MagicMock()
        c = ChromaReadOnly(skip_connection=True)
        yield c


class TestDetectType:
    def test_rule_pattern(self, client):
        assert client._detect_type("RULE-001") == "rule"

    def test_rule_pattern_three_digits(self, client):
        assert client._detect_type("RULE-042") == "rule"

    def test_decision_pattern(self, client):
        assert client._detect_type("DECISION-003") == "decision"

    def test_session_pattern(self, client):
        assert client._detect_type("SESSION-2026-02-11-TOPIC") == "session"

    def test_session_minimal(self, client):
        assert client._detect_type("SESSION-2026-02-11") == "session"

    def test_unknown(self, client):
        assert client._detect_type("DOC-XYZ") == "document"

    def test_rule_pattern_no_match_extra(self, client):
        # RULE-0001 has 4 digits — no match
        assert client._detect_type("RULE-0001") == "document"


class TestSkipConnection:
    def test_query_returns_empty(self, client):
        result = client.query("coll", "test")
        assert result["ids"] == []
        assert result["documents"] == []

    def test_get_returns_ids(self, client):
        result = client.get("coll", ["id1", "id2"])
        assert result["ids"] == ["id1", "id2"]
        assert result["documents"] == []

    def test_list_collections_empty(self, client):
        assert client.list_collections() == []

    def test_get_client_returns_none(self, client):
        assert client._get_client() is None


class TestGetCollection:
    def test_returns_wrapper(self, client):
        coll = client.get_collection("test_coll")
        assert coll.name == "test_coll"
        assert coll._parent is client


class TestAdd:
    def test_add_redirects_rule(self, client):
        client._router.route_rule.return_value = {"success": True}

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = client.add(
                "coll",
                documents=["rule content"],
                ids=["RULE-001"],
                metadatas=[{"name": "Test Rule"}],
            )

        assert result["deprecated"] is True
        assert result["redirected"] is True
        assert result["operation"] == "add"
        client._router.route_rule.assert_called_once()

    def test_add_redirects_decision(self, client):
        client._router.route_decision.return_value = {"success": True}

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = client.add(
                "coll",
                documents=["decision content"],
                ids=["DECISION-001"],
                metadatas=[{"name": "Test Decision"}],
            )

        assert result["redirected"] is True
        client._router.route_decision.assert_called_once()

    def test_add_redirects_session(self, client):
        client._router.route_session.return_value = {"success": True}

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = client.add(
                "coll",
                documents=["session content"],
                ids=["SESSION-2026-02-11-TEST"],
            )

        assert result["redirected"] is True
        client._router.route_session.assert_called_once()

    def test_add_generic_skipped(self, client):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = client.add(
                "coll",
                documents=["generic doc"],
                ids=["DOC-XYZ"],
            )

        assert result["redirected"] is True
        results = result["typedb_result"]["results"]
        assert results[0]["skipped"] is True

    def test_add_handles_error(self, client):
        client._router.route_rule.side_effect = RuntimeError("boom")

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = client.add(
                "coll",
                documents=["content"],
                ids=["RULE-001"],
            )

        results = result["typedb_result"]["results"]
        assert results[0]["success"] is False
        assert "boom" in results[0]["error"]


class TestUpdate:
    def test_update_delegates_to_add(self, client):
        client._router.route_rule.return_value = {"success": True}

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = client.update(
                "coll",
                documents=["updated"],
                ids=["RULE-001"],
            )

        assert result["deprecated"] is True
        assert result["operation"] == "add"  # delegates to add


class TestDelete:
    def test_delete_not_redirected(self, client):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = client.delete("coll", ids=["RULE-001"])

        assert result["deprecated"] is True
        assert result["redirected"] is False
        assert "not executed" in result["message"]


class TestDeprecationStatus:
    def test_returns_status(self, client):
        status = client.get_deprecation_status()
        assert status["writes_deprecated"] is True
        assert status["reads_allowed"] is True
        assert status["redirect_target"] == "typedb"


class TestDeprecationWarning:
    def test_log_deprecation_emits_warning(self, client):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client._log_deprecation("test_op", "test message")
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "test_op" in str(w[0].message)

    def test_no_warning_when_disabled(self):
        with patch(_P_ROUTER):
            c = ChromaReadOnly(skip_connection=True, log_deprecations=False)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            c._log_deprecation("test_op", "test message")
            assert len(w) == 0


class TestFactory:
    def test_create_readonly_client(self):
        with patch(_P_ROUTER):
            c = create_readonly_client(skip_connection=True)
        assert isinstance(c, ChromaReadOnly)
        assert c.skip_connection is True

    def test_create_with_log_disabled(self):
        with patch(_P_ROUTER):
            c = create_readonly_client(skip_connection=True, log_deprecations=False)
        assert c.log_deprecations is False
