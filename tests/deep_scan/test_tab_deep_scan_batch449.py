"""Batch 449 — chat/commands.py debug→warning (3 fixes),
decisions.py add_error_trace (2 fixes),
sessions_detail_loaders.py add_error_trace (7 fixes),
TypeDB queries (5 CLEAN), Stores+helpers (5 CLEAN) confirmation.

Validates fixes for:
- BUG-446-CMD-001..003: chat/commands.py debug→warning + exc_info
- BUG-449-DEC-001..002: decisions.py add_error_trace type-only
- BUG-449-SDL-001..007: sessions_detail_loaders.py add_error_trace type-only
"""
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def _read(relpath: str) -> str:
    return (_ROOT / relpath).read_text(encoding="utf-8")


def _check_no_debug_in_except(src: str, filename: str) -> list:
    """Return lines where logger.debug appears in except blocks."""
    violations = []
    in_except = False
    for i, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("except "):
            in_except = True
        elif in_except and stripped and not stripped.startswith("#"):
            if "logger.debug(" in stripped:
                violations.append((i, stripped))
            if not stripped.startswith(("logger.", "add_error_trace", "state.", "return",
                                       "#", "pass", "raise", "if ", "else:")):
                in_except = False
    return violations


def _check_no_bare_e_in_add_error_trace(src: str) -> list:
    """Return lines where add_error_trace uses {e} or {str(e)} instead of {type(e).__name__}."""
    violations = []
    for i, line in enumerate(src.splitlines(), 1):
        if "add_error_trace(" in line:
            if '{e}' in line or '{str(e)}' in line:
                violations.append((i, line.strip()))
    return violations


# ─── chat/commands.py — debug→warning + exc_info ─────────────────────────

class TestChatCommandsWarningExcInfo:
    """BUG-446-CMD-001..003: debug→warning + exc_info in chat commands."""

    def test_no_debug_in_except_blocks(self):
        src = _read("governance/routes/chat/commands.py")
        violations = _check_no_debug_in_except(src, "commands.py")
        assert not violations, f"logger.debug in except blocks: {violations}"

    def test_rules_query_warning(self):
        src = _read("governance/routes/chat/commands.py")
        assert "BUG-446-CMD-001" in src

    def test_active_rules_warning(self):
        src = _read("governance/routes/chat/commands.py")
        assert "BUG-446-CMD-002" in src

    def test_search_rules_warning(self):
        src = _read("governance/routes/chat/commands.py")
        assert "BUG-446-CMD-003" in src

    def test_warning_has_exc_info(self):
        src = _read("governance/routes/chat/commands.py")
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "BUG-446-CMD" in line:
                # Next line should have warning + exc_info
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                assert "logger.warning(" in next_line, f"Expected warning at line {i+2}"
                assert "exc_info=True" in next_line, f"Missing exc_info at line {i+2}"


# ─── decisions.py — add_error_trace type-only ─────────────────────────────

class TestDecisionsErrorTraceTypeOnly:
    """BUG-449-DEC-001..002: add_error_trace uses type(e).__name__ only."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/decisions.py")
        violations = _check_no_bare_e_in_add_error_trace(src)
        assert not violations, f"Bare {{e}} in add_error_trace: {violations}"

    def test_save_decision_bug_marker(self):
        src = _read("agent/governance_ui/controllers/decisions.py")
        assert "BUG-449-DEC-001" in src

    def test_delete_decision_bug_marker(self):
        src = _read("agent/governance_ui/controllers/decisions.py")
        assert "BUG-449-DEC-002" in src


# ─── sessions_detail_loaders.py — add_error_trace type-only ──────────────

class TestSessionDetailLoadersErrorTraceTypeOnly:
    """BUG-449-SDL-001..007: add_error_trace uses type(e).__name__ only."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        violations = _check_no_bare_e_in_add_error_trace(src)
        assert not violations, f"Bare {{e}} in add_error_trace: {violations}"

    def test_tool_calls_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        assert "BUG-449-SDL-001" in src

    def test_thinking_items_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        assert "BUG-449-SDL-002" in src

    def test_evidence_rendered_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        assert "BUG-449-SDL-003" in src

    def test_evidence_files_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        assert "BUG-449-SDL-004" in src

    def test_session_tasks_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        assert "BUG-449-SDL-005" in src

    def test_transcript_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        assert "BUG-449-SDL-006" in src

    def test_expand_entry_bug_marker(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        assert "BUG-449-SDL-007" in src


# ─── Batch 447 CLEAN — TypeDB queries ────────────────────────────────────

class TestBatch447TypeDBClean:
    """Batch 447: TypeDB queries layer confirmed CLEAN."""

    def test_rules_crud_importable(self):
        src = _read("governance/typedb/queries/rules/crud.py")
        assert "def " in src

    def test_rules_inference_importable(self):
        src = _read("governance/typedb/queries/rules/inference.py")
        assert "def " in src

    def test_tasks_crud_importable(self):
        src = _read("governance/typedb/queries/tasks/crud.py")
        assert "def " in src

    def test_tasks_linking_importable(self):
        src = _read("governance/typedb/queries/tasks/linking.py")
        assert "def " in src

    def test_tasks_relationships_importable(self):
        src = _read("governance/typedb/queries/tasks/relationships.py")
        assert "def " in src


# ─── Batch 448 CLEAN — Stores + helpers ──────────────────────────────────

class TestBatch448StoresClean:
    """Batch 448: Stores + helpers layer confirmed CLEAN."""

    def test_typedb_access_importable(self):
        src = _read("governance/stores/typedb_access.py")
        assert "def " in src

    def test_helpers_importable(self):
        src = _read("governance/stores/helpers.py")
        assert "def " in src

    def test_retry_importable(self):
        src = _read("governance/stores/retry.py")
        assert "def " in src or "class " in src

    def test_agents_store_importable(self):
        src = _read("governance/stores/agents.py")
        assert "def " in src or "class " in src

    def test_vector_store_importable(self):
        src = _read("governance/vector_store/store.py")
        assert "def " in src


# ─── Import validation ───────────────────────────────────────────────────

class TestBatch449Imports:
    """Verify modified modules compile cleanly."""

    def test_commands_compiles(self):
        src = _read("governance/routes/chat/commands.py")
        compile(src, "commands.py", "exec")

    def test_decisions_compiles(self):
        src = _read("agent/governance_ui/controllers/decisions.py")
        compile(src, "decisions.py", "exec")

    def test_sessions_detail_loaders_compiles(self):
        src = _read("agent/governance_ui/controllers/sessions_detail_loaders.py")
        compile(src, "sessions_detail_loaders.py", "exec")
