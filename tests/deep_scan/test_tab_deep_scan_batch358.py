"""
Defense tests for deep scan batches 358-361.

Covers:
- BUG-358-EVT-001: evidence_transcript.py path traversal (is_relative_to vs startswith)
- BUG-358-EVT-002: evidence_transcript.py unbounded per_page cap
- BUG-361-TRC-001: traceability.py 5× str(e) error sanitization
- BUG-361-TRU-001: trust.py str(e) error sanitization
- BUG-361-TRU-002: trust.py newline/CR/tab escape in TypeQL
- BUG-361-HND-001: handoff.py 5× str(e) error sanitization
- BUG-361-MEM-001: memory_tiers.py L3 str(e) error sanitization
- BUG-361-MEM-002: memory_tiers.py content size cap
- BUG-360-STS-001: tasks/status.py silent exception → logger.debug
- BUG-360-RCR-001: rules/crud.py update_rule validation
- BUG-359-LNK-001: cc_link_miner.py error list cap

Created: 2026-02-18 (batch 358-361)
"""
import importlib
import inspect
import re
import textwrap

import pytest


# =============================================================================
# BUG-358-EVT-001: evidence_transcript.py uses is_relative_to (not startswith)
# =============================================================================
class TestEvidenceTranscriptPathTraversal:
    """Verify path containment uses is_relative_to instead of startswith."""

    def test_uses_is_relative_to(self):
        src = inspect.getsource(
            importlib.import_module("governance.services.evidence_transcript")
        )
        assert "is_relative_to" in src, "Must use is_relative_to for path containment"

    def test_no_startswith_for_path_check(self):
        """Ensure startswith() is NOT used for path containment (prefix-bypass vulnerable)."""
        src = inspect.getsource(
            importlib.import_module("governance.services.evidence_transcript")
        )
        # The old pattern was: str(candidate).startswith(str(_EVIDENCE_DIR.resolve()))
        # After fix, this line should be replaced with is_relative_to
        assert "startswith(str(_EVIDENCE_DIR" not in src, \
            "startswith() for path containment is vulnerable to prefix-sibling bypass"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.services.evidence_transcript")
        )
        assert "BUG-358-EVT-001" in src


# =============================================================================
# BUG-358-EVT-002: evidence_transcript.py per_page cap
# =============================================================================
class TestEvidenceTranscriptPerPageCap:
    """Verify per_page is capped to prevent unbounded memory."""

    def test_per_page_cap_code_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.services.evidence_transcript")
        )
        assert "BUG-358-EVT-002" in src
        # Should cap per_page with min()
        assert "min(per_page" in src or "min( per_page" in src, \
            "per_page must be capped with min()"

    def test_per_page_cap_value(self):
        """The cap should be reasonable (<=200)."""
        src = inspect.getsource(
            importlib.import_module("governance.services.evidence_transcript")
        )
        # Find the min(per_page, N) pattern
        match = re.search(r"min\(per_page,\s*(\d+)\)", src)
        assert match, "Expected min(per_page, N) pattern"
        cap_value = int(match.group(1))
        assert cap_value <= 200, f"per_page cap {cap_value} too high (max 200)"


# =============================================================================
# BUG-361-TRC-001: traceability.py error sanitization
# =============================================================================
class TestTraceabilityErrorSanitization:
    """Verify all 5 error handlers in traceability.py use type(e).__name__."""

    def test_no_raw_str_e_in_mcp_returns(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.traceability")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_all_five_handlers_use_logger(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.traceability")
        )
        # 5 trace functions: trace_task_chain, trace_session_chain, trace_rule_chain,
        # trace_gap_chain, trace_evidence_chain
        logger_error_count = src.count("logger.error(")
        assert logger_error_count >= 5, \
            f"Expected 5+ logger.error calls, found {logger_error_count}"

    def test_exc_info_true(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.traceability")
        )
        exc_info_count = src.count("exc_info=True")
        assert exc_info_count >= 5, \
            f"Expected 5+ exc_info=True, found {exc_info_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.traceability")
        )
        assert "BUG-361-TRC-001" in src


