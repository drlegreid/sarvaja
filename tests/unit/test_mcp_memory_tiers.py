"""
Unit tests for Memory Tiers MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/memory_tiers.py module.
Tests: memory_save(), memory_recall().
"""

import json
import pytest
from unittest.mock import patch

import governance.mcp_tools.memory_tiers as _mem_mod
from governance.mcp_tools.memory_tiers import register_memory_tier_tools


def _json_format(data, **kwargs):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        if callable(name):
            self.tools[name.__name__] = name
            return name

        def decorator(fn):
            key = name if name else fn.__name__
            self.tools[key] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_memory_tier_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _force_json_and_clean():
    _mem_mod._short_memory.clear()
    with patch(
        "governance.mcp_tools.memory_tiers.format_mcp_result",
        side_effect=_json_format,
    ):
        yield
    _mem_mod._short_memory.clear()


class TestRegistration:
    def test_registers_two_tools(self):
        mcp = _register()
        assert "memory_save" in mcp.tools
        assert "memory_recall" in mcp.tools


class TestMemorySaveL1:
    """Tests for memory_save() L1 tier."""

    def test_save_l1(self):
        mcp = _register()
        result = json.loads(mcp.tools["memory_save"](tier="L1", content="test data"))
        assert result["tier"] == "L1"
        assert result["status"] == "saved"
        assert len(_mem_mod._short_memory) == 1

    def test_save_l1_with_tags(self):
        mcp = _register()
        result = json.loads(mcp.tools["memory_save"](
            tier="L1", content="tagged", tags="auth,security"
        ))
        assert result["status"] == "saved"
        mem_id = result["memory_id"]
        assert _mem_mod._short_memory[mem_id]["tags"] == ["auth", "security"]

    def test_save_l1_with_session(self):
        mcp = _register()
        mcp.tools["memory_save"](tier="L1", content="ctx", session_id="SESSION-TEST")
        vals = list(_mem_mod._short_memory.values())
        assert vals[0]["session_id"] == "SESSION-TEST"


class TestMemorySaveL2:
    """Tests for memory_save() L2 tier - fallback path."""

    def test_l2_chromadb_unavailable_fallback(self):
        """When ChromaDB fails, L2 falls back to L1 storage."""
        mcp = _register()
        # ChromaDB will likely fail since we're in unit test (no server)
        result = json.loads(mcp.tools["memory_save"](tier="L2", content="test"))
        assert result["tier"] == "L2"
        # Either saved to ChromaDB or fell back to L1
        assert "saved" in result["status"] or "fallback" in result["status"]


class TestMemorySaveL3:
    """Tests for memory_save() L3 tier."""

    @patch("governance.stores.audit.record_audit")
    @patch("governance.stores.audit._save_audit_store")
    @patch("governance.stores.audit._apply_retention")
    def test_save_l3_success(self, mock_ret, mock_save, mock_audit):
        mcp = _register()
        result = json.loads(mcp.tools["memory_save"](tier="L3", content="persistent"))
        assert result["tier"] == "L3"
        assert result["status"] == "saved_typedb_audit"


class TestMemorySaveInvalid:
    def test_unknown_tier(self):
        mcp = _register()
        result = json.loads(mcp.tools["memory_save"](tier="L99", content="test"))
        assert "error" in result


class TestMemoryRecallL1:
    """Tests for memory_recall() L1 tier."""

    def test_recall_content_match(self):
        mcp = _register()
        mcp.tools["memory_save"](tier="L1", content="TypeDB migration plan")
        result = json.loads(mcp.tools["memory_recall"](query="typedb", tier="L1"))
        assert result["total"] >= 1

    def test_recall_tag_match(self):
        mcp = _register()
        mcp.tools["memory_save"](tier="L1", content="some data", tags="security")
        result = json.loads(mcp.tools["memory_recall"](query="security", tier="L1"))
        assert result["total"] >= 1

    def test_recall_no_match(self):
        mcp = _register()
        mcp.tools["memory_save"](tier="L1", content="unrelated stuff")
        result = json.loads(mcp.tools["memory_recall"](query="nonexistent_xyz", tier="L1"))
        assert result["total"] == 0

    def test_recall_returns_content(self):
        mcp = _register()
        mcp.tools["memory_save"](tier="L1", content="important data about tests")
        result = json.loads(mcp.tools["memory_recall"](query="important", tier="L1"))
        assert result["total"] >= 1
        assert "important" in result["results"][0]["content"]


class TestMemoryRecallL3:
    """Tests for memory_recall() L3 tier (audit trail)."""

    @patch("governance.stores.audit.query_audit_trail")
    def test_recall_l3_match(self, mock_query):
        mock_query.return_value = [
            {"entity_id": "MEM-L3-001", "timestamp": "2026-02-11",
             "metadata": {"content": "TypeDB rules", "tags": ["gov"]}},
        ]
        mcp = _register()
        result = json.loads(mcp.tools["memory_recall"](query="typedb", tier="L3"))
        assert result["total"] >= 1

    @patch("governance.stores.audit.query_audit_trail")
    def test_recall_l3_no_match(self, mock_query):
        mock_query.return_value = [
            {"entity_id": "MEM-L3-001", "timestamp": "2026-02-11",
             "metadata": {"content": "unrelated"}},
        ]
        mcp = _register()
        result = json.loads(mcp.tools["memory_recall"](query="zzz_nonexistent", tier="L3"))
        assert result["total"] == 0
