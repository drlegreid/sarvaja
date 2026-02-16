"""
Unit tests for transcript.py route (GAP-SESSION-TRANSCRIPT-001).

Tests the /sessions/{id}/transcript API endpoints.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from governance.routes.sessions.transcript import router
from governance.session_metrics.models import TranscriptEntry


# Build a minimal FastAPI app for route testing
from fastapi import FastAPI

_app = FastAPI()
_app.include_router(router, prefix="/api")
client = TestClient(_app)


class TestSessionTranscriptRoute:
    @patch("governance.routes.sessions.transcript.find_jsonl_for_session")
    @patch("governance.routes.sessions.transcript.session_service")
    @patch("governance.routes.sessions.transcript.get_transcript_page")
    def test_paginated_response_shape(self, mock_get_page, mock_service, mock_find):
        """Transcript endpoint returns properly shaped response."""
        mock_service.get_session.return_value = {"session_id": "S-1"}
        mock_find.return_value = Path("/tmp/test.jsonl")
        mock_get_page.return_value = {
            "entries": [{"index": 0, "entry_type": "user_prompt", "content": "hi"}],
            "total": 1,
            "page": 1,
            "per_page": 50,
            "has_more": False,
        }

        resp = client.get("/api/sessions/S-1/transcript")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "total" in data
        assert data["session_id"] == "S-1"

    @patch("governance.routes.sessions.transcript.session_service")
    def test_session_not_found_returns_404(self, mock_service):
        """404 when session_id doesn't exist."""
        mock_service.get_session.return_value = None

        resp = client.get("/api/sessions/NONEXISTENT/transcript")
        assert resp.status_code == 404

    @patch("governance.routes.sessions.transcript.find_evidence_file")
    @patch("governance.routes.sessions.transcript._sessions_store", {})
    @patch("governance.routes.sessions.transcript.find_jsonl_for_session")
    @patch("governance.routes.sessions.transcript.session_service")
    def test_no_jsonl_no_store_no_evidence_returns_empty(
        self, mock_service, mock_find, mock_ev,
    ):
        """Returns empty transcript when no JSONL, no store, no evidence."""
        mock_service.get_session.return_value = {"session_id": "S-1"}
        mock_find.return_value = None
        mock_ev.return_value = None

        resp = client.get("/api/sessions/S-1/transcript")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entries"] == []
        assert data["total"] == 0
        assert data["source"] == "none"

    @patch("governance.routes.sessions.transcript.parse_evidence_transcript")
    @patch("governance.routes.sessions.transcript.find_evidence_file")
    @patch("governance.routes.sessions.transcript._sessions_store", {})
    @patch("governance.routes.sessions.transcript.find_jsonl_for_session")
    @patch("governance.routes.sessions.transcript.session_service")
    def test_no_jsonl_no_store_with_evidence_returns_evidence(
        self, mock_service, mock_find, mock_ev, mock_parse,
    ):
        """Returns evidence-based transcript when only evidence file exists."""
        mock_service.get_session.return_value = {"session_id": "S-1"}
        mock_find.return_value = None
        mock_ev.return_value = Path("/tmp/evidence.md")
        mock_parse.return_value = {
            "entries": [{"index": 0, "entry_type": "tool_use", "tool_name": "/status"}],
            "total": 1, "page": 1, "per_page": 50, "has_more": False,
            "source": "evidence",
        }

        resp = client.get("/api/sessions/S-1/transcript")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "evidence"
        assert len(data["entries"]) == 1
        assert data["entries"][0]["entry_type"] == "tool_use"

    @patch("governance.routes.sessions.transcript._sessions_store",
           {"S-1": {"tool_calls": [{"tool_name": "Bash", "arguments": {},
                    "result": "ok", "success": True, "timestamp": "2026-02-15T10:00:00"}],
                    "thoughts": []}})
    @patch("governance.routes.sessions.transcript.find_jsonl_for_session")
    @patch("governance.routes.sessions.transcript.session_service")
    def test_no_jsonl_with_store_returns_synthetic(self, mock_service, mock_find):
        """Returns synthetic transcript from _sessions_store when no JSONL."""
        mock_service.get_session.return_value = {"session_id": "S-1"}
        mock_find.return_value = None

        resp = client.get("/api/sessions/S-1/transcript")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "synthetic"
        assert len(data["entries"]) == 2  # tool_use + tool_result
        assert data["entries"][0]["entry_type"] == "tool_use"
        assert data["entries"][1]["entry_type"] == "tool_result"

    @patch("governance.routes.sessions.transcript.find_jsonl_for_session")
    @patch("governance.routes.sessions.transcript.session_service")
    @patch("governance.routes.sessions.transcript.stream_transcript")
    def test_single_entry_expanded(self, mock_stream, mock_service, mock_find):
        """Single entry endpoint returns expanded content."""
        mock_service.get_session.return_value = {"session_id": "S-1"}
        mock_find.return_value = Path("/tmp/test.jsonl")

        entry = TranscriptEntry(
            index=5, timestamp="2026-02-15T10:00:00Z",
            entry_type="tool_use", content='{"command": "ls"}',
            content_length=17, tool_name="Bash",
        )
        mock_stream.return_value = iter([entry])

        resp = client.get("/api/sessions/S-1/transcript/5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entry"]["index"] == 5
        assert data["entry"]["tool_name"] == "Bash"

    @patch("governance.routes.sessions.transcript.find_jsonl_for_session")
    @patch("governance.routes.sessions.transcript.session_service")
    @patch("governance.routes.sessions.transcript.stream_transcript")
    def test_single_entry_not_found(self, mock_stream, mock_service, mock_find):
        """404 when entry_index doesn't exist in the file."""
        mock_service.get_session.return_value = {"session_id": "S-1"}
        mock_find.return_value = Path("/tmp/test.jsonl")
        mock_stream.return_value = iter([])  # No entries match

        resp = client.get("/api/sessions/S-1/transcript/999")
        assert resp.status_code == 404


class TestTranscriptQueryParams:
    @patch("governance.routes.sessions.transcript.find_jsonl_for_session")
    @patch("governance.routes.sessions.transcript.session_service")
    @patch("governance.routes.sessions.transcript.get_transcript_page")
    def test_query_params_passed_through(self, mock_get_page, mock_service, mock_find):
        """Query parameters are forwarded to the service."""
        mock_service.get_session.return_value = {"session_id": "S-1"}
        mock_find.return_value = Path("/tmp/test.jsonl")
        mock_get_page.return_value = {
            "entries": [], "total": 0, "page": 2, "per_page": 10, "has_more": False,
        }

        resp = client.get(
            "/api/sessions/S-1/transcript",
            params={"page": 2, "per_page": 10, "include_thinking": "false",
                    "include_user": "false", "content_limit": 500},
        )
        assert resp.status_code == 200
        mock_get_page.assert_called_once()
        call_kwargs = mock_get_page.call_args
        assert call_kwargs.kwargs.get("page") == 2 or call_kwargs[1].get("page") == 2
