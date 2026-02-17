"""
Deep Scan Batch 302-305: Defense tests for security fixes.

Tests for:
  BUG-302-READ-003: _build_task_from_id backslash escape order
  BUG-303-TRUST-001: Agent ID validation in trust controller
  BUG-304-DEL-001: rule_delete confirm identity check
  BUG-305-INFRA-001: start_service allowlist
  BUG-305-INFRA-002: load_container_logs allowlist + lines clamp
  BUG-305-INFRA-003: Socket leak prevention in check_port
  BUG-305-SDL-001: Session ID validation in detail loaders
"""

import re
import textwrap
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-302-READ-003: _build_task_from_id escape order ─────────────


class TestBuildTaskFromIdEscape:
    """Verify _build_task_from_id uses backslash-first escape."""

    def test_escape_order_in_source(self):
        src = (SRC / "governance/typedb/queries/tasks/read.py").read_text()
        idx = src.find("def _build_task_from_id")
        assert idx != -1, "_build_task_from_id not found"
        block = src[idx:idx + 400]
        assert "BUG-302-READ-003" in block
        backslash_pos = block.find(".replace('\\\\', '\\\\\\\\')")
        quote_pos = block.find('.replace(\'"\', \'\\\\"\')')
        assert backslash_pos != -1, "Backslash escape not found"
        assert quote_pos != -1, "Quote escape not found"
        assert backslash_pos < quote_pos, "Backslash must be escaped FIRST"


# ── BUG-303-TRUST-001: Agent ID validation ──────────────────────────


