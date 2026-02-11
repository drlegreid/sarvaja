"""
Unit tests for Three-Tier Memory Model MCP Tools.

Per EPIC-G: Tests for memory_save (L1/L2/L3) and memory_recall.
Focus on L1 in-process path and validation logic.
"""

import json
import sys
import pytest
from unittest.mock import patch, MagicMock

import governance.mcp_tools.memory_tiers as mem_mod
from governance.mcp_tools.memory_tiers import register_memory_tier_tools


def _json_format(data, **kw):
    """Force JSON output instead of TOON."""
    return json.dumps(data, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _force_json():
    with patch("governance.mcp_tools.memory_tiers.format_mcp_result", side_effect=_json_format):
        yield


@pytest.fixture(autouse=True)
def _clear_short_memory():
    """Clear L1 memory before each test."""
    mem_mod._short_memory.clear()
    yield
    mem_mod._short_memory.clear()


@pytest.fixture(autouse=True)
def _block_chromadb():
    """Block chromadb import to prevent real ChromaDB interaction."""
    original = sys.modules.get("chromadb")
    sys.modules["chromadb"] = None  # type: ignore[assignment]
    yield
    if original is not None:
        sys.modules["chromadb"] = original
    else:
        sys.modules.pop("chromadb", None)


@pytest.fixture
def mcp_tools():
    mcp = _CaptureMCP()
    register_memory_tier_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# memory_save - L1
# ---------------------------------------------------------------------------
class TestMemorySaveL1:
    """Tests for memory_save() L1 tier."""

    def test_save_l1_basic(self, mcp_tools):
        result = json.loads(mcp_tools["memory_save"](tier="L1", content="test data"))
        assert result["tier"] == "L1"
        assert result["status"] == "saved"
        assert result["memory_id"].startswith("MEM-L1-")

    def test_save_l1_with_tags(self, mcp_tools):
        mcp_tools["memory_save"](tier="L1", content="tagged", tags="rules,sessions")
        assert len(mem_mod._short_memory) == 1
        mem = list(mem_mod._short_memory.values())[0]
        assert mem["tags"] == ["rules", "sessions"]

    def test_save_l1_with_session(self, mcp_tools):
        mcp_tools["memory_save"](tier="L1", content="test", session_id="S-1")
        mem = list(mem_mod._short_memory.values())[0]
        assert mem["session_id"] == "S-1"

    def test_save_l1_case_insensitive(self, mcp_tools):
        result = json.loads(mcp_tools["memory_save"](tier="l1", content="lower case"))
        assert result["tier"] == "L1"

    def test_save_l1_stores_timestamp(self, mcp_tools):
        mcp_tools["memory_save"](tier="L1", content="ts test")
        mem = list(mem_mod._short_memory.values())[0]
        assert "created" in mem
        assert "T" in mem["created"]  # ISO format

    def test_save_l1_empty_tags(self, mcp_tools):
        mcp_tools["memory_save"](tier="L1", content="no tags")
        mem = list(mem_mod._short_memory.values())[0]
        assert mem["tags"] == []


# ---------------------------------------------------------------------------
# memory_save - L2 fallback
# ---------------------------------------------------------------------------
class TestMemorySaveL2:
    """Tests for memory_save() L2 tier (ChromaDB fallback)."""

    def test_save_l2_fallback_to_l1(self, mcp_tools):
        """With chromadb blocked, L2 falls back to L1 storage."""
        result = json.loads(mcp_tools["memory_save"](tier="L2", content="l2 data"))
        assert result["tier"] == "L2"
        assert result["status"] == "saved_fallback_L1"
        assert "warning" in result
        assert len(mem_mod._short_memory) == 1
        mem = list(mem_mod._short_memory.values())[0]
        assert mem["intended_tier"] == "L2"


# ---------------------------------------------------------------------------
# memory_save - L3
# ---------------------------------------------------------------------------
class TestMemorySaveL3:
    """Tests for memory_save() L3 tier."""

    def test_save_l3_audit_unavailable(self, mcp_tools):
        """When audit store unavailable, returns error."""
        result = json.loads(mcp_tools["memory_save"](tier="L3", content="persistent"))
        assert result["tier"] == "L3"
        assert result["status"] in ("saved_typedb_audit", "error")

    def test_save_unknown_tier(self, mcp_tools):
        result = json.loads(mcp_tools["memory_save"](tier="L4", content="bad"))
        assert "error" in result
        assert "Unknown tier" in result["error"]


# ---------------------------------------------------------------------------
# memory_recall - L1 only (chromadb blocked)
# ---------------------------------------------------------------------------
class TestMemoryRecallL1:
    """Tests for memory_recall() with L1 search (chromadb blocked)."""

    def test_recall_empty(self, mcp_tools):
        result = json.loads(mcp_tools["memory_recall"](query="anything", tier="L1"))
        assert result["total"] == 0
        assert result["results"] == []

    def test_recall_content_match(self, mcp_tools):
        # Insert directly to avoid timestamp collision
        mem_mod._short_memory["MEM-L1-A"] = {
            "content": "Fix the login bug", "tags": [], "session_id": None, "created": "now",
        }
        mem_mod._short_memory["MEM-L1-B"] = {
            "content": "Add dashboard feature", "tags": [], "session_id": None, "created": "now",
        }
        result = json.loads(mcp_tools["memory_recall"](query="login", tier="L1"))
        assert result["total"] == 1
        assert "login" in result["results"][0]["content"].lower()

    def test_recall_tag_match(self, mcp_tools):
        mem_mod._short_memory["MEM-L1-C"] = {
            "content": "Some data", "tags": ["auth", "security"],
            "session_id": None, "created": "now",
        }
        result = json.loads(mcp_tools["memory_recall"](query="auth", tier="L1"))
        assert result["total"] == 1

    def test_recall_case_insensitive(self, mcp_tools):
        mem_mod._short_memory["MEM-L1-D"] = {
            "content": "UPPERCASE content", "tags": [], "session_id": None, "created": "now",
        }
        result = json.loads(mcp_tools["memory_recall"](query="uppercase", tier="L1"))
        assert result["total"] == 1

    def test_recall_limit(self, mcp_tools):
        for i in range(10):
            mem_mod._short_memory[f"MEM-L1-{i}"] = {
                "content": f"Item number {i} about rules", "tags": [],
                "session_id": None, "created": "now",
            }
        result = json.loads(mcp_tools["memory_recall"](query="rules", tier="L1", limit=3))
        assert len(result["results"]) == 3

    def test_recall_truncates_content(self, mcp_tools):
        mcp_tools["memory_save"](tier="L1", content="A" * 500)
        result = json.loads(mcp_tools["memory_recall"](query="AAAA", tier="L1"))
        assert len(result["results"][0]["content"]) <= 300

    def test_recall_returns_metadata(self, mcp_tools):
        mcp_tools["memory_save"](tier="L1", content="test data", tags="tag1")
        result = json.loads(mcp_tools["memory_recall"](query="test", tier="L1"))
        r = result["results"][0]
        assert r["tier"] == "L1"
        assert "memory_id" in r
        assert "created" in r
        assert "tags" in r

    def test_recall_no_match(self, mcp_tools):
        mcp_tools["memory_save"](tier="L1", content="hello world")
        result = json.loads(mcp_tools["memory_recall"](query="nonexistent", tier="L1"))
        assert result["total"] == 0
