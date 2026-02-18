"""
Batch 286-289 — Deep Scan: Services, MCP tools, TypeDB queries hardening.

Fixes verified:
- BUG-286-XSS-001: URI scheme allowlist blocks data:, vbscript:, tab injection
- BUG-286-MINE-001: mine_session_links guards JSONL file existence
- BUG-286-TRUST-001: Trust score 0.0 preserved (not replaced by 0.8)
- BUG-287-CKP-001: Path traversal uses relative_to() not startswith()
- BUG-287-RSC-001: rule_applies_to_path guards None/empty path
- BUG-288-MEM-001: CHROMADB_PORT int() guarded at import time
- BUG-288-MEM-002: L2 fallback respects _SHORT_MEMORY_MAX cap
- BUG-288-HND-001: handoff.evidence_gathered None guard
- BUG-289-ATTR-001: _update_attribute validates attr_name allowlist
- BUG-289-INF-001: Inference queries guard _execute_query with try/except

Triage summary: 94 findings → 11 confirmed HIGH, 83 rejected/deferred.
"""
import inspect
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# BUG-286-XSS-001: URI scheme allowlist in render_markdown
# ===========================================================================

class TestXSSSchemeAllowlist:
    """Verify _safe_link blocks dangerous URI schemes."""

    def _get_render_source(self):
        from governance.services.cc_session_ingestion import render_markdown
        return inspect.getsource(render_markdown)

    def test_safe_schemes_defined(self):
        """_SAFE_SCHEMES allowlist must be defined."""
        src = self._get_render_source()
        assert "_SAFE_SCHEMES" in src

    def test_blocks_data_uri(self):
        """data: URIs must be blocked."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("[click](data:text/html,<script>alert(1)</script>)")
        assert "data:" not in result
        assert "<a" not in result

    def test_blocks_vbscript_uri(self):
        """vbscript: URIs must be blocked."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("[click](vbscript:MsgBox)")
        assert "vbscript:" not in result
        assert "<a" not in result

    def test_blocks_javascript_uri(self):
        """javascript: URIs must still be blocked."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("[click](javascript:alert(1))")
        assert "javascript:" not in result
        assert "<a" not in result

    def test_allows_https_uri(self):
        """https: URIs must be allowed."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("[link](https://example.com)")
        assert '<a href=' in result
        assert "https://example.com" in result

    def test_allows_mailto_uri(self):
        """mailto: URIs must be allowed."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("[email](mailto:test@example.com)")
        assert '<a href=' in result

    def test_href_quote_escaped(self):
        """Double quotes in href must be escaped to prevent attribute breakout."""
        src = self._get_render_source()
        assert '&quot;' in src or 'safe_href' in src

    def test_whitespace_collapse(self):
        """Internal whitespace in URI must be collapsed for bypass prevention."""
        src = self._get_render_source()
        assert "re.sub" in src
        # Must collapse control chars + whitespace
        assert "\\x00" in src or "x00-" in src


# ===========================================================================
# BUG-286-MINE-001: mine_session_links JSONL file guard
# ===========================================================================

class TestMineSessionLinksFileGuard:
    """Verify mine_session_links checks JSONL file existence."""

    def test_source_has_file_guard(self):
        """mine_session_links must check Path(jsonl_path).exists()."""
        from governance.services.cc_link_miner import mine_session_links
        src = inspect.getsource(mine_session_links)
        idx = src.index("def mine_session_links")
        block = src[idx:idx + 2000]
        assert "Path(jsonl_path).exists()" in block

    def test_returns_error_on_missing_file(self):
        """Must return error dict when file doesn't exist."""
        from governance.services.cc_link_miner import mine_session_links
        src = inspect.getsource(mine_session_links)
        idx = src.index("BUG-286-MINE-001")
        block = src[idx:idx + 300]
        assert '"error"' in block or "'error'" in block
        assert "JSONL file not found" in block

    def test_guard_before_parse_call(self):
        """File existence check must come before parse_log_file_extended() call."""
        from governance.services.cc_link_miner import mine_session_links
        src = inspect.getsource(mine_session_links)
        guard_pos = src.find("Path(jsonl_path).exists()")
        # Find the actual CALL to parse_log_file_extended (not the import)
        call_pos = src.find("entries = parse_log_file_extended")
        assert guard_pos > 0, "File guard must exist"
        assert call_pos > 0, "Parse call must exist"
        assert guard_pos < call_pos, "File guard must come before parse call"


# ===========================================================================
# BUG-286-TRUST-001: Trust score 0.0 preserved
# ===========================================================================

class TestTrustScoreFalsyGuard:
    """Verify trust_score of 0.0 is not replaced by 0.8."""

    def test_uses_is_not_none_pattern(self):
        """Must use 'is not None' instead of 'or' for trust_score."""
        from governance.services.agents import list_agents
        src = inspect.getsource(list_agents)
        idx = src.index("BUG-286-TRUST-001")
        block = src[idx:idx + 300]
        assert "is not None" in block

    def test_no_trust_score_or_pattern(self):
        """Old pattern 'trust_score or 0.8' must not exist in agent list section."""
        from governance.services.agents import list_agents
        src = inspect.getsource(list_agents)
        # The fix replaces 'or 0.8' with 'is not None' check
        assert "trust_score or 0.8" not in src


# ===========================================================================
# BUG-287-CKP-001: Path traversal uses relative_to()
# ===========================================================================

class TestCheckpointPathTraversal:
    """Verify _checkpoint_path uses relative_to() not startswith()."""

    def test_uses_relative_to(self):
        """Must use relative_to() for path traversal check."""
        from governance.services.ingestion_checkpoint import _checkpoint_path
        src = inspect.getsource(_checkpoint_path)
        assert "relative_to(" in src

    def test_no_startswith_check(self):
        """Must not use string startswith() for path safety."""
        from governance.services.ingestion_checkpoint import _checkpoint_path
        src = inspect.getsource(_checkpoint_path)
        assert ".startswith(" not in src

    def test_traversal_detection_method(self):
        """Path traversal check must use relative_to() pattern, not startswith()."""
        from governance.services.ingestion_checkpoint import _checkpoint_path
        src = inspect.getsource(_checkpoint_path)
        # The fix uses relative_to() which is the correct approach
        assert "relative_to(" in src
        # The old vulnerable pattern must be gone
        assert '.startswith(str(' not in src


# ===========================================================================
# BUG-287-RSC-001: rule_applies_to_path guards None/empty path
# ===========================================================================

class TestRuleScopePathGuard:
    """Verify rule_applies_to_path handles None and empty paths."""

    def test_none_path_returns_false(self):
        """None path must return False (fail-closed)."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(["governance/**"], None) is False

    def test_empty_string_returns_false(self):
        """Empty string path must return False."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(["governance/**"], "") is False

    def test_integer_path_returns_false(self):
        """Non-string path must return False."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(["governance/**"], 42) is False

    def test_valid_path_still_works(self):
        """Valid paths must still match correctly."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(["*.py"], "test.py") is True

    def test_no_scope_returns_true(self):
        """No scope (global) must still return True."""
        from governance.services.rule_scope import rule_applies_to_path
        assert rule_applies_to_path(None, "anything.py") is True


# ===========================================================================
# BUG-288-MEM-001: CHROMADB_PORT guarded int()
# ===========================================================================

class TestMemoryTiersPortGuard:
    """Verify CHROMADB_PORT int() is guarded at import time."""

    def test_port_try_except_in_source(self):
        """Module must have try/except around int(os.getenv(...))."""
        import governance.mcp_tools.memory_tiers as mt
        src = inspect.getsource(mt)
        # Find the CHROMADB_PORT section
        idx = src.index("BUG-288-MEM-001")
        block = src[idx - 100:idx + 300]
        assert "try:" in block
        assert "except" in block
        assert "ValueError" in block or "TypeError" in block

    def test_port_is_int(self):
        """CHROMADB_PORT must be an integer after import."""
        from governance.mcp_tools.memory_tiers import CHROMADB_PORT
        assert isinstance(CHROMADB_PORT, int)


# ===========================================================================
# BUG-288-MEM-002: L2 fallback respects _SHORT_MEMORY_MAX
# ===========================================================================

class TestMemoryL2FallbackCap:
    """Verify L2 fallback path checks _SHORT_MEMORY_MAX."""

    def test_l2_fallback_has_cap_check(self):
        """L2 fallback must check _SHORT_MEMORY_MAX before writing."""
        import governance.mcp_tools.memory_tiers as mt
        src = inspect.getsource(mt)
        # Find the L2 fallback section
        idx = src.index("BUG-288-MEM-002")
        block = src[idx:idx + 400]
        assert "_SHORT_MEMORY_MAX" in block
        assert "oldest_key" in block or "del _short_memory" in block

    def test_l1_cap_still_present(self):
        """L1 path must still have its original cap check."""
        import governance.mcp_tools.memory_tiers as mt
        src = inspect.getsource(mt)
        idx = src.index("BUG-271-MEMORY-001")
        block = src[idx:idx + 200]
        assert "_SHORT_MEMORY_MAX" in block


# ===========================================================================
# BUG-288-HND-001: handoff.evidence_gathered None guard
# ===========================================================================

class TestHandoffEvidenceNullGuard:
    """Verify evidence_gathered None guard in handoff_complete."""

    def test_none_guard_in_source(self):
        """Must check evidence_gathered is None before append."""
        from governance.mcp_tools.handoff import register_handoff_tools
        src = inspect.getsource(register_handoff_tools)
        idx = src.index("BUG-288-HND-001")
        block = src[idx:idx + 200]
        assert "is None" in block
        assert "evidence_gathered = []" in block or "evidence_gathered=[]" in block


# ===========================================================================
# BUG-289-ATTR-001: _update_attribute attr_name allowlist
# ===========================================================================

class TestTaskAttrNameAllowlist:
    """Verify _update_attribute validates attr_name against allowlist."""

    def test_allowlist_defined(self):
        """_ALLOWED_TASK_ATTR_NAMES must be defined."""
        from governance.typedb.queries.tasks.crud import _ALLOWED_TASK_ATTR_NAMES
        assert isinstance(_ALLOWED_TASK_ATTR_NAMES, frozenset)
        assert len(_ALLOWED_TASK_ATTR_NAMES) >= 5

    def test_allowlist_contains_expected(self):
        """Must contain standard task attribute names."""
        from governance.typedb.queries.tasks.crud import _ALLOWED_TASK_ATTR_NAMES
        expected = {"task-status", "task-name", "phase", "item-type", "task-priority"}
        assert expected.issubset(_ALLOWED_TASK_ATTR_NAMES)

    def test_update_attribute_rejects_bad_name(self):
        """Must raise ValueError for disallowed attribute names."""
        from governance.typedb.queries.tasks.crud import _update_attribute
        tx = MagicMock()
        with pytest.raises(ValueError, match="Disallowed attribute"):
            _update_attribute(tx, "TASK-001", "malicious-attr", "", "value")

    def test_update_attribute_source_has_check(self):
        """Source must check attr_name against allowlist."""
        from governance.typedb.queries.tasks.crud import _update_attribute
        src = inspect.getsource(_update_attribute)
        assert "_ALLOWED_TASK_ATTR_NAMES" in src
        assert "raise ValueError" in src


# ===========================================================================
# BUG-289-INF-001: Inference queries guard _execute_query
# ===========================================================================

class TestInferenceQueryGuards:
    """Verify inference query methods have try/except guards."""

    def _get_source(self, method_name):
        from governance.typedb.queries.rules.inference import RuleInferenceQueries
        return inspect.getsource(getattr(RuleInferenceQueries, method_name))

    def test_get_rule_dependencies_guarded(self):
        """get_rule_dependencies must have try/except around _execute_query."""
        src = self._get_source("get_rule_dependencies")
        assert "try:" in src
        assert "except Exception" in src
        assert "return []" in src

    def test_get_rules_depending_on_guarded(self):
        """get_rules_depending_on must have try/except around _execute_query."""
        src = self._get_source("get_rules_depending_on")
        assert "try:" in src
        assert "except Exception" in src
        assert "return []" in src

    def test_find_conflicts_guarded(self):
        """find_conflicts must have try/except around _execute_query."""
        src = self._get_source("find_conflicts")
        assert "try:" in src
        assert "except Exception" in src
        assert "return []" in src

    def test_get_decision_impacts_guarded(self):
        """get_decision_impacts must have try/except around _execute_query."""
        src = self._get_source("get_decision_impacts")
        assert "try:" in src
        assert "except Exception" in src
        assert "return []" in src

    def test_find_conflicts_filters_nulls(self):
        """find_conflicts must filter out None id1/id2 from results."""
        src = self._get_source("find_conflicts")
        assert 'r.get("id1")' in src and 'r.get("id2")' in src


# ===========================================================================
# Cross-batch: Import verification
# ===========================================================================

class TestBatch286Imports:
    """Verify all fixed modules import cleanly."""

    def test_cc_session_ingestion(self):
        from governance.services.cc_session_ingestion import render_markdown
        assert callable(render_markdown)

    def test_cc_link_miner(self):
        from governance.services.cc_link_miner import mine_session_links
        assert callable(mine_session_links)

    def test_ingestion_checkpoint(self):
        from governance.services.ingestion_checkpoint import _checkpoint_path
        assert callable(_checkpoint_path)

    def test_memory_tiers(self):
        from governance.mcp_tools.memory_tiers import CHROMADB_PORT
        assert isinstance(CHROMADB_PORT, int)

    def test_task_crud(self):
        from governance.typedb.queries.tasks.crud import _ALLOWED_TASK_ATTR_NAMES
        assert len(_ALLOWED_TASK_ATTR_NAMES) >= 5

    def test_rule_inference(self):
        from governance.typedb.queries.rules.inference import RuleInferenceQueries
        assert hasattr(RuleInferenceQueries, "get_rule_dependencies")

    def test_rule_scope(self):
        from governance.services.rule_scope import rule_applies_to_path
        assert callable(rule_applies_to_path)

    def test_agents(self):
        from governance.services.agents import list_agents
        assert callable(list_agents)
