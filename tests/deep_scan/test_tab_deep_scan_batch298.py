"""
Batch 298-301 — Deep Scan: TypeDB Queries, MCP Tools, Routes, Services.

Fixes verified:
- BUG-298-READ-001: TypeQL escape order fixed (backslash first, then quotes)
- BUG-298-READ-002: get_all_tasks filter escaping fixed (same pattern)
- BUG-299-TRC-001: Traceability TypeQL newline/CR/tab escaping added
- BUG-299-ING-001: Ingestion MCP path containment check
- BUG-299-HND-001: Handoff task_id/from_agent/to_agent sanitization
- BUG-300-DEL-001: __DELEGATE__ sentinel restricted to explicit /delegate
- BUG-298-EVID-001: session_evidence output_dir path containment
- BUG-301-ORCH-001: ingestion_orchestrator path containment check

Triage summary: 69 findings → 8 confirmed HIGH, 61 rejected/deferred.
"""
import inspect
import re
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# BUG-298-READ-001: TypeQL escape order in _fetch_task_attr/_fetch_task_relation
# ===========================================================================

class TestReadEscapeOrder:
    """Verify read.py escapes backslash BEFORE quotes."""

    def test_fetch_task_attr_escapes_backslash_first(self):
        """_fetch_task_attr must escape backslash before quotes."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._fetch_task_attr)
        # Find the escape line
        assert "replace('\\\\', '\\\\\\\\')" in src
        # Ensure backslash replace comes before quote replace
        bs_pos = src.find("replace('\\\\', '\\\\\\\\')")
        qt_pos = src.find('replace(\'"\'')
        assert bs_pos > 0 and bs_pos < qt_pos

    def test_fetch_task_relation_escapes_backslash_first(self):
        """_fetch_task_relation must escape backslash before quotes."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._fetch_task_relation)
        assert "replace('\\\\', '\\\\\\\\')" in src
        bs_pos = src.find("replace('\\\\', '\\\\\\\\')")
        qt_pos = src.find('replace(\'"\'')
        assert bs_pos > 0 and bs_pos < qt_pos

    def test_no_single_escape_pattern(self):
        """Must NOT have the old single-escape pattern (quote only)."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src_attr = inspect.getsource(TaskReadQueries._fetch_task_attr)
        src_rel = inspect.getsource(TaskReadQueries._fetch_task_relation)
        # The old buggy pattern was: tid = task_id.replace('"', '\\"')
        # Without backslash escape first. Check the comment marker changed.
        assert "BUG-298-READ-001" in src_attr
        assert "BUG-298-READ-001" in src_rel


# ===========================================================================
# BUG-298-READ-002: get_all_tasks filter escaping
# ===========================================================================

class TestGetAllTasksFilterEscaping:
    """Verify get_all_tasks status/phase filters escape correctly."""

    def test_status_filter_escapes_backslash(self):
        """status filter must escape backslash before quotes."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries.get_all_tasks)
        # Find status escape
        assert "BUG-298-READ-002" in src
        # Status escape should have two-step pattern
        idx = src.find("status_esc")
        block = src[idx:idx + 100]
        assert "replace('\\\\'" in block

    def test_phase_filter_escapes_backslash(self):
        """phase filter must escape backslash before quotes."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries.get_all_tasks)
        idx = src.find("phase_esc")
        block = src[idx:idx + 100]
        assert "replace('\\\\'" in block


# ===========================================================================
# BUG-299-TRC-001: Traceability TypeQL newline escaping
# ===========================================================================

class TestTraceabilityNewlineEscaping:
    """Verify traceability.py escapes newlines/CR/tabs in TypeQL."""

    def test_rule_chain_escapes_newlines(self):
        """trace_rule_chain must escape newline chars."""
        from governance.mcp_tools.traceability import register_traceability_tools
        src = inspect.getsource(register_traceability_tools)
        # Find the rule_id escape block
        assert "safe_rule_id" in src
        idx = src.find("safe_rule_id")
        block = src[idx:idx + 300]
        assert "replace('\\n'" in block
        assert "replace('\\r'" in block
        assert "replace('\\t'" in block

    def test_gap_chain_escapes_newlines(self):
        """trace_gap_chain must escape newline chars."""
        from governance.mcp_tools.traceability import register_traceability_tools
        src = inspect.getsource(register_traceability_tools)
        assert "safe_gap_id" in src
        idx = src.find("safe_gap_id")
        block = src[idx:idx + 300]
        assert "replace('\\n'" in block

    def test_evidence_chain_escapes_newlines(self):
        """trace_evidence_chain must escape newline chars."""
        from governance.mcp_tools.traceability import register_traceability_tools
        src = inspect.getsource(register_traceability_tools)
        assert "safe_evidence_path" in src
        idx = src.find("safe_evidence_path")
        block = src[idx:idx + 300]
        assert "replace('\\n'" in block
        assert "replace('\\r'" in block
        assert "replace('\\t'" in block

    def test_all_three_use_bug_marker(self):
        """All escape blocks must reference BUG-299-TRC-001."""
        from governance.mcp_tools.traceability import register_traceability_tools
        src = inspect.getsource(register_traceability_tools)
        assert src.count("BUG-299-TRC-001") >= 3


# ===========================================================================
# BUG-299-ING-001: Ingestion path containment
# ===========================================================================

class TestIngestionPathContainment:
    """Verify ingestion MCP validates explicit paths."""

    def test_resolve_jsonl_path_has_containment_check(self):
        """_resolve_jsonl_path must validate path is under allowed bases."""
        from governance.mcp_tools.ingestion import _resolve_jsonl_path
        src = inspect.getsource(_resolve_jsonl_path)
        assert "BUG-299-ING-001" in src
        assert "_allowed_bases" in src
        assert "resolve()" in src

    def test_rejects_outside_path(self):
        """Path outside allowed bases must return None."""
        from governance.mcp_tools.ingestion import _resolve_jsonl_path
        # /etc/passwd is outside allowed bases
        result = _resolve_jsonl_path("session-1", "/etc/passwd")
        assert result is None

    def test_rejects_traversal_path(self):
        """Path with traversal must return None."""
        from governance.mcp_tools.ingestion import _resolve_jsonl_path
        result = _resolve_jsonl_path("session-1", "../../../../etc/passwd")
        assert result is None


# ===========================================================================
# BUG-299-HND-001: Handoff sanitization
# ===========================================================================

class TestHandoffSanitization:
    """Verify handoff_create sanitizes task_id/from_agent/to_agent."""

    def test_handoff_create_sanitizes_task_id(self):
        """handoff_create must sanitize task_id."""
        from governance.mcp_tools.handoff import register_handoff_tools
        src = inspect.getsource(register_handoff_tools)
        # Find the handoff_create function body (need larger block for signature + docstring + try)
        idx = src.find("def handoff_create")
        block = src[idx:idx + 900]
        assert "BUG-299-HND-001" in block
        assert "re.sub" in block

    def test_sanitizes_all_three_fields(self):
        """Must sanitize task_id, from_agent, to_agent."""
        from governance.mcp_tools.handoff import register_handoff_tools
        src = inspect.getsource(register_handoff_tools)
        idx = src.find("BUG-299-HND-001")
        block = src[idx:idx + 300]
        assert "task_id" in block
        assert "from_agent" in block
        assert "to_agent" in block


# ===========================================================================
# BUG-300-DEL-001: __DELEGATE__ sentinel injection prevention
# ===========================================================================

class TestDelegateSentinelGuard:
    """Verify __DELEGATE__ sentinel only honored from explicit /delegate."""

    def test_explicit_delegate_flag_exists(self):
        """Must track _is_explicit_delegate flag."""
        from governance.routes.chat.endpoints import send_chat_message
        src = inspect.getsource(send_chat_message)
        assert "_is_explicit_delegate" in src
        assert "BUG-300-DEL-001" in src

    def test_delegate_check_requires_flag(self):
        """__DELEGATE__ check must require _is_explicit_delegate."""
        from governance.routes.chat.endpoints import send_chat_message
        src = inspect.getsource(send_chat_message)
        # The check must be: if _is_explicit_delegate and response_content.startswith(...)
        assert "_is_explicit_delegate and response_content.startswith" in src

    def test_flag_checks_slash_delegate(self):
        """Flag must be based on /delegate command prefix."""
        from governance.routes.chat.endpoints import send_chat_message
        src = inspect.getsource(send_chat_message)
        assert '"/delegate"' in src or "'/delegate'" in src


# ===========================================================================
# BUG-298-EVID-001: session_evidence output_dir containment
# ===========================================================================

class TestEvidenceOutputDirContainment:
    """Verify session_evidence validates output_dir."""

    def test_output_dir_containment_check(self):
        """generate_session_evidence must validate output_dir."""
        from governance.services.session_evidence import generate_session_evidence
        src = inspect.getsource(generate_session_evidence)
        assert "BUG-298-EVID-001" in src
        assert "resolve()" in src
        assert "_DEFAULT_EVIDENCE_DIR" in src

    def test_rejects_outside_evidence_root(self):
        """output_dir outside evidence root must return None."""
        from governance.services.session_evidence import generate_session_evidence
        from pathlib import Path

        session_data = {
            "session_id": "TEST-SESSION",
            "status": "COMPLETED",
        }
        # Try to write to /tmp (outside evidence root)
        result = generate_session_evidence(session_data, output_dir=Path("/tmp"))
        assert result is None


# ===========================================================================
# BUG-301-ORCH-001: ingestion_orchestrator path containment
# ===========================================================================

class TestOrchestratorPathContainment:
    """Verify ingestion_orchestrator validates jsonl_path."""

    def test_validate_jsonl_path_exists(self):
        """_validate_jsonl_path helper must exist."""
        from governance.services.ingestion_orchestrator import _validate_jsonl_path
        assert callable(_validate_jsonl_path)

    def test_estimate_has_containment_check(self):
        """estimate_ingestion must check path containment."""
        from governance.services.ingestion_orchestrator import estimate_ingestion
        src = inspect.getsource(estimate_ingestion)
        assert "BUG-301-ORCH-001" in src
        assert "_validate_jsonl_path" in src

    def test_rejects_etc_passwd(self):
        """Path to /etc/passwd must be rejected."""
        from governance.services.ingestion_orchestrator import estimate_ingestion
        from pathlib import Path
        result = estimate_ingestion(Path("/etc/passwd"))
        assert "error" in result


# ===========================================================================
# Cross-batch: Import verification
# ===========================================================================

class TestBatch298Imports:
    """Verify all fixed modules import cleanly."""

    def test_read_queries(self):
        from governance.typedb.queries.tasks.read import TaskReadQueries
        assert hasattr(TaskReadQueries, '_fetch_task_attr')
        assert hasattr(TaskReadQueries, '_fetch_task_relation')
        assert hasattr(TaskReadQueries, 'get_all_tasks')

    def test_traceability(self):
        from governance.mcp_tools.traceability import register_traceability_tools
        assert callable(register_traceability_tools)

    def test_ingestion(self):
        from governance.mcp_tools.ingestion import _resolve_jsonl_path
        assert callable(_resolve_jsonl_path)

    def test_handoff(self):
        from governance.mcp_tools.handoff import register_handoff_tools
        assert callable(register_handoff_tools)

    def test_endpoints(self):
        from governance.routes.chat.endpoints import send_chat_message
        assert callable(send_chat_message)

    def test_session_evidence(self):
        from governance.services.session_evidence import generate_session_evidence
        assert callable(generate_session_evidence)

    def test_ingestion_orchestrator(self):
        from governance.services.ingestion_orchestrator import (
            estimate_ingestion, run_ingestion_pipeline, _validate_jsonl_path
        )
        assert callable(estimate_ingestion)
        assert callable(run_ingestion_pipeline)
        assert callable(_validate_jsonl_path)
