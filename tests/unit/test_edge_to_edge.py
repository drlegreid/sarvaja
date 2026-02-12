"""
Unit tests for Edge-to-Edge Validation.

Per DOC-SIZE-01-v1: Tests for governance/integrity/edge_to_edge.py.
Tests: validate_edge_to_edge — API validation, error handling.
"""

from unittest.mock import patch, MagicMock

from governance.integrity.edge_to_edge import validate_edge_to_edge


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or []
    return resp


class TestValidateEdgeToEdge:
    @patch("httpx.Client")
    def test_validates_all_entities(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, [])
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = validate_edge_to_edge()
        assert "integrity_report" in result
        assert mc.get.call_count == 5

    @patch("httpx.Client")
    def test_handles_api_error(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("connection refused"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = validate_edge_to_edge()
        assert "api_error" in result
        assert "connection refused" in result["api_error"]

    @patch("httpx.Client")
    def test_skips_non_200_responses(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(500)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = validate_edge_to_edge()
        assert "rules" not in result
        assert "integrity_report" in result

    @patch("httpx.Client")
    def test_custom_api_url(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, [])
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        validate_edge_to_edge(api_url="http://custom:9090")
        first_call = mc.get.call_args_list[0]
        assert "http://custom:9090" in first_call[0][0]

    @patch("httpx.Client")
    def test_with_rule_data(self, MockClient):
        mc = MagicMock()
        rules_data = [{"rule_id": "R-1", "title": "Test Rule", "status": "ACTIVE"}]
        mc.get.return_value = _mock_response(200, rules_data)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = validate_edge_to_edge()
        assert "rules" in result
