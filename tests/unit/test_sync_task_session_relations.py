"""
Unit tests for Sync Task-Session Relations script.

Per DOC-SIZE-01-v1: Tests for governance/sync_task_session_relations.py module.
Tests: sync_task_session_relations — success, errors, skips, already linked.
"""

from unittest.mock import patch, MagicMock

from governance.sync_task_session_relations import sync_task_session_relations


def _mock_response(status_code=200, json_data=None, text=""):
    """Create a mock response object."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


# ── sync_task_session_relations ────────────────────────────


class TestSyncTaskSessionRelations:
    @patch("governance.sync_task_session_relations.requests")
    def test_successful_sync(self, mock_requests):
        tasks_resp = _mock_response(200, {
            "items": [
                {"task_id": "T-1", "linked_sessions": ["S-1", "S-2"]},
            ]
        })
        link_resp = _mock_response(200)
        verify_resp = _mock_response(200, {"tasks_completed": 2})

        mock_requests.get.side_effect = [tasks_resp, verify_resp]
        mock_requests.post.return_value = link_resp

        result = sync_task_session_relations()
        assert result == 0
        assert mock_requests.post.call_count == 2

    @patch("governance.sync_task_session_relations.requests")
    def test_tasks_api_failure(self, mock_requests):
        mock_requests.get.return_value = _mock_response(500)
        result = sync_task_session_relations()
        assert result == 1

    @patch("governance.sync_task_session_relations.requests")
    def test_skips_empty_sessions(self, mock_requests):
        tasks_resp = _mock_response(200, {
            "items": [
                {"task_id": "T-1", "linked_sessions": []},
                {"task_id": "T-2", "linked_sessions": None},
            ]
        })
        verify_resp = _mock_response(200, {"tasks_completed": 0})

        mock_requests.get.side_effect = [tasks_resp, verify_resp]

        result = sync_task_session_relations()
        assert result == 0
        mock_requests.post.assert_not_called()

    @patch("governance.sync_task_session_relations.requests")
    def test_already_linked_409(self, mock_requests):
        tasks_resp = _mock_response(200, {
            "items": [
                {"task_id": "T-1", "linked_sessions": ["S-1"]},
            ]
        })
        link_resp = _mock_response(409)
        verify_resp = _mock_response(200, {"tasks_completed": 1})

        mock_requests.get.side_effect = [tasks_resp, verify_resp]
        mock_requests.post.return_value = link_resp

        result = sync_task_session_relations()
        assert result == 0

    @patch("governance.sync_task_session_relations.requests")
    def test_session_not_found_404(self, mock_requests):
        tasks_resp = _mock_response(200, {
            "items": [
                {"task_id": "T-1", "linked_sessions": ["S-MISSING"]},
            ]
        })
        link_resp = _mock_response(404)
        verify_resp = _mock_response(200, {"tasks_completed": 0})

        mock_requests.get.side_effect = [tasks_resp, verify_resp]
        mock_requests.post.return_value = link_resp

        result = sync_task_session_relations()
        assert result == 0

    @patch("governance.sync_task_session_relations.requests")
    def test_link_error(self, mock_requests):
        tasks_resp = _mock_response(200, {
            "items": [
                {"task_id": "T-1", "linked_sessions": ["S-1"]},
            ]
        })
        link_resp = _mock_response(500)
        verify_resp = _mock_response(200, {"tasks_completed": 0})

        mock_requests.get.side_effect = [tasks_resp, verify_resp]
        mock_requests.post.return_value = link_resp

        result = sync_task_session_relations()
        assert result == 1

    @patch("governance.sync_task_session_relations.requests")
    def test_exception_during_link(self, mock_requests):
        tasks_resp = _mock_response(200, {
            "items": [
                {"task_id": "T-1", "linked_sessions": ["S-1"]},
            ]
        })
        verify_resp = _mock_response(200, {"tasks_completed": 0})

        mock_requests.get.side_effect = [tasks_resp, verify_resp]
        mock_requests.post.side_effect = Exception("network error")

        result = sync_task_session_relations()
        assert result == 1

    @patch("governance.sync_task_session_relations.requests")
    def test_mixed_results(self, mock_requests):
        tasks_resp = _mock_response(200, {
            "items": [
                {"task_id": "T-1", "linked_sessions": ["S-1", "S-2"]},
                {"task_id": "T-2", "linked_sessions": []},
                {"task_id": "T-3", "linked_sessions": ["S-3"]},
            ]
        })
        verify_resp = _mock_response(200, {"tasks_completed": 2})

        mock_requests.get.side_effect = [tasks_resp, verify_resp]
        mock_requests.post.side_effect = [
            _mock_response(200),   # T-1 -> S-1 success
            _mock_response(409),   # T-1 -> S-2 already linked
            _mock_response(201),   # T-3 -> S-3 success
        ]

        result = sync_task_session_relations()
        assert result == 0

    @patch("governance.sync_task_session_relations.requests")
    def test_uses_api_base_env(self, mock_requests):
        tasks_resp = _mock_response(200, {"items": []})
        verify_resp = _mock_response(200, {})

        mock_requests.get.side_effect = [tasks_resp, verify_resp]

        sync_task_session_relations()

        # Should call with default API_BASE
        call_url = mock_requests.get.call_args_list[0][0][0]
        assert "/api/tasks" in call_url
