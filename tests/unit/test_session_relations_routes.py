"""
Unit tests for Session Relations Routes.

Batch 127: Tests for governance/routes/sessions/relations.py
- link_evidence_to_session: TypeDB link + error handling
- get_session_tasks: linked tasks query
- get_session_evidence: TypeDB + filesystem fallback
- _scan_evidence_filesystem: directory scan

Note: tool_calls and thoughts endpoints were removed from relations.py
(they shadowed working endpoints in detail.py). Tests moved to
test_data_pipeline_fixes.py.
"""

import os
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from governance.routes.sessions.relations import router, _scan_evidence_filesystem


_MOD = "governance.routes.sessions.relations"

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)


# ── link_evidence_to_session ─────────────────────────────


class TestLinkEvidenceToSession:

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    def test_no_typedb_returns_503(self, mock_client):
        resp = client.post("/api/sessions/S-1/evidence",
                           json={"evidence_source": "evidence/test.md"})
        assert resp.status_code == 503

    @patch(f"{_MOD}.get_typedb_client")
    def test_session_not_found_returns_404(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_session.return_value = None
        mock_get.return_value = mock_db

        resp = client.post("/api/sessions/MISSING/evidence",
                           json={"evidence_source": "evidence/test.md"})
        assert resp.status_code == 404

    @patch(f"{_MOD}.get_typedb_client")
    def test_successful_link(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_session.return_value = MagicMock()
        mock_db.link_evidence_to_session.return_value = True
        mock_get.return_value = mock_db

        resp = client.post("/api/sessions/S-1/evidence",
                           json={"evidence_source": "evidence/test.md"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["session_id"] == "S-1"
        assert data["evidence_source"] == "evidence/test.md"

    @patch(f"{_MOD}.get_typedb_client")
    def test_link_failure_returns_500(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_session.return_value = MagicMock()
        mock_db.link_evidence_to_session.return_value = False
        mock_get.return_value = mock_db

        resp = client.post("/api/sessions/S-1/evidence",
                           json={"evidence_source": "evidence/test.md"})
        assert resp.status_code == 500


# ── get_session_tasks ────────────────────────────────────


class TestGetSessionTasks:

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    def test_no_typedb_returns_503(self, mock_client):
        resp = client.get("/api/sessions/S-1/tasks")
        assert resp.status_code == 503

    @patch(f"{_MOD}.get_typedb_client")
    def test_session_not_found(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_session.return_value = None
        mock_get.return_value = mock_db

        resp = client.get("/api/sessions/MISSING/tasks")
        assert resp.status_code == 404

    @patch(f"{_MOD}.get_typedb_client")
    def test_returns_tasks(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_session.return_value = MagicMock()
        mock_db.get_tasks_for_session.return_value = [
            {"task_id": "T-1", "name": "Task", "status": "OPEN"}
        ]
        mock_get.return_value = mock_db

        resp = client.get("/api/sessions/S-1/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_count"] == 1
        assert data["tasks"][0]["task_id"] == "T-1"


# ── get_session_evidence ─────────────────────────────────


class TestGetSessionEvidence:

    @patch(f"{_MOD}.get_typedb_client", return_value=None)
    @patch(f"{_MOD}._scan_evidence_filesystem", return_value=["evidence/S-1.md"])
    def test_no_typedb_uses_filesystem(self, mock_scan, mock_get):
        resp = client.get("/api/sessions/S-1/evidence")
        data = resp.json()
        assert data["evidence_count"] == 1
        assert "evidence/S-1.md" in data["evidence_files"]

    @patch(f"{_MOD}.get_typedb_client")
    def test_session_not_found(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_session.return_value = None
        mock_get.return_value = mock_db

        resp = client.get("/api/sessions/MISSING/evidence")
        assert resp.status_code == 404

    @patch(f"{_MOD}.get_typedb_client")
    def test_typedb_returns_evidence(self, mock_get):
        mock_db = MagicMock()
        mock_db.get_session.return_value = MagicMock()
        mock_db.get_session_evidence.return_value = ["evidence/test.md"]
        mock_get.return_value = mock_db

        resp = client.get("/api/sessions/S-1/evidence")
        data = resp.json()
        assert data["evidence_count"] == 1

    @patch(f"{_MOD}.get_typedb_client")
    @patch(f"{_MOD}._scan_evidence_filesystem", return_value=["evidence/S-1-fs.md"])
    def test_typedb_empty_falls_back_to_filesystem(self, mock_scan, mock_get):
        mock_db = MagicMock()
        mock_db.get_session.return_value = MagicMock()
        mock_db.get_session_evidence.return_value = []
        mock_get.return_value = mock_db

        resp = client.get("/api/sessions/S-1/evidence")
        data = resp.json()
        assert data["evidence_count"] == 1
        mock_scan.assert_called_once()


# ── _scan_evidence_filesystem ────────────────────────────


class TestScanEvidenceFilesystem:

    def test_no_evidence_dir(self, tmp_path):
        with patch("os.getcwd", return_value=str(tmp_path)):
            result = _scan_evidence_filesystem("S-1")
            assert result == []

    def test_matches_session_id(self, tmp_path):
        ev_dir = tmp_path / "evidence"
        ev_dir.mkdir()
        (ev_dir / "SESSION-2026-02-11-S-1.md").write_text("evidence")
        (ev_dir / "SESSION-2026-02-11-S-2.md").write_text("other")
        (ev_dir / "unrelated.txt").write_text("not md")

        with patch("os.getcwd", return_value=str(tmp_path)):
            result = _scan_evidence_filesystem("S-1")
            assert len(result) == 1
            assert "S-1" in result[0]

    def test_returns_sorted(self, tmp_path):
        ev_dir = tmp_path / "evidence"
        ev_dir.mkdir()
        (ev_dir / "SESSION-B-CHAT.md").write_text("b")
        (ev_dir / "SESSION-A-CHAT.md").write_text("a")

        with patch("os.getcwd", return_value=str(tmp_path)):
            result = _scan_evidence_filesystem("CHAT")
            assert result == sorted(result)

    def test_skips_non_md(self, tmp_path):
        ev_dir = tmp_path / "evidence"
        ev_dir.mkdir()
        (ev_dir / "SESSION-S1.json").write_text("json")
        (ev_dir / "SESSION-S1.md").write_text("md")

        with patch("os.getcwd", return_value=str(tmp_path)):
            result = _scan_evidence_filesystem("S1")
            assert len(result) == 1
            assert result[0].endswith(".md")
