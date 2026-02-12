"""
Unit tests for Evidence Routes.

Per DOC-SIZE-01-v1: Tests for routes/evidence.py module.
Tests: _extract_session_id, list_evidence, search_evidence, get_evidence.
"""

import os
from io import StringIO
from unittest.mock import patch, MagicMock, mock_open

import pytest

from governance.routes.evidence import _extract_session_id


class TestExtractSessionId:
    def test_valid_pattern(self):
        assert _extract_session_id("SESSION-2026-02-11-001.md") == "SESSION-2026-02-11-001"

    def test_no_match(self):
        assert _extract_session_id("random-file.md") is None

    def test_embedded_in_longer_name(self):
        result = _extract_session_id("SESSION-2026-01-01-002-extra.md")
        assert result == "SESSION-2026-01-01-002"


class TestListEvidence:
    @pytest.mark.asyncio
    async def test_no_evidence_dir(self):
        with patch("governance.routes.evidence.os.path.exists", return_value=False):
            from governance.routes.evidence import list_evidence
            result = await list_evidence(offset=0, limit=20)
        assert result == []

    @pytest.mark.asyncio
    async def test_with_files(self):
        files = ["SESSION-2026-01-01-001.md", "SESSION-2026-01-02-001.md"]
        with patch("governance.routes.evidence.os.path.exists", return_value=True), \
             patch("governance.routes.evidence.os.listdir", return_value=files), \
             patch("builtins.open", mock_open(read_data="# Test content")), \
             patch("governance.routes.evidence.os.path.getctime", return_value=1707638400.0):
            from governance.routes.evidence import list_evidence
            result = await list_evidence(offset=0, limit=20)
        assert len(result) == 2
        assert result[0].session_id == "SESSION-2026-01-01-001"

    @pytest.mark.asyncio
    async def test_pagination(self):
        files = [f"SESSION-2026-01-{i:02d}-001.md" for i in range(1, 6)]
        with patch("governance.routes.evidence.os.path.exists", return_value=True), \
             patch("governance.routes.evidence.os.listdir", return_value=files), \
             patch("builtins.open", mock_open(read_data="# Test")), \
             patch("governance.routes.evidence.os.path.getctime", return_value=1707638400.0):
            from governance.routes.evidence import list_evidence
            result = await list_evidence(offset=2, limit=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_read_error_skipped(self):
        with patch("governance.routes.evidence.os.path.exists", return_value=True), \
             patch("governance.routes.evidence.os.listdir", return_value=["bad.md"]), \
             patch("builtins.open", side_effect=IOError("read error")):
            from governance.routes.evidence import list_evidence
            result = await list_evidence(offset=0, limit=20)
        assert result == []


class TestSearchEvidence:
    @pytest.mark.asyncio
    async def test_keyword_fallback(self, tmp_path):
        # Create a real file for keyword search
        evidence_file = tmp_path / "test.md"
        evidence_file.write_text("This is about testing")

        with patch("governance.routes.evidence.glob.glob",
                   return_value=[str(evidence_file)]):
            from governance.routes.evidence import search_evidence
            result = await search_evidence(query="testing", top_k=5, source_type=None)
        assert result.search_method == "keyword_fallback"
        assert result.count >= 1

    @pytest.mark.asyncio
    async def test_no_results(self):
        with patch("governance.routes.evidence.glob.glob", return_value=[]):
            from governance.routes.evidence import search_evidence
            result = await search_evidence(query="nonexistent", top_k=5, source_type=None)
        assert result.count == 0
        assert result.search_method == "keyword_fallback"

    @pytest.mark.asyncio
    async def test_source_type_filter(self):
        # With source_type="rule", the evidence glob is skipped
        with patch("governance.routes.evidence.glob.glob", return_value=[]):
            from governance.routes.evidence import search_evidence
            result = await search_evidence(query="test", top_k=5, source_type="rule")
        assert result.count == 0

    @pytest.mark.asyncio
    async def test_results_sorted_by_score(self, tmp_path):
        file1 = tmp_path / "low.md"
        file1.write_text("test")  # 1 occurrence
        file2 = tmp_path / "high.md"
        file2.write_text("test test test")  # 3 occurrences

        with patch("governance.routes.evidence.glob.glob",
                   side_effect=[[str(file1), str(file2)], []]):
            from governance.routes.evidence import search_evidence
            result = await search_evidence(query="test", top_k=5, source_type=None)
        assert result.count == 2
        # Higher score first
        assert result.results[0].score >= result.results[1].score


class TestGetEvidence:
    @pytest.mark.asyncio
    async def test_found(self, tmp_path):
        # Write a real evidence file to match the path the route constructs
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
        (evidence_dir / "SESSION-2026-01-01-001.md").write_text("# Evidence")

        # We need the route to find our tmp dir. The route calculates
        # evidence_dir from __file__, so we patch the relevant os calls.
        real_evidence_dir = str(evidence_dir)
        filepath = str(evidence_dir / "SESSION-2026-01-01-001.md")

        with patch("governance.routes.evidence.os.path.join",
                   side_effect=[real_evidence_dir, filepath]), \
             patch("governance.routes.evidence.os.path.realpath",
                   side_effect=lambda x: x), \
             patch("governance.routes.evidence.os.path.exists", return_value=True), \
             patch("governance.routes.evidence.os.path.getctime", return_value=1707638400.0), \
             patch("builtins.open", mock_open(read_data="# Evidence content")):
            from governance.routes.evidence import get_evidence
            result = await get_evidence("SESSION-2026-01-01-001")
        assert result.evidence_id == "SESSION-2026-01-01-001"
        assert result.session_id == "SESSION-2026-01-01-001"

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        with patch("governance.routes.evidence.os.path.join",
                   side_effect=["/fake/evidence", "/fake/evidence/MISSING.md"]), \
             patch("governance.routes.evidence.os.path.realpath",
                   side_effect=lambda x: x), \
             patch("governance.routes.evidence.os.path.exists", return_value=False):
            from governance.routes.evidence import get_evidence
            with pytest.raises(HTTPException) as exc_info:
                await get_evidence("MISSING")
            assert exc_info.value.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self):
        from fastapi import HTTPException
        # realpath resolves to outside evidence dir
        with patch("governance.routes.evidence.os.path.join",
                   side_effect=["/app/evidence", "/app/evidence/../../etc/passwd.md"]), \
             patch("governance.routes.evidence.os.path.realpath",
                   side_effect=["/etc/passwd.md", "/app/evidence"]), \
             patch("governance.routes.evidence.os.path.exists", return_value=True):
            from governance.routes.evidence import get_evidence
            with pytest.raises(HTTPException) as exc_info:
                await get_evidence("../../etc/passwd")
            assert exc_info.value.status_code == 403