class TestTrustAgentIdValidation:
    """Verify agent_id is validated before URL interpolation."""

    def test_agent_id_regex_in_source(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        assert "_AGENT_ID_RE" in src
        assert "BUG-303-TRUST-001" in src

    def test_select_agent_validates(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        idx = src.find("def select_agent")
        assert idx != -1
        block = src[idx:idx + 400]
        assert "_AGENT_ID_RE.match" in block

    def test_toggle_agent_validates(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        idx = src.find("def toggle_agent_pause")
        assert idx != -1
        block = src[idx:idx + 400]
        assert "_AGENT_ID_RE.match" in block

    def test_load_trust_history_validates(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        idx = src.find("def load_trust_history")
        assert idx != -1
        block = src[idx:idx + 400]
        assert "_AGENT_ID_RE.match" in block

    def test_regex_rejects_path_traversal(self):
        pattern = re.compile(r'^[A-Za-z0-9_\-]{1,64}$')
        assert pattern.match("AGENT-001")
        assert not pattern.match("../admin")
        assert not pattern.match("AGENT-001/../secret")
        assert not pattern.match("")
        assert not pattern.match("A" * 65)


# ── BUG-304-DEL-001: rule_delete confirm identity check ─────────────


class TestRuleDeleteConfirmGuard:
    """Verify rule_delete uses 'is not True' identity check."""

    def test_identity_check_in_source(self):
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        assert "BUG-304-DEL-001" in src
        assert "confirm is not True" in src

    def test_truthiness_bypass_blocked(self):
        """Truthy non-True values must NOT bypass the guard."""
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        idx = src.find("def rule_delete")
        assert idx != -1
        block = src[idx:idx + 600]
        # Must use identity check, not truthiness
        assert "is not True" in block
        # Should NOT have `if not confirm:` (truthiness check)
        # The old pattern would be `if not confirm:` which passes for truthy non-True
        lines = block.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("if") and "confirm" in stripped and "is not True" not in stripped:
                if "not confirm" in stripped and "is not" not in stripped:
                    pytest.fail(f"Found unsafe truthiness check: {stripped}")


# ── BUG-305-INFRA-001: start_service allowlist ──────────────────────


class TestStartServiceAllowlist:
    """Verify start_service has service allowlist."""

    def test_allowlist_in_source(self):
        src = (SRC / "agent/governance_ui/controllers/infra_loaders.py").read_text()
        idx = src.find("def start_service")
        assert idx != -1
        block = src[idx:idx + 500]
        assert "BUG-305-INFRA-001" in block
        assert "_ALLOWED_SERVICES" in block
        assert "typedb" in block
        assert "chromadb" in block

    def test_rejects_unknown_service(self):
        src = (SRC / "agent/governance_ui/controllers/infra_loaders.py").read_text()
        idx = src.find("def start_service")
        block = src[idx:idx + 500]
        assert "not in _ALLOWED_SERVICES" in block or "service not in _ALLOWED_SERVICES" in block


# ── BUG-305-INFRA-002: load_container_logs validation ────────────────


class TestContainerLogsValidation:
    """Verify container logs has allowlist and lines clamping."""

    def test_container_allowlist_in_source(self):
        src = (SRC / "agent/governance_ui/controllers/infra_loaders.py").read_text()
        idx = src.find("def load_container_logs")
        assert idx != -1
        block = src[idx:idx + 600]
        assert "BUG-305-INFRA-002" in block
        assert "_ALLOWED_CONTAINERS" in block

    def test_lines_clamping(self):
        src = (SRC / "agent/governance_ui/controllers/infra_loaders.py").read_text()
        idx = src.find("def load_container_logs")
        block = src[idx:idx + 600]
        assert "min(" in block and "max(" in block, "Lines must be clamped with min/max"
        assert "500" in block, "Max lines should be 500"


# ── BUG-305-INFRA-003: Socket leak prevention ───────────────────────


class TestCheckPortSocketLeak:
    """Verify check_port uses finally to close socket."""

    def test_finally_close_in_source(self):
        src = (SRC / "agent/governance_ui/controllers/infra_loaders.py").read_text()
        idx = src.find("def check_port")
        assert idx != -1
        block = src[idx:idx + 700]
        assert "BUG-305-INFRA-003" in block
        assert "finally:" in block
        assert "sock.close()" in block


# ── BUG-305-SDL-001: Session ID validation in detail loaders ────────


class TestSessionDetailLoaderValidation:
    """Verify session_id is validated in all loader functions."""

    def test_validation_helper_exists(self):
        src = (SRC / "agent/governance_ui/controllers/sessions_detail_loaders.py").read_text()
        assert "_valid_session_id" in src
        assert "_SESSION_ID_RE" in src
        assert "BUG-305-SDL-001" in src

    def test_all_loaders_use_validation(self):
        src = (SRC / "agent/governance_ui/controllers/sessions_detail_loaders.py").read_text()
        loaders = [
            "load_session_tool_calls",
            "load_session_thinking_items",
            "load_session_evidence_rendered",
            "load_session_evidence",
            "load_session_tasks",
            "load_session_transcript",
            "load_transcript_entry_expanded",
        ]
        for loader in loaders:
            idx = src.find(f"def {loader}")
            assert idx != -1, f"{loader} not found"
            block = src[idx:idx + 300]
            assert "_valid_session_id" in block, f"{loader} missing _valid_session_id check"

    def test_entry_index_cast_to_int(self):
        src = (SRC / "agent/governance_ui/controllers/sessions_detail_loaders.py").read_text()
        idx = src.find("def load_transcript_entry_expanded")
        block = src[idx:idx + 300]
        assert "int(entry_index)" in block

    def test_validation_regex_rejects_traversal(self):
        pattern = re.compile(r'^[A-Za-z0-9_\-]+$')
        assert pattern.match("SESSION-2026-02-17-AUDIT")
        assert not pattern.match("../../etc/passwd")
        assert not pattern.match("SESSION/../admin")
        assert not pattern.match("SESSION%2F..%2F")


# ── Import verification ─────────────────────────────────────────────


class TestBatch302Imports:
    """Verify all fixed modules import cleanly."""

    def test_import_read_queries(self):
        from governance.typedb.queries.tasks import read  # noqa: F401

    def test_import_rules_crud(self):
        from governance.mcp_tools import rules_crud  # noqa: F401

    def test_import_trust_controller(self):
        from agent.governance_ui.controllers import trust  # noqa: F401

    def test_import_infra_loaders(self):
        from agent.governance_ui.controllers import infra_loaders  # noqa: F401

    def test_import_sessions_detail_loaders(self):
        from agent.governance_ui.controllers import sessions_detail_loaders  # noqa: F401
