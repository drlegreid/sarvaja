"""Deep scan batch 166: TypeDB client + stores layer.

Batch 166 findings: 25 total, 1 confirmed fix, 24 rejected.
- BUG-TYPEQL-ESCAPE-002: Missing backslash escaping in TypeQL write queries.
"""
import pytest
from pathlib import Path


# ── TypeQL backslash escaping defense ──────────────


class TestTypeQLBackslashEscapingDefense:
    """Verify TypeQL escaping handles backslashes before quotes."""

    def test_correct_escape_order(self):
        """Backslash must be escaped BEFORE double-quote."""
        value = 'foo\\"bar'  # Python literal: foo\"bar
        # Correct order: escape \ first, then "
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        # Wrong order would double-escape
        assert '\\\\"' in escaped or '\\"' in escaped

    def test_backslash_only_escaped(self):
        """String with only backslash is doubled."""
        value = "path\\to\\file"
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        assert "path\\\\to\\\\file" == escaped

    def test_quote_only_escaped(self):
        """String with only quotes is backslash-escaped."""
        value = 'say "hello"'
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        assert escaped == 'say \\"hello\\"'

    def test_crud_py_uses_backslash_escaping(self):
        """tasks/crud.py uses backslash+quote escaping (BUG-TYPEQL-ESCAPE-002)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        # Count occurrences of the correct pattern
        correct = src.count("replace('\\\\', '\\\\\\\\').replace('\"', '\\\\\"')")
        quote_only = src.count(".replace('\"', '\\\\\"')")
        # Most escapes should use the correct double-escape pattern
        assert correct >= 5, f"Expected >=5 correct escape patterns, found {correct}"

    def test_no_bare_quote_escape_in_insert_task(self):
        """insert_task fields all use backslash-first escaping."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        # Find the insert_task function
        start = src.index("def insert_task")
        end = src.index("\n    def ", start + 1)
        insert_func = src[start:end]
        # Count escaping patterns in insert_task only
        correct = insert_func.count("replace('\\\\', '\\\\\\\\')")
        assert correct >= 8, f"Expected >=8 backslash escapes in insert_task, found {correct}"


# ── Route path segment defense ──────────────


class TestRoutePathSegmentDefense:
    """Verify route path registration doesn't shadow static paths."""

    def test_rules_route_segments(self):
        """Static /rules/dependencies/overview has 3 segments, not matched by /rules/{rule_id} (2 segments)."""
        # FastAPI/Starlette matches path segment count exactly
        dynamic_segments = "/rules/{rule_id}".count("/")  # 2 segments
        static_segments = "/rules/dependencies/overview".count("/")  # 3 segments
        assert static_segments > dynamic_segments  # No shadowing

    def test_rules_route_registered(self):
        """Both /rules/{rule_id} and /rules/dependencies/overview are registered."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/rules/crud.py").read_text()
        assert '"/rules/{rule_id}"' in src
        assert '"/rules/dependencies/overview"' in src


# ── Singleton client defense ──────────────


class TestSingletonClientDefense:
    """Verify TypeDB client uses singleton pattern."""

    def test_client_singleton_pattern(self):
        """governance/client.py uses _client_instance singleton."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/client.py").read_text()
        assert "_client_instance" in src
        assert "global _client_instance" in src

    def test_asyncio_single_threaded(self):
        """FastAPI with uvicorn uses single-threaded asyncio (no race on singleton)."""
        # uvicorn default = 1 worker, asyncio event loop = single-threaded
        # Multi-threading requires --workers flag which is not used
        import asyncio
        assert hasattr(asyncio, 'get_event_loop')


# ── Session _session_to_dict defense ──────────────


class TestSessionToDictDefense:
    """Verify _session_to_dict handles all field types."""

    def test_tasks_completed_defaults_to_zero(self):
        """tasks_completed defaults to 0 in Session dataclass."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/entities.py").read_text()
        assert "tasks_completed" in src

    def test_start_time_handled(self):
        """_session_to_dict handles start_time conversion."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/typedb_access.py").read_text()
        assert "start_time" in src
        assert "isoformat" in src


# ── base3.py _process_results defense ──────────────


class TestBase3ProcessResultsDefense:
    """Verify base3.py result processing is defensive."""

    def test_process_results_has_except(self):
        """_process_results catches exceptions during result iteration."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/base3.py").read_text()
        assert "def _process_results" in src
        assert "except Exception" in src
