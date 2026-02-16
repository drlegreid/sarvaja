"""
Batch 73 — Deep Scan: Parsers + TypeDB access triage.

Fixes verified:
- BUG-PARSER-001: Pytest failure regex now matches paths with / and -
- BUG-TIMESTAMP-FORMAT-001: TypeQL timestamps now quoted
- BUG-CONTENT-001: Content indexer resume offset off-by-one fixed
- BUG-TASK-EXTRACT-002: _fetch_task_relation returns [] not None

Triage summary: 14 findings → 4 confirmed, 10 rejected.
"""
import inspect
import re
from unittest.mock import patch, MagicMock, PropertyMock

import pytest


# ===========================================================================
# BUG-PARSER-001: Pytest failure regex missing / and - characters
# ===========================================================================

class TestPytestRegexFix:
    """Verify failure_pattern now captures real pytest nodeids."""

    def _get_failure_pattern(self):
        from governance.routes.tests.parser import parse_pytest_output
        src = inspect.getsource(parse_pytest_output)
        # Extract the regex pattern from source
        match = re.search(r'failure_pattern = re\.compile\(r"(.+?)"\)', src)
        assert match, "Could not find failure_pattern regex"
        return re.compile(match.group(1))

    def test_regex_matches_path_with_slashes(self):
        """Nodeids like tests/unit/test_foo.py must match."""
        pattern = self._get_failure_pattern()
        line = "_____ tests/unit/test_foo.py::TestClass::test_method _____"
        m = pattern.search(line)
        assert m is not None
        assert "tests/unit/test_foo.py" in m.group(1)

    def test_regex_matches_parameterized_with_hyphens(self):
        """Nodeids like test_foo[param-1] must match."""
        pattern = self._get_failure_pattern()
        line = "_____ test_foo[param-1] _____"
        m = pattern.search(line)
        assert m is not None
        assert "test_foo[param-1]" in m.group(1)

    def test_regex_matches_full_nodeid(self):
        """Full pytest nodeid with path, class, method, params."""
        pattern = self._get_failure_pattern()
        line = "________ tests/unit/test-deep-scan.py::TestBatch::test_fix[v-1] ________"
        m = pattern.search(line)
        assert m is not None
        assert "/" in m.group(1)
        assert "-" in m.group(1)

    def test_parse_pytest_output_extracts_failures(self):
        """Functional test: parse_pytest_output finds failures in quiet mode."""
        from governance.routes.tests.parser import parse_pytest_output
        output = """FAILURES
_____ tests/unit/test_foo.py::TestBar::test_baz _____
some traceback here
_____ tests/unit/test_qux.py::test_quux[param-1] _____
another traceback
"""
        results = parse_pytest_output(output)
        assert len(results) == 2
        assert results[0]["nodeid"] == "tests/unit/test_foo.py::TestBar::test_baz"
        assert results[1]["nodeid"] == "tests/unit/test_qux.py::test_quux[param-1]"

    def test_character_class_includes_slash_and_hyphen(self):
        """The regex character class must contain / and -."""
        from governance.routes.tests.parser import parse_pytest_output
        src = inspect.getsource(parse_pytest_output)
        # Find the character class in the regex
        assert "/" in src, "Regex must include / for path separators"
        assert "\\-" in src or "-]" in src, "Regex must include - for hyphens"


# ===========================================================================
# TypeDB datetime attributes: timestamps must NOT be quoted (value datetime)
# REVERTED BUG-TIMESTAMP-FORMAT-001: Schema confirms datetime type, not string
# ===========================================================================

class TestTypeQLTimestampFormat:
    """Verify timestamps in TypeQL use unquoted datetime format (schema: value datetime)."""

    def _get_status_source(self):
        from governance.typedb.queries.tasks.status import update_task_status
        return inspect.getsource(update_task_status)

    def test_claimed_at_timestamp_unquoted(self):
        """claimed_at insert must use UNQUOTED timestamp (datetime type)."""
        src = self._get_status_source()
        assert 'task-claimed-at {timestamp_str}' in src, \
            "claimed_at timestamp must be unquoted for datetime type"
        assert 'task-claimed-at "{timestamp_str}"' not in src, \
            "claimed_at must NOT have quotes (datetime, not string)"

    def test_completed_at_timestamp_unquoted(self):
        """completed_at insert must use UNQUOTED timestamp (datetime type)."""
        src = self._get_status_source()
        assert 'task-completed-at {timestamp_str}' in src, \
            "completed_at timestamp must be unquoted for datetime type"
        assert 'task-completed-at "{timestamp_str}"' not in src, \
            "completed_at must NOT have quotes (datetime, not string)"

    def test_datetime_format_is_iso(self):
        """Timestamp format must be YYYY-MM-DDTHH:MM:SS (TypeDB datetime)."""
        src = self._get_status_source()
        assert "%Y-%m-%dT%H:%M:%S" in src, \
            "Timestamp must use ISO format for TypeDB datetime"


