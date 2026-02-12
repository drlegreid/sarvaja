"""
Unit tests for Session Relations Routes.

Per DOC-SIZE-01-v1: Tests for routes/sessions/relations.py module.
Tests: link_evidence, get_session_tasks, get_session_evidence,
       _scan_evidence_filesystem.

Note: tool_calls and thoughts endpoints were removed from relations.py
(they shadowed working endpoints in detail.py). Tests moved to
test_data_pipeline_fixes.py.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

_P = "governance.routes.sessions.relations"


# ── link_evidence_to_session ────────────────────────────────────


class TestLinkEvidence:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.sessions.relations import link_evidence_to_session, EvidenceLink
        client = MagicMock()
        client.get_session.return_value = MagicMock()
        client.link_evidence_to_session.return_value = True
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = await link_evidence_to_session("S-1", EvidenceLink(evidence_source="ev.md"))
        assert result["session_id"] == "S-1"
        assert result["evidence_source"] == "ev.md"

    @pytest.mark.asyncio
    async def test_no_client(self):
        from governance.routes.sessions.relations import link_evidence_to_session, EvidenceLink
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await link_evidence_to_session("S-1", EvidenceLink(evidence_source="ev.md"))
            assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_session_not_found(self):
        from governance.routes.sessions.relations import link_evidence_to_session, EvidenceLink
        client = MagicMock()
        client.get_session.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=client):
            with pytest.raises(HTTPException) as exc:
                await link_evidence_to_session("S-MISSING", EvidenceLink(evidence_source="ev.md"))
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_link_failure(self):
        from governance.routes.sessions.relations import link_evidence_to_session, EvidenceLink
        client = MagicMock()
        client.get_session.return_value = MagicMock()
        client.link_evidence_to_session.return_value = False
        with patch(f"{_P}.get_typedb_client", return_value=client):
            with pytest.raises(HTTPException) as exc:
                await link_evidence_to_session("S-1", EvidenceLink(evidence_source="ev.md"))
            assert exc.value.status_code == 500


# ── get_session_tasks ───────────────────────────────────────────


class TestGetSessionTasks:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.sessions.relations import get_session_tasks
        client = MagicMock()
        client.get_session.return_value = MagicMock()
        client.get_tasks_for_session.return_value = [{"task_id": "T-1"}]
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = await get_session_tasks("S-1")
        assert result["task_count"] == 1

    @pytest.mark.asyncio
    async def test_no_client(self):
        from governance.routes.sessions.relations import get_session_tasks
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await get_session_tasks("S-1")
            assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_session_not_found(self):
        from governance.routes.sessions.relations import get_session_tasks
        client = MagicMock()
        client.get_session.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=client):
            with pytest.raises(HTTPException) as exc:
                await get_session_tasks("S-MISSING")
            assert exc.value.status_code == 404


# ── get_session_evidence ────────────────────────────────────────


class TestGetSessionEvidence:
    @pytest.mark.asyncio
    async def test_typedb_success(self):
        from governance.routes.sessions.relations import get_session_evidence
        client = MagicMock()
        client.get_session.return_value = MagicMock()
        client.get_session_evidence.return_value = ["evidence/file.md"]
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = await get_session_evidence("S-1")
        assert result["evidence_count"] == 1

    @pytest.mark.asyncio
    async def test_no_client_filesystem_fallback(self, tmp_path):
        from governance.routes.sessions.relations import get_session_evidence
        ev_dir = tmp_path / "evidence"
        ev_dir.mkdir()
        (ev_dir / "SESSION-S-1.md").write_text("evidence")
        with patch(f"{_P}.get_typedb_client", return_value=None), \
             patch("os.getcwd", return_value=str(tmp_path)):
            result = await get_session_evidence("S-1")
        assert result["evidence_count"] == 1

    @pytest.mark.asyncio
    async def test_session_not_found(self):
        from governance.routes.sessions.relations import get_session_evidence
        client = MagicMock()
        client.get_session.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=client):
            with pytest.raises(HTTPException) as exc:
                await get_session_evidence("S-MISSING")
            assert exc.value.status_code == 404


# ── _scan_evidence_filesystem ───────────────────────────────────


class TestScanEvidenceFilesystem:
    def test_matches_files(self, tmp_path):
        from governance.routes.sessions.relations import _scan_evidence_filesystem
        ev_dir = tmp_path / "evidence"
        ev_dir.mkdir()
        (ev_dir / "SESSION-2026-01-01-TEST.md").write_text("ev")
        (ev_dir / "OTHER.md").write_text("other")
        with patch("os.getcwd", return_value=str(tmp_path)):
            result = _scan_evidence_filesystem("SESSION-2026-01-01-TEST")
        assert len(result) == 1
        assert "SESSION-2026-01-01-TEST.md" in result[0]

    def test_no_evidence_dir(self, tmp_path):
        from governance.routes.sessions.relations import _scan_evidence_filesystem
        with patch("os.getcwd", return_value=str(tmp_path)):
            result = _scan_evidence_filesystem("S-1")
        assert result == []

    def test_no_matches(self, tmp_path):
        from governance.routes.sessions.relations import _scan_evidence_filesystem
        ev_dir = tmp_path / "evidence"
        ev_dir.mkdir()
        (ev_dir / "OTHER.md").write_text("other")
        with patch("os.getcwd", return_value=str(tmp_path)):
            result = _scan_evidence_filesystem("S-UNIQUE")
        assert result == []
