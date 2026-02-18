"""Batch 405 — Task route protection, chat info disclosure, session exc_info,
mutation exc_info tests.

Validates fixes for:
- BUG-402-SVC-001..006: tasks/crud.py linking handler try/except wrappers
- BUG-405-CMD-001: chat/commands.py str(e) → type(e).__name__ in /context
- BUG-403-CRD-001: sessions/crud.py exc_info additions
- BUG-403-CRD-002: sessions/crud.py get_session catch-all handler
- BUG-404-TM-006: tasks_mutations.py exc_info additions
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-402-SVC-001..006: tasks/crud.py linking handler protection ────

class TestTasksCrudLinkingProtection:
    """All linking route handlers must have try/except with HTTPException re-raise."""

    def _get_handler_block(self, src, handler_name):
        idx = src.index(f"def {handler_name}")
        next_def = src.find("\ndef ", idx + 10)
        return src[idx:next_def] if next_def != -1 else src[idx:]

    def test_link_task_to_rule_protected(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        block = self._get_handler_block(src, "link_task_to_rule")
        assert "try:" in block
        assert "except HTTPException:" in block
        assert "except Exception" in block
        assert "BUG-402-SVC-001" in block

    def test_link_task_to_session_protected(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        block = self._get_handler_block(src, "link_task_to_session")
        assert "try:" in block
        assert "except HTTPException:" in block
        assert "except Exception" in block
        assert "BUG-402-SVC-002" in block

    def test_get_task_sessions_protected(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        block = self._get_handler_block(src, "get_task_sessions")
        assert "try:" in block
        assert "except HTTPException:" in block
        assert "except Exception" in block
        assert "BUG-402-SVC-003" in block

    def test_link_task_to_document_protected(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        block = self._get_handler_block(src, "link_task_to_document")
        assert "try:" in block
        assert "except HTTPException:" in block
        assert "except Exception" in block
        assert "BUG-402-SVC-004" in block

    def test_get_task_documents_protected(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        block = self._get_handler_block(src, "get_task_documents")
        assert "try:" in block
        assert "except HTTPException:" in block
        assert "except Exception" in block
        assert "BUG-402-SVC-005" in block

    def test_unlink_task_document_protected(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        block = self._get_handler_block(src, "unlink_task_document")
        assert "try:" in block
        assert "except HTTPException:" in block
        assert "except Exception" in block
        assert "BUG-402-SVC-006" in block

    def test_all_error_responses_use_type_name(self):
        """Error detail strings should use type(e).__name__, not str(e)."""
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        assert "detail=str(e)" not in src

    def test_all_linking_handlers_log_with_exc_info(self):
        """All linking except blocks should log with exc_info=True."""
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        for handler in ["link_task_to_rule", "link_task_to_session",
                        "get_task_sessions", "link_task_to_document",
                        "get_task_documents", "unlink_task_document"]:
            block = self._get_handler_block(src, handler)
            assert "exc_info=True" in block, f"{handler} missing exc_info=True"

    def test_bug_markers_present(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        for i in range(1, 7):
            assert f"BUG-402-SVC-00{i}" in src, f"Missing BUG-402-SVC-00{i}"


# ── BUG-405-CMD-001: chat/commands.py str(e) sanitization ─────────────

class TestChatCommandsInfoDisclosure:
    """Chat command /context must not leak exception details via str(e)."""

    def test_context_command_no_str_e(self):
        src = (SRC / "governance/routes/chat/commands.py").read_text()
        # Find /context handler block
        idx = src.index('content_lower.startswith("/context")')
        # Find next elif or else
        next_elif = src.find("elif content_lower", idx + 10)
        block = src[idx:next_elif] if next_elif != -1 else src[idx:]
        assert "str(e)" not in block, "/context handler still uses str(e)"

    def test_context_command_uses_type_name(self):
        src = (SRC / "governance/routes/chat/commands.py").read_text()
        idx = src.index('content_lower.startswith("/context")')
        next_elif = src.find("elif content_lower", idx + 10)
        block = src[idx:next_elif] if next_elif != -1 else src[idx:]
        assert "type(e).__name__" in block, "/context handler missing type(e).__name__"

    def test_context_command_logs_with_exc_info(self):
        src = (SRC / "governance/routes/chat/commands.py").read_text()
        idx = src.index('content_lower.startswith("/context")')
        next_elif = src.find("elif content_lower", idx + 10)
        block = src[idx:next_elif] if next_elif != -1 else src[idx:]
        assert "exc_info=True" in block, "/context handler missing exc_info=True"

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/chat/commands.py").read_text()
        assert "BUG-405-CMD-001" in src


# ── BUG-403-CRD-001/002: sessions/crud.py exc_info + catch-all ────────

class TestSessionsCrudExcInfo:
    """Session CRUD handlers must have exc_info and proper catch-all."""

    def _get_handler_block(self, src, handler_name):
        idx = src.index(f"def {handler_name}")
        next_def = src.find("\ndef ", idx + 10)
        return src[idx:next_def] if next_def != -1 else src[idx:]

    def test_list_sessions_typedb_exc_info(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        block = self._get_handler_block(src, "list_sessions")
        assert "exc_info=True" in block

    def test_create_session_typedb_exc_info(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        block = self._get_handler_block(src, "create_session")
        assert "exc_info=True" in block

    def test_get_session_typedb_exc_info(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        block = self._get_handler_block(src, "get_session")
        assert "exc_info=True" in block

    def test_get_session_has_catch_all(self):
        """get_session must catch Exception (not just TypeDBUnavailable)."""
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        block = self._get_handler_block(src, "get_session")
        assert "except Exception" in block, "get_session missing catch-all"
        assert "BUG-403-CRD-002" in block

    def test_bug_markers_present(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        assert "BUG-403-CRD-001" in src
        assert "BUG-403-CRD-002" in src

    def test_no_str_e_in_session_crud(self):
        """No detail=str(e) in any session CRUD handler."""
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        assert "detail=str(e)" not in src


# ── BUG-404-TM-006: tasks_mutations.py exc_info additions ─────────────

class TestTasksMutationsExcInfo:
    """All link/unlink logger.error() calls must have exc_info=True."""

    def _check_error_line(self, src, error_fragment):
        """Find logger.error line containing fragment, verify exc_info=True."""
        idx = src.index(error_fragment)
        line_end = src.index("\n", idx)
        line_start = src.rindex("\n", 0, idx) + 1
        line = src[line_start:line_end]
        assert "exc_info=True" in line, f"Missing exc_info=True in: {line.strip()}"

    def test_link_task_to_rule_exc_info(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        self._check_error_line(src, "Failed to link task")

    def test_link_task_to_session_exc_info(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        self._check_error_line(src, "Failed to link task")

    def test_link_task_to_document_exc_info(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        self._check_error_line(src, "Failed to link task")

    def test_unlink_task_from_document_exc_info(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        self._check_error_line(src, "Failed to unlink document")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        assert "BUG-404-TM-006" in src

    def test_all_outer_errors_have_exc_info(self):
        """Every logger.error in link/unlink functions should have exc_info."""
        src = (SRC / "governance/services/tasks_mutations.py").read_text()
        # Check all four link/unlink functions
        for func in ["link_task_to_rule", "link_task_to_session",
                      "link_task_to_document", "unlink_task_from_document"]:
            idx = src.index(f"def {func}")
            next_def = src.find("\ndef ", idx + 10)
            block = src[idx:next_def] if next_def != -1 else src[idx:]
            # Find all logger.error lines in block
            for i, line in enumerate(block.split("\n")):
                if "logger.error(" in line and "exc_info" not in line:
                    assert False, f"{func} has logger.error without exc_info: {line.strip()}"


# ── Module import defense tests ──────────────────────────────────────

class TestBatch405Imports:
    def test_tasks_crud_route_importable(self):
        import governance.routes.tasks.crud
        assert governance.routes.tasks.crud is not None

    def test_chat_commands_importable(self):
        import governance.routes.chat.commands
        assert governance.routes.chat.commands is not None

    def test_sessions_crud_importable(self):
        import governance.routes.sessions.crud
        assert governance.routes.sessions.crud is not None

    def test_tasks_mutations_importable(self):
        import governance.services.tasks_mutations
        assert governance.services.tasks_mutations is not None
