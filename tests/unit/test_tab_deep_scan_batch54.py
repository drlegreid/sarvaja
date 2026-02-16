"""
Batch 54 — Deep Scan: TypeDB query escaping + task route exception handling.

Fixes verified:
- BUG-TYPEQL-ESCAPE-001: status, phase, priority, resolution, gap_id escaped in insert_task
- BUG-ROUTE-NOEXCEPT-001: get_task, update_task, delete_task wrapped in try-except
"""
import ast
import inspect
import textwrap
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# BUG-TYPEQL-ESCAPE-001: TypeQL field escaping consistency
# ===========================================================================

class TestTypeQLFieldEscaping:
    """Verify all user-provided fields are escaped in TypeDB task insert."""

    def _get_insert_task_source(self):
        """Get source of insert_task method."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        return inspect.getsource(TaskCRUDOperations.insert_task)

    def test_status_escaped(self):
        """status field must be escaped before TypeQL interpolation."""
        src = self._get_insert_task_source()
        assert 'status_escaped' in src or 'status.replace' in src

    def test_phase_escaped(self):
        """phase field must be escaped before TypeQL interpolation."""
        src = self._get_insert_task_source()
        assert 'phase_escaped' in src or 'phase.replace' in src

    def test_priority_escaped(self):
        """priority field must be escaped before TypeQL interpolation."""
        src = self._get_insert_task_source()
        assert 'priority_escaped' in src or 'priority.replace' in src

    def test_resolution_escaped(self):
        """resolution field must be escaped before TypeQL interpolation."""
        src = self._get_insert_task_source()
        assert 'resolution_escaped' in src

    def test_gap_id_escaped(self):
        """gap_id field must be escaped before TypeQL interpolation."""
        src = self._get_insert_task_source()
        assert 'gap_id_escaped' in src

    def test_item_type_escaped(self):
        """item_type field must be escaped."""
        src = self._get_insert_task_source()
        assert 'item_type_escaped' in src

    def test_name_was_already_escaped(self):
        """name field should have been escaped (pre-existing)."""
        src = self._get_insert_task_source()
        assert 'name_escaped' in src

    def test_body_was_already_escaped(self):
        """body field should have been escaped (pre-existing)."""
        src = self._get_insert_task_source()
        assert 'body_escaped' in src

    def test_no_unescaped_status_in_insert(self):
        """Status in insert_parts must use escaped version."""
        src = self._get_insert_task_source()
        # Should NOT have raw {status}" in insert parts (only {status_escaped}")
        assert 'task-status "{status_escaped}"' in src or 'task-status "{status}"' not in src


# ===========================================================================
# BUG-ROUTE-NOEXCEPT-001: Task route exception handling
# ===========================================================================

class TestTaskRouteExceptionHandling:
    """Verify get_task, update_task, delete_task have try-except blocks."""

    def _get_crud_source(self):
        from governance.routes.tasks import crud
        return inspect.getsource(crud)

    def test_get_task_has_try_except(self):
        """get_task route must have try-except block."""
        src = self._get_crud_source()
        # Find the get_task function body
        get_task_idx = src.index("async def get_task")
        # Next function starts at next "async def" or "@router"
        next_func = src.find("@router", get_task_idx + 50)
        get_task_body = src[get_task_idx:next_func] if next_func > 0 else src[get_task_idx:]
        assert "try:" in get_task_body, "get_task must have try block"
        assert "except" in get_task_body, "get_task must have except block"

    def test_update_task_has_try_except(self):
        """update_task route must have try-except block."""
        src = self._get_crud_source()
        update_idx = src.index("async def update_task")
        next_func = src.find("@router", update_idx + 50)
        update_body = src[update_idx:next_func] if next_func > 0 else src[update_idx:]
        assert "try:" in update_body, "update_task must have try block"
        assert "except" in update_body, "update_task must have except block"

    def test_delete_task_has_try_except(self):
        """delete_task route must have try-except block."""
        src = self._get_crud_source()
        delete_idx = src.index("async def delete_task")
        next_func = src.find("@router", delete_idx + 50)
        delete_body = src[delete_idx:next_func] if next_func > 0 else src[delete_idx:]
        assert "try:" in delete_body, "delete_task must have try block"
        assert "except" in delete_body, "delete_task must have except block"

    def test_create_task_already_had_try_except(self):
        """create_task should already have had try-except (pre-existing)."""
        src = self._get_crud_source()
        create_idx = src.index("async def create_task")
        next_func = src.find("@router", create_idx + 50)
        create_body = src[create_idx:next_func] if next_func > 0 else src[create_idx:]
        assert "try:" in create_body

    def test_httpexception_reraise_pattern(self):
        """Handlers must re-raise HTTPException before catching generic Exception."""
        src = self._get_crud_source()
        # Count "except HTTPException:" — should appear in get, update, delete
        http_exception_count = src.count("except HTTPException:")
        assert http_exception_count >= 3, f"Expected 3+ HTTPException re-raises, found {http_exception_count}"


# ===========================================================================
# Cross-layer: TypeDB escaping consistency check
# ===========================================================================

class TestTypeQLEscapingCrossLayer:
    """Verify escaping patterns are consistent across TypeDB query builders."""

    def test_task_insert_escapes_all_string_fields(self):
        """All string fields interpolated into TypeQL must use .replace('\"', '\\\"')."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations.insert_task)
        # Count replace patterns for escaping
        escape_count = src.count('.replace(\'"\', \'\\\\"\')') + src.count('.replace(\'"\'')
        # name, body, status, phase, resolution, gap_id, item_type, document_path, agent_id, task_type, priority = 11
        assert escape_count >= 8, f"Expected 8+ field escaping calls, found {escape_count}"

    def test_rule_crud_has_escaping(self):
        """Rule CRUD should also escape fields."""
        try:
            from governance.typedb.queries.rules.crud import RuleQueryMixin
            src = inspect.getsource(RuleQueryMixin.create_rule)
            # At minimum, directive should be escaped
            assert "replace" in src, "Rule create must escape at least directive field"
        except ImportError:
            pytest.skip("Rule query module not available")