# =============================================================================
# BUG-361-TRU-001 + BUG-361-TRU-002: trust.py error + escape
# =============================================================================
class TestTrustErrorAndEscape:
    """Verify trust.py error sanitization and TypeQL escape completeness."""

    def test_no_raw_str_e_in_mcp_return(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.trust")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_has_logger(self):
        mod = importlib.import_module("governance.mcp_tools.trust")
        assert hasattr(mod, "logger"), "trust.py must have a logger"

    def test_newline_escape_in_agent_id(self):
        """BUG-361-TRU-002: Must escape \\n, \\r, \\t in agent_id for TypeQL."""
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.trust")
        )
        assert r".replace('\n'" in src, "Must escape newlines in agent_id"
        assert r".replace('\r'" in src, "Must escape carriage returns in agent_id"
        assert r".replace('\t'" in src, "Must escape tabs in agent_id"

    def test_bug_markers_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.trust")
        )
        assert "BUG-361-TRU-001" in src
        assert "BUG-361-TRU-002" in src


# =============================================================================
# BUG-361-HND-001: handoff.py error sanitization
# =============================================================================
class TestHandoffErrorSanitization:
    """Verify all 5 error handlers in handoff.py use type(e).__name__."""

    def test_no_raw_str_e_in_mcp_returns(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.handoff")
        )
        mcp_error_lines = [
            l.strip() for l in src.split("\n")
            if "format_mcp_result" in l and "failed:" in l
        ]
        assert len(mcp_error_lines) >= 5, \
            f"Expected 5+ MCP error return lines, found {len(mcp_error_lines)}"
        for line in mcp_error_lines:
            assert "type(e).__name__" in line, \
                f"MCP error return uses raw str(e): {line}"

    def test_has_logger(self):
        mod = importlib.import_module("governance.mcp_tools.handoff")
        assert hasattr(mod, "logger"), "handoff.py must have a logger"

    def test_logger_error_calls(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.handoff")
        )
        logger_error_count = src.count("logger.error(")
        assert logger_error_count >= 5, \
            f"Expected 5+ logger.error calls, found {logger_error_count}"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.handoff")
        )
        assert "BUG-361-HND-001" in src


# =============================================================================
# BUG-361-MEM-001 + BUG-361-MEM-002: memory_tiers.py fixes
# =============================================================================
class TestMemoryTiersFixes:
    """Verify memory_tiers.py error sanitization and content cap."""

    def test_l3_error_no_raw_str_e(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.memory_tiers")
        )
        # Find lines with "error" key in format_mcp_result for L3 path
        # The old pattern was: "error": str(e)
        assert '"error": str(e)' not in src, \
            "L3 error path must not use raw str(e)"

    def test_content_size_cap(self):
        """BUG-361-MEM-002: Content must be capped before storage."""
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.memory_tiers")
        )
        assert "_MAX_CONTENT_SIZE" in src, "Must define _MAX_CONTENT_SIZE"
        assert "BUG-361-MEM-002" in src

    def test_content_cap_value_reasonable(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.memory_tiers")
        )
        match = re.search(r"_MAX_CONTENT_SIZE\s*=\s*(\d[\d_]*)", src)
        assert match, "Expected _MAX_CONTENT_SIZE = N"
        cap = int(match.group(1).replace("_", ""))
        assert 10_000 <= cap <= 1_000_000, f"Content cap {cap} outside reasonable range"

    def test_bug_markers_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.mcp_tools.memory_tiers")
        )
        assert "BUG-361-MEM-001" in src
        assert "BUG-361-MEM-002" in src


# =============================================================================
# BUG-360-STS-001: tasks/status.py silent exception logging
# =============================================================================
class TestTaskStatusSilentException:
    """Verify silent exception suppression is replaced with logging."""

    def test_no_bare_except_pass(self):
        """The old pattern was: except Exception: pass"""
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.status")
        )
        # Check there's no bare "except Exception:\n            pass" pattern
        # There should be logger.debug instead
        bare_pass_count = len(re.findall(
            r"except\s+Exception\s*:\s*\n\s*pass", src
        ))
        assert bare_pass_count == 0, \
            f"Found {bare_pass_count} bare except Exception: pass — should use logger.debug"

    def test_has_logger_debug_for_resolution(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.status")
        )
        # Should now have logger.debug for resolution deletes
        assert "logger.debug" in src, "Resolution delete should use logger.debug"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.tasks.status")
        )
        assert "BUG-360-STS-001" in src


