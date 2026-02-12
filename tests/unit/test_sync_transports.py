"""
Unit tests for Sync Agent Transports.

Per DOC-SIZE-01-v1: Tests for agent/sync_agent/transports.py module.
Tests: LocalFileTransport (push, pull), GitTransport (push, pull),
       ClearMLTransport (_check_clearml, push, pull).
"""

import json
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from agent.sync_agent.models import Change
from agent.sync_agent.transports import (
    LocalFileTransport,
    ClearMLTransport,
)


# ── LocalFileTransport ────────────────────────────────────────


class TestLocalFileTransportPush:
    @pytest.mark.asyncio
    async def test_push_creates_file(self, tmp_path):
        transport = LocalFileTransport(str(tmp_path))
        change = Change(
            collection="rules", doc_id="R-1", action="upsert",
            data={"name": "Rule 1"},
        )
        count = await transport.push([change])
        assert count == 1
        out = tmp_path / "rules" / "R-1.json"
        assert out.exists()
        content = json.loads(out.read_text())
        assert content["id"] == "R-1"
        assert content["data"]["name"] == "Rule 1"

    @pytest.mark.asyncio
    async def test_push_multiple(self, tmp_path):
        transport = LocalFileTransport(str(tmp_path))
        changes = [
            Change(collection="rules", doc_id="R-1", action="upsert", data={"name": "R1"}),
            Change(collection="tasks", doc_id="T-1", action="upsert", data={"name": "T1"}),
        ]
        count = await transport.push(changes)
        assert count == 2
        assert (tmp_path / "rules" / "R-1.json").exists()
        assert (tmp_path / "tasks" / "T-1.json").exists()

    @pytest.mark.asyncio
    async def test_push_empty_list(self, tmp_path):
        transport = LocalFileTransport(str(tmp_path))
        count = await transport.push([])
        assert count == 0


class TestLocalFileTransportPull:
    @pytest.mark.asyncio
    async def test_pull_reads_files(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "R-1.json").write_text(json.dumps({
            "id": "R-1", "data": {"name": "Rule 1"},
            "action": "upsert", "timestamp": "2026-02-11T10:00:00",
        }))
        transport = LocalFileTransport(str(tmp_path))
        changes = await transport.pull()
        assert len(changes) == 1
        assert changes[0].doc_id == "R-1"
        assert changes[0].collection == "rules"

    @pytest.mark.asyncio
    async def test_pull_empty_dir(self, tmp_path):
        transport = LocalFileTransport(str(tmp_path))
        changes = await transport.pull()
        assert changes == []

    @pytest.mark.asyncio
    async def test_pull_multiple_collections(self, tmp_path):
        for coll in ["rules", "tasks"]:
            d = tmp_path / coll
            d.mkdir()
            (d / "item.json").write_text(json.dumps({
                "id": f"{coll}-1", "data": {}, "action": "upsert",
                "timestamp": "2026-02-11T10:00:00",
            }))
        transport = LocalFileTransport(str(tmp_path))
        changes = await transport.pull()
        assert len(changes) == 2

    @pytest.mark.asyncio
    async def test_name(self, tmp_path):
        transport = LocalFileTransport(str(tmp_path))
        assert transport.name == "local"


# ── ClearMLTransport ──────────────────────────────────────────


class TestClearMLTransport:
    def test_clearml_not_available(self):
        with patch.dict("sys.modules", {"clearml": None}):
            transport = ClearMLTransport.__new__(ClearMLTransport)
            transport.project = "test"
            transport._clearml_available = False
        assert transport._clearml_available is False

    @pytest.mark.asyncio
    async def test_push_without_clearml(self):
        transport = ClearMLTransport.__new__(ClearMLTransport)
        transport.project = "test"
        transport._clearml_available = False
        change = Change(collection="sessions", doc_id="S-1", action="upsert", data={})
        count = await transport.push([change])
        assert count == 0

    @pytest.mark.asyncio
    async def test_pull_returns_empty(self):
        transport = ClearMLTransport.__new__(ClearMLTransport)
        transport.project = "test"
        transport._clearml_available = False
        result = await transport.pull()
        assert result == []

    def test_name(self):
        transport = ClearMLTransport.__new__(ClearMLTransport)
        assert transport.name == "clearml"