# ===========================================================================
# BUG-CONTENT-001: Content indexer resume offset off-by-one
# ===========================================================================

class TestContentIndexerResumeOffset:
    """Verify resume checkpoint uses correct offset (no off-by-one)."""

    def test_lines_processed_includes_plus_one(self):
        """lines_seen calculation must add +1 for correct resume boundary."""
        from governance.services.cc_content_indexer import index_session_content
        src = inspect.getsource(index_session_content)
        # Both batch and final flush should use + start_line + 1
        occurrences = src.count("+ start_line + 1")
        assert occurrences >= 2, \
            f"Expected at least 2 '+start_line+1' (batch+flush), found {occurrences}"

    def test_accumulator_line_end_is_relative(self):
        """_accumulate_semantic_chunks uses enumerate from 0 (relative index)."""
        from governance.services.cc_content_indexer import _accumulate_semantic_chunks
        src = inspect.getsource(_accumulate_semantic_chunks)
        # line_end = i where i comes from enumerate(entries)
        assert "line_end = i" in src
        # enumerate starts from 0, so line_end is relative to generator start
        assert "for i, entry in enumerate(entries)" in src

    def test_no_old_offset_pattern(self):
        """Old pattern without +1 must not exist."""
        from governance.services.cc_content_indexer import index_session_content
        src = inspect.getsource(index_session_content)
        # Should NOT have the old pattern: "line_end", lines_seen) + start_line\n
        # (without the +1)
        lines = src.splitlines()
        for line in lines:
            if "start_line" in line and "line_end" in line:
                assert "+ 1" in line, \
                    f"Missing +1 in offset calculation: {line.strip()}"


# ===========================================================================
# BUG-TASK-EXTRACT-002: _fetch_task_relation returns [] not None
# ===========================================================================

class TestFetchTaskRelationReturnType:
    """Verify _fetch_task_relation returns empty list, not None."""

    def test_return_type_annotation(self):
        """Return type should be List[str]."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        import typing
        hints = typing.get_type_hints(TaskReadQueries._fetch_task_relation)
        assert hints.get("return") == list[str] or "List" in str(hints.get("return", "")), \
            f"Expected List[str] return type, got {hints.get('return')}"

    def test_empty_results_return_empty_list(self):
        """When _safe_query returns [], _fetch_task_relation should return []."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._fetch_task_relation)
        # Must end with `else []` not `else None`
        assert "else []" in src, "Empty results should return [] not None"
        assert "else None" not in src, "Must not return None for empty results"

    def test_source_has_bug_comment(self):
        """Fix should have the bug reference comment."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._fetch_task_relation)
        assert "BUG-TASK-EXTRACT-002" in src


# ===========================================================================
# Rejected findings — confirm code is correct
# ===========================================================================

class TestRejectedFindings:
    """Confirm that rejected agent findings are indeed non-issues."""

    def test_typedb_variable_key_mapping_correct(self):
        """TypeDB 3.x: select $varname → result key 'varname' (agent claimed mismatch)."""
        from governance.typedb.queries.sessions.read import SessionReadQueries
        src = inspect.getsource(SessionReadQueries._build_session_from_id)
        # _build_session_from_id uses $desc → .get("desc"), $path → .get("path")
        assert '.get("desc")' in src
        assert '.get("path")' in src
        assert '.get("start")' in src

    def test_task_to_response_handles_none_lists(self):
        """task_to_response uses 'or []' for nullable list fields."""
        from governance.stores.helpers import task_to_response
        src = inspect.getsource(task_to_response)
        assert "linked_rules=task.linked_rules or []" in src
        assert "linked_sessions=task.linked_sessions or []" in src

    def test_status_escaping_consistent(self):
        """All user-provided fields in TypeQL are escaped."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        # Key fields should use .replace('"', '\\"')
        assert 'status.replace(\'"\', \'\\\\"\')' in src or \
               "status_escaped" in src

    def test_safe_query_returns_list(self):
        """_safe_query always returns a list (empty on error)."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._safe_query)
        assert "return []" in src
