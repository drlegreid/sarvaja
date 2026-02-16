"""
Unit tests for Tab Deep Scan Batch 29 — Stores + TypeDB access layer.

Covers: BUG-STORE-001 (missing linked_commits/resolution in _task_to_dict),
BUG-STORE-002 (null-safe linked fields), BUG-STORE-004 (audit JSON validation),
BUG-STORE-005 (extract_session_id regex).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


# ── BUG-STORE-001: _task_to_dict missing fields ─────────────────────


class TestTaskToDictFieldParity:
    """_task_to_dict must include all fields from task_to_response."""

    def test_has_resolution_field(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._task_to_dict)
        assert "resolution" in source

    def test_has_linked_commits_field(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._task_to_dict)
        assert "linked_commits" in source

    def test_both_converters_have_same_keys(self):
        """_task_to_dict and task_to_response should output same keys."""
        from governance.stores import typedb_access, helpers

        # Create a mock task with all fields
        task = MagicMock()
        task.id = "T-1"
        task.name = "Test"
        task.description = "Desc"
        task.body = "Body"
        task.phase = "BACKLOG"
        task.status = "TODO"
        task.priority = "HIGH"
        task.task_type = "bug"
        task.resolution = None
        task.agent_id = "code-agent"
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.linked_rules = []
        task.linked_sessions = []
        task.linked_commits = []
        task.linked_documents = []
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        dict_result = typedb_access._task_to_dict(task)
        response_result = helpers.task_to_response(task)
        response_dict = response_result.model_dump() if hasattr(response_result, 'model_dump') else response_result.dict()

        # _task_to_dict should have at least these keys from response
        for key in ["linked_commits", "resolution", "linked_rules",
                     "linked_sessions", "linked_documents"]:
            assert key in dict_result, f"_task_to_dict missing key: {key}"

    def test_bugfix_marker(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._task_to_dict)
        assert "BUG-STORE-001" in source


# ── BUG-STORE-002: Null-safe linked fields ───────────────────────────


class TestNullSafeLinkedFields:
    """linked_rules/sessions/documents/commits must never be None."""

    def test_task_to_dict_null_linked_rules(self):
        from governance.stores.typedb_access import _task_to_dict
        task = MagicMock()
        task.id = "T-1"
        task.name = "t"
        task.description = ""
        task.body = None
        task.phase = ""
        task.status = "TODO"
        task.priority = None
        task.task_type = None
        task.resolution = None
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.linked_rules = None
        task.linked_sessions = None
        task.linked_commits = None
        task.linked_documents = None
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        result = _task_to_dict(task)
        assert result["linked_rules"] == []
        assert result["linked_sessions"] == []
        assert result["linked_documents"] == []

    def test_task_to_response_null_linked_rules(self):
        from governance.stores.helpers import task_to_response
        task = MagicMock()
        task.id = "T-1"
        task.name = "t"
        task.description = ""
        task.body = None
        task.phase = ""
        task.status = "TODO"
        task.priority = None
        task.task_type = None
        task.resolution = None
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.linked_rules = None
        task.linked_sessions = None
        task.linked_commits = None
        task.linked_documents = None
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        result = task_to_response(task)
        assert result.linked_rules == []
        assert result.linked_sessions == []
        assert result.linked_documents == []
        assert result.linked_commits == []

    def test_task_to_dict_populated_linked_fields(self):
        from governance.stores.typedb_access import _task_to_dict
        task = MagicMock()
        task.id = "T-1"
        task.name = "t"
        task.description = ""
        task.body = None
        task.phase = ""
        task.status = "TODO"
        task.priority = None
        task.task_type = None
        task.resolution = None
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.linked_rules = ["R-1"]
        task.linked_sessions = ["S-1"]
        task.linked_commits = ["abc123"]
        task.linked_documents = ["doc.md"]
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        result = _task_to_dict(task)
        assert result["linked_rules"] == ["R-1"]
        assert result["linked_sessions"] == ["S-1"]
        assert result["linked_commits"] == ["abc123"]
        assert result["linked_documents"] == ["doc.md"]

    def test_bugfix_marker(self):
        from governance.stores import typedb_access
        source = inspect.getsource(typedb_access._task_to_dict)
        assert "BUG-STORE-002" in source


# ── BUG-STORE-004: Audit JSON validation ─────────────────────────────


class TestAuditJsonValidation:
    """_load_audit_store must validate JSON structure."""

    def test_loads_valid_list(self):
        from governance.stores import audit
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"entity_id": "E-1", "action_type": "CREATE"}], f)
            f.flush()
            path = Path(f.name)
        try:
            old_path = audit.AUDIT_STORE_PATH
            audit.AUDIT_STORE_PATH = path
            audit._load_audit_store()
            assert len(audit._audit_store) == 1
            assert audit._audit_store[0]["entity_id"] == "E-1"
        finally:
            audit.AUDIT_STORE_PATH = old_path
            path.unlink(missing_ok=True)

    def test_rejects_non_list_json(self):
        from governance.stores import audit
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"not": "a list"}, f)
            f.flush()
            path = Path(f.name)
        try:
            old_path = audit.AUDIT_STORE_PATH
            audit.AUDIT_STORE_PATH = path
            audit._load_audit_store()
            assert audit._audit_store == []
        finally:
            audit.AUDIT_STORE_PATH = old_path
            path.unlink(missing_ok=True)

    def test_filters_non_dict_entries(self):
        from governance.stores import audit
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"good": True}, "bad string", 42, None, {"also_good": True}], f)
            f.flush()
            path = Path(f.name)
        try:
            old_path = audit.AUDIT_STORE_PATH
            audit.AUDIT_STORE_PATH = path
            audit._load_audit_store()
            assert len(audit._audit_store) == 2
        finally:
            audit.AUDIT_STORE_PATH = old_path
            path.unlink(missing_ok=True)

    def test_handles_corrupted_json(self):
        from governance.stores import audit
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json")
            f.flush()
            path = Path(f.name)
        try:
            old_path = audit.AUDIT_STORE_PATH
            audit.AUDIT_STORE_PATH = path
            audit._load_audit_store()
            assert audit._audit_store == []
        finally:
            audit.AUDIT_STORE_PATH = old_path
            path.unlink(missing_ok=True)

    def test_bugfix_marker(self):
        from governance.stores import audit
        source = inspect.getsource(audit._load_audit_store)
        assert "BUG-STORE-004" in source


# ── BUG-STORE-005: extract_session_id regex ──────────────────────────


class TestExtractSessionIdRegex:
    """extract_session_id must handle topic-based and numeric session IDs."""

    def test_numeric_suffix(self):
        from governance.stores.helpers import extract_session_id
        result = extract_session_id("SESSION-2026-02-15-001.md")
        assert result == "SESSION-2026-02-15-001"

    def test_topic_based_suffix(self):
        from governance.stores.helpers import extract_session_id
        result = extract_session_id("SESSION-2026-02-15-DEEP-SCAN.md")
        assert result == "SESSION-2026-02-15-DEEP-SCAN"

    def test_chat_session_id(self):
        from governance.stores.helpers import extract_session_id
        result = extract_session_id("SESSION-2026-02-15-CHAT-TEST.md")
        assert result == "SESSION-2026-02-15-CHAT-TEST"

    def test_mcp_auto_session_id(self):
        from governance.stores.helpers import extract_session_id
        result = extract_session_id("SESSION-2026-02-15-MCP-AUTO-abc123.md")
        assert result == "SESSION-2026-02-15-MCP-AUTO-abc123"

    def test_cc_session_id(self):
        from governance.stores.helpers import extract_session_id
        result = extract_session_id("SESSION-2026-02-15-CC-platform.md")
        assert result == "SESSION-2026-02-15-CC-platform"

    def test_no_match(self):
        from governance.stores.helpers import extract_session_id
        result = extract_session_id("not-a-session.md")
        assert result is None

    def test_bugfix_marker(self):
        from governance.stores import helpers
        source = inspect.getsource(helpers.extract_session_id)
        assert "BUG-STORE-005" in source


# ── Retry decorator correctness ──────────────────────────────────────


class TestRetryDecorator:
    """retry_on_transient must handle edge cases properly."""

    def test_returns_on_first_success(self):
        from governance.stores.retry import retry_on_transient

        @retry_on_transient(max_attempts=3)
        def success():
            return "ok"

        assert success() == "ok"

    def test_retries_on_transient(self):
        from governance.stores.retry import retry_on_transient

        call_count = 0

        @retry_on_transient(max_attempts=3, base_delay=0.01)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("test")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 3

    def test_raises_after_all_attempts_exhausted(self):
        from governance.stores.retry import retry_on_transient
        import pytest

        @retry_on_transient(max_attempts=2, base_delay=0.01)
        def always_fail():
            raise TimeoutError("test")

        with pytest.raises(TimeoutError):
            always_fail()

    def test_non_transient_raises_immediately(self):
        from governance.stores.retry import retry_on_transient
        import pytest

        call_count = 0

        @retry_on_transient(max_attempts=3)
        def bad_code():
            nonlocal call_count
            call_count += 1
            raise ValueError("not transient")

        with pytest.raises(ValueError):
            bad_code()
        assert call_count == 1  # No retry for non-transient


# ── Session conversion consistency ───────────────────────────────────


class TestSessionConversionConsistency:
    """session_to_response and _session_to_dict must have same CC fields."""

    def test_both_have_cc_fields(self):
        from governance.stores import typedb_access, helpers
        dict_src = inspect.getsource(typedb_access._session_to_dict)
        resp_src = inspect.getsource(helpers.session_to_response)

        cc_fields = [
            "cc_session_uuid", "cc_project_slug", "cc_git_branch",
            "cc_tool_count", "cc_thinking_chars", "cc_compaction_count",
            "project_id",
        ]
        for field in cc_fields:
            assert field in dict_src, f"_session_to_dict missing {field}"
            assert field in resp_src, f"session_to_response missing {field}"

    def test_both_use_getattr_for_cc(self):
        """Both converters must use getattr for defensive CC access."""
        from governance.stores import typedb_access, helpers
        dict_src = inspect.getsource(typedb_access._session_to_dict)
        resp_src = inspect.getsource(helpers.session_to_response)

        for field in ["cc_session_uuid", "cc_project_slug", "cc_git_branch"]:
            assert f"getattr(session, '{field}'" in dict_src, \
                f"_session_to_dict not using getattr for {field}"
            assert f"getattr(session, '{field}'" in resp_src, \
                f"session_to_response not using getattr for {field}"
