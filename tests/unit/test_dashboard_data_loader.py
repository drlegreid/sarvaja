"""
Unit tests for Dashboard Initial Data Loader.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/dashboard_data_loader.py.
Tests: load_initial_data, _load_rules, _load_decisions, _load_sessions,
       _load_agents, _load_tasks, _load_projects, source_type derivation.
"""

from unittest.mock import MagicMock, patch, call

from agent.governance_ui.dashboard_data_loader import load_initial_data


def _mock_response(status_code=200, json_data=None):
    """Create a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


def _make_client(responses):
    """Create a mock httpx.Client with sequential GET responses."""
    mock_client = MagicMock()
    mock_client.get.side_effect = responses
    return mock_client


# ── load_initial_data ────────────────────────────────────


class TestLoadInitialData:
    @patch("httpx.Client")
    def test_loads_all_data(self, MockClient):
        state = MagicMock()
        rules_resp = _mock_response(200, {"items": [{"rule_id": "R-1"}]})
        decisions_resp = _mock_response(200, {"items": [{"decision_id": "D-1"}]})
        sessions_resp = _mock_response(200, {
            "items": [{"session_id": "S-1", "start_time": "", "end_time": "", "agent_id": "a1"}],
            "pagination": {"total": 1},
        })
        agents_resp = _mock_response(200, {"items": [{"agent_id": "A-1"}]})
        tasks_resp = _mock_response(200, {
            "items": [{"task_id": "T-1"}],
            "pagination": {"total": 1},
        })
        projects_resp = _mock_response(200, {"items": [{"project_id": "P-1"}]})

        mock_client = MagicMock()
        mock_client.get.side_effect = [rules_resp, decisions_resp, sessions_resp, agents_resp, tasks_resp, projects_resp]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          get_rules=MagicMock(), get_decisions=MagicMock(),
                          get_sessions=MagicMock(), get_tasks=MagicMock())

        assert state.rules == [{"rule_id": "R-1"}]
        assert state.decisions == [{"decision_id": "D-1"}]
        assert state.agents == [{"agent_id": "A-1"}]
        assert state.projects == [{"project_id": "P-1"}]

    @patch("httpx.Client")
    def test_fallback_on_exception(self, MockClient):
        state = MagicMock()
        MockClient.side_effect = Exception("connection refused")

        get_rules = MagicMock(return_value=[{"rule_id": "R-MCP"}])
        get_decisions = MagicMock(return_value=[])
        get_sessions = MagicMock(return_value=[])
        get_tasks = MagicMock(return_value=[])

        load_initial_data(state, "http://localhost:8082",
                          get_rules, get_decisions, get_sessions, get_tasks)

        assert state.rules == [{"rule_id": "R-MCP"}]
        get_rules.assert_called_once()


class TestLoadRules:
    @patch("httpx.Client")
    def test_api_success(self, MockClient):
        state = MagicMock()
        get_rules = MagicMock()
        rules_resp = _mock_response(200, {"items": [{"rule_id": "R-1"}]})
        # Need responses for all 6 endpoints
        decisions_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, [])
        agents_resp = _mock_response(200, [])
        tasks_resp = _mock_response(200, [])
        projects_resp = _mock_response(200, [])

        mock_client = MagicMock()
        mock_client.get.side_effect = [rules_resp, decisions_resp, sessions_resp, agents_resp, tasks_resp, projects_resp]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          get_rules, MagicMock(), MagicMock(), MagicMock())

        assert state.rules == [{"rule_id": "R-1"}]
        get_rules.assert_not_called()

    @patch("httpx.Client")
    def test_api_failure_fallback(self, MockClient):
        state = MagicMock()
        get_rules = MagicMock(return_value=[{"rule_id": "R-FALLBACK"}])
        rules_resp = _mock_response(500)
        decisions_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, [])
        agents_resp = _mock_response(200, [])
        tasks_resp = _mock_response(200, [])
        projects_resp = _mock_response(200, [])

        mock_client = MagicMock()
        mock_client.get.side_effect = [rules_resp, decisions_resp, sessions_resp, agents_resp, tasks_resp, projects_resp]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          get_rules, MagicMock(), MagicMock(), MagicMock())

        assert state.rules == [{"rule_id": "R-FALLBACK"}]


class TestLoadSessions:
    @patch("httpx.Client")
    def test_computes_metrics(self, MockClient):
        state = MagicMock()
        rules_resp = _mock_response(200, [])
        decisions_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, {
            "items": [
                {"session_id": "S-1", "start_time": "2026-01-01T10:00:00",
                 "end_time": "2026-01-01T11:00:00", "agent_id": "code-agent"},
            ],
            "pagination": {"total": 1},
        })
        agents_resp = _mock_response(200, [])
        tasks_resp = _mock_response(200, [])
        projects_resp = _mock_response(200, [])

        mock_client = MagicMock()
        mock_client.get.side_effect = [rules_resp, decisions_resp, sessions_resp, agents_resp, tasks_resp, projects_resp]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        # Sessions metrics should be computed
        assert hasattr(state, "sessions_metrics_duration")
        assert state.sessions_agent_options == ["code-agent"]


class TestLoadTasks:
    @patch("httpx.Client")
    def test_paginated_tasks(self, MockClient):
        state = MagicMock()
        rules_resp = _mock_response(200, [])
        decisions_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, [])
        agents_resp = _mock_response(200, [])
        tasks_resp = _mock_response(200, {
            "items": [{"task_id": "T-1"}, {"task_id": "T-2"}],
            "pagination": {"total": 2, "offset": 0, "limit": 20},
        })
        projects_resp = _mock_response(200, [])

        mock_client = MagicMock()
        mock_client.get.side_effect = [rules_resp, decisions_resp, sessions_resp, agents_resp, tasks_resp, projects_resp]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert state.tasks == [{"task_id": "T-1"}, {"task_id": "T-2"}]
        assert state.tasks_pagination == {"total": 2, "offset": 0, "limit": 20}

    @patch("httpx.Client")
    def test_list_response_auto_paginates(self, MockClient):
        state = MagicMock()
        rules_resp = _mock_response(200, [])
        decisions_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, [])
        agents_resp = _mock_response(200, [])
        # Return raw list (no "items" key)
        tasks_resp = _mock_response(200, [{"task_id": f"T-{i}"} for i in range(5)])
        projects_resp = _mock_response(200, [])

        mock_client = MagicMock()
        mock_client.get.side_effect = [rules_resp, decisions_resp, sessions_resp, agents_resp, tasks_resp, projects_resp]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert len(state.tasks) == 5
        assert state.tasks_pagination["total"] == 5


# ── Projects ──────────────────────────────────────────────


class TestLoadProjects:
    @patch("httpx.Client")
    def test_loads_projects(self, MockClient):
        """Projects loaded from /api/projects."""
        state = MagicMock()
        empty_resp = _mock_response(200, [])
        projects_resp = _mock_response(200, {
            "items": [{"project_id": "PROJ-1", "name": "Sarvaja"}],
        })

        mock_client = MagicMock()
        mock_client.get.side_effect = [
            empty_resp, empty_resp, empty_resp, empty_resp, empty_resp,
            projects_resp,
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert state.projects == [{"project_id": "PROJ-1", "name": "Sarvaja"}]

    @patch("httpx.Client")
    def test_projects_api_failure(self, MockClient):
        """Projects defaults to empty on API failure."""
        state = MagicMock()
        empty_resp = _mock_response(200, [])
        projects_resp = _mock_response(500)

        mock_client = MagicMock()
        mock_client.get.side_effect = [
            empty_resp, empty_resp, empty_resp, empty_resp, empty_resp,
            projects_resp,
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert state.projects == []


# ── Source Type Derivation ────────────────────────────────


class TestSourceTypeDerivation:
    @patch("httpx.Client")
    def test_cc_session_gets_cc_source(self, MockClient):
        """Sessions with cc_session_uuid get source_type='CC'."""
        state = MagicMock()
        empty_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, {
            "items": [
                {"session_id": "S-1", "start_time": "", "end_time": "",
                 "agent_id": "a1", "cc_session_uuid": "abc-123"},
            ],
            "pagination": {"total": 1},
        })

        mock_client = MagicMock()
        mock_client.get.side_effect = [
            empty_resp, empty_resp, sessions_resp, empty_resp, empty_resp, empty_resp,
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        # Check the sessions list that was assigned to state
        sessions = state.sessions
        # state.sessions is set via format_timestamps_in_list, which returns the list
        # The items were mutated in-place before that call
        # We need to check the call to sessions — use the mock set
        # Since state is MagicMock, state.sessions was set to a return value
        # Let's check the sessions_resp items were mutated
        items = sessions_resp.json()["items"]
        assert items[0].get("source_type") == "CC"

    @patch("httpx.Client")
    def test_cc_slug_session_gets_cc_source(self, MockClient):
        """Sessions with -CC- in ID get source_type='CC'."""
        state = MagicMock()
        empty_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, {
            "items": [
                {"session_id": "SESSION-2026-02-11-CC-TEST", "start_time": "",
                 "end_time": "", "agent_id": "a1"},
            ],
            "pagination": {"total": 1},
        })

        mock_client = MagicMock()
        mock_client.get.side_effect = [
            empty_resp, empty_resp, sessions_resp, empty_resp, empty_resp, empty_resp,
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        items = sessions_resp.json()["items"]
        assert items[0].get("source_type") == "CC"

    @patch("httpx.Client")
    def test_chat_session_gets_chat_source(self, MockClient):
        """Sessions with -CHAT- in ID get source_type='Chat'."""
        state = MagicMock()
        empty_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, {
            "items": [
                {"session_id": "SESSION-2026-02-11-CHAT-TEST", "start_time": "",
                 "end_time": "", "agent_id": "a1"},
            ],
            "pagination": {"total": 1},
        })

        mock_client = MagicMock()
        mock_client.get.side_effect = [
            empty_resp, empty_resp, sessions_resp, empty_resp, empty_resp, empty_resp,
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        items = sessions_resp.json()["items"]
        assert items[0].get("source_type") == "Chat"

    @patch("httpx.Client")
    def test_mcp_auto_session_gets_chat_source(self, MockClient):
        """Sessions with -MCP-AUTO- in ID get source_type='Chat'."""
        state = MagicMock()
        empty_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, {
            "items": [
                {"session_id": "SESSION-2026-02-11-MCP-AUTO-abc", "start_time": "",
                 "end_time": "", "agent_id": "a1"},
            ],
            "pagination": {"total": 1},
        })

        mock_client = MagicMock()
        mock_client.get.side_effect = [
            empty_resp, empty_resp, sessions_resp, empty_resp, empty_resp, empty_resp,
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        items = sessions_resp.json()["items"]
        assert items[0].get("source_type") == "Chat"

    @patch("httpx.Client")
    def test_api_session_gets_api_source(self, MockClient):
        """Sessions without CC/Chat markers get source_type='API'."""
        state = MagicMock()
        empty_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, {
            "items": [
                {"session_id": "SESSION-2026-02-11-MANUAL", "start_time": "",
                 "end_time": "", "agent_id": "a1"},
            ],
            "pagination": {"total": 1},
        })

        mock_client = MagicMock()
        mock_client.get.side_effect = [
            empty_resp, empty_resp, sessions_resp, empty_resp, empty_resp, empty_resp,
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        items = sessions_resp.json()["items"]
        assert items[0].get("source_type") == "API"

    @patch("httpx.Client")
    def test_existing_source_type_not_overwritten(self, MockClient):
        """Pre-existing source_type is preserved."""
        state = MagicMock()
        empty_resp = _mock_response(200, [])
        sessions_resp = _mock_response(200, {
            "items": [
                {"session_id": "SESSION-2026-02-11-CHAT-X", "start_time": "",
                 "end_time": "", "agent_id": "a1", "source_type": "Custom"},
            ],
            "pagination": {"total": 1},
        })

        mock_client = MagicMock()
        mock_client.get.side_effect = [
            empty_resp, empty_resp, sessions_resp, empty_resp, empty_resp, empty_resp,
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        load_initial_data(state, "http://localhost:8082",
                          MagicMock(), MagicMock(), MagicMock(), MagicMock())

        items = sessions_resp.json()["items"]
        assert items[0].get("source_type") == "Custom"