# =============================================================================
# BUG-360-RCR-001: rules/crud.py update_rule validation
# =============================================================================
class TestRulesCrudUpdateValidation:
    """Verify update_rule validates category/priority/status/rule_type."""

    def test_update_rule_has_validation(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.rules.crud")
        )
        # Check that update_rule now validates inputs
        assert "BUG-360-RCR-001" in src

    def test_update_rule_validates_category(self):
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.rules.crud")
        )
        # The update_rule function should contain validation for category
        # Extract the update_rule method source
        update_start = src.find("def update_rule(")
        assert update_start > 0, "update_rule method must exist"
        # Check for category validation in the update_rule scope
        update_section = src[update_start:update_start + 2000]
        assert "valid_categories" in update_section, \
            "update_rule must validate category against allowlist"
        assert "valid_priorities" in update_section, \
            "update_rule must validate priority against allowlist"
        assert "valid_statuses" in update_section, \
            "update_rule must validate status against allowlist"

    def test_create_and_update_share_allowlists(self):
        """Ensure create_rule and update_rule use the same categories."""
        src = inspect.getsource(
            importlib.import_module("governance.typedb.queries.rules.crud")
        )
        # Both should include "governance" in their valid_categories
        create_section = src[src.find("def create_rule("):src.find("def update_rule(")]
        update_section = src[src.find("def update_rule("):src.find("def deprecate_rule(")]
        # Both should have the standard categories
        for cat in ["governance", "technical", "operational"]:
            assert cat in create_section, f"create_rule missing category: {cat}"
            assert cat in update_section, f"update_rule missing category: {cat}"


# =============================================================================
# BUG-359-LNK-001: cc_link_miner.py error list cap
# =============================================================================
class TestLinkMinerErrorCap:
    """Verify error list is capped to prevent unbounded growth."""

    def test_error_cap_constant_defined(self):
        src = inspect.getsource(
            importlib.import_module("governance.services.cc_link_miner")
        )
        assert "_MAX_ERRORS" in src, "Must define _MAX_ERRORS constant"

    def test_error_cap_guard_in_loop_append_paths(self):
        """Error appends inside linking loops should check the cap."""
        src = inspect.getsource(
            importlib.import_module("governance.services.cc_link_miner")
        )
        # Count error append calls in except blocks (loop-based linking)
        # These are the ones that need capping — not one-shot static appends
        lines = src.split("\n")
        loop_append_count = 0
        capped_count = 0
        for i, line in enumerate(lines):
            if 'result["errors"].append(' in line and "link" in line.lower():
                loop_append_count += 1
                prev_lines = "\n".join(lines[max(0, i-3):i+1])
                if "_MAX_ERRORS" in prev_lines:
                    capped_count += 1
        assert loop_append_count >= 4, \
            f"Expected 4+ loop error append lines, found {loop_append_count}"
        assert capped_count == loop_append_count, \
            f"Only {capped_count}/{loop_append_count} loop appends are capped"

    def test_error_cap_reasonable_value(self):
        src = inspect.getsource(
            importlib.import_module("governance.services.cc_link_miner")
        )
        match = re.search(r"_MAX_ERRORS\s*=\s*(\d+)", src)
        assert match, "Expected _MAX_ERRORS = N"
        cap = int(match.group(1))
        assert 10 <= cap <= 500, f"Error cap {cap} outside reasonable range"

    def test_bug_marker_present(self):
        src = inspect.getsource(
            importlib.import_module("governance.services.cc_link_miner")
        )
        assert "BUG-359-LNK-001" in src


# =============================================================================
# Import sanity checks
# =============================================================================
class TestBatch358Imports:
    """Verify all modified modules import cleanly."""

    def test_import_evidence_transcript(self):
        importlib.import_module("governance.services.evidence_transcript")

    def test_import_traceability(self):
        importlib.import_module("governance.mcp_tools.traceability")

    def test_import_trust(self):
        importlib.import_module("governance.mcp_tools.trust")

    def test_import_handoff(self):
        importlib.import_module("governance.mcp_tools.handoff")

    def test_import_memory_tiers(self):
        importlib.import_module("governance.mcp_tools.memory_tiers")

    def test_import_tasks_status(self):
        importlib.import_module("governance.typedb.queries.tasks.status")

    def test_import_rules_crud(self):
        importlib.import_module("governance.typedb.queries.rules.crud")

    def test_import_cc_link_miner(self):
        importlib.import_module("governance.services.cc_link_miner")
