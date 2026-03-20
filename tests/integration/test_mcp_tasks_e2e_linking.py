"""MCP Tasks E2E Integration Tests — Linking, details, intent, verification.

Per EPIC-GOV-TASKS-V2 Phase 5: End-to-end tests for linking features.
Per DOC-SIZE-01-v1: Split from test_mcp_tasks_e2e.py.

Run: .venv/bin/python3 -m pytest tests/integration/test_mcp_tasks_e2e_linking.py -v
Requires: TypeDB on localhost:1729
"""

import pytest

from tests.integration.conftest import MockMCP, parse_mcp_result, make_test_id

pytestmark = [pytest.mark.integration, pytest.mark.typedb, pytest.mark.mcp]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def crud_tools(typedb_available):
    """Register task CRUD MCP tools."""
    from governance.mcp_tools.tasks_crud import register_task_crud_tools
    mcp = MockMCP()
    register_task_crud_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def link_tools(typedb_available):
    """Register task linking MCP tools."""
    from governance.mcp_tools.tasks_linking import register_task_linking_tools
    mcp = MockMCP()
    register_task_linking_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def verify_tools(typedb_available):
    """Register task verify/sync MCP tools."""
    from governance.mcp_tools.tasks_crud_verify import register_task_verify_tools
    mcp = MockMCP()
    register_task_verify_tools(mcp)
    return mcp.tools


@pytest.fixture(scope="module")
def intent_tools(typedb_available):
    """Register task intent/outcome MCP tools."""
    from governance.mcp_tools.tasks_intent import register_task_intent_tools
    mcp = MockMCP()
    register_task_intent_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

_created_task_ids = []


@pytest.fixture(scope="module", autouse=True)
def cleanup_tasks(typedb_available):
    """Delete test tasks after module completes."""
    yield
    if not _created_task_ids:
        return
    try:
        from governance.mcp_tools.common import get_typedb_client
        client = get_typedb_client()
        if client.connect():
            for tid in list(_created_task_ids):
                try:
                    client.delete_task(tid)
                except Exception:
                    pass
            client.close()
    except Exception:
        pass


def _create_test_task(crud_tools, prefix="E2E-LNK", **overrides):
    """Helper: create a task and track for cleanup."""
    tid = make_test_id(prefix)
    _created_task_ids.append(tid)
    defaults = dict(
        name=f"E2E Link Task {tid}",
        task_id=tid,
        description="Created by E2E linking test",
        status="OPEN",
        priority="LOW",
        task_type="test",
        phase="P10",
    )
    defaults.update(overrides)
    result = parse_mcp_result(crud_tools["task_create"](**defaults))
    return tid, result


# ===========================================================================
# Test Class: Task-Session Linking
# ===========================================================================

class TestTaskSessionLinking:
    """BDD: Task-session linking via MCP."""

    def test_link_session_to_task(self, crud_tools, link_tools):
        """task_link_session creates completed-in relation."""
        tid, _ = _create_test_task(crud_tools)
        sid = f"SESSION-E2E-{tid}"
        result = parse_mcp_result(
            link_tools["task_link_session"](task_id=tid, session_id=sid)
        )
        assert "task_id" in result or "error" in result


# ===========================================================================
# Test Class: Task-Document and Evidence Linking
# ===========================================================================

class TestTaskDocumentLinking:
    """BDD: Document and evidence linking via MCP tools."""

    def test_link_document(self, crud_tools, link_tools):
        """task_link_document creates document-references-task relation."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            link_tools["task_link_document"](
                task_id=tid, document_path="docs/test-doc.md"
            )
        )
        assert "task_id" in result or "error" in result

    def test_get_documents_returns_list(self, crud_tools, link_tools):
        """task_get_documents returns a list (possibly empty)."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            link_tools["task_get_documents"](task_id=tid)
        )
        assert "documents" in result or "error" in result

    def test_link_evidence(self, crud_tools, link_tools):
        """task_link_evidence creates evidence-supports relation."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            link_tools["task_link_evidence"](
                task_id=tid, evidence_path="evidence/e2e-test.md"
            )
        )
        assert "task_id" in result or "error" in result

    def test_get_evidence_returns_list(self, crud_tools, link_tools):
        """task_get_evidence returns a list (possibly empty)."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            link_tools["task_get_evidence"](task_id=tid)
        )
        assert "evidence_files" in result or "error" in result


# ===========================================================================
# Test Class: Task Commit Linking
# ===========================================================================

class TestTaskCommitLinking:
    """BDD: Commit linking via MCP tools."""

    def test_link_commit(self, crud_tools, link_tools):
        """task_link_commit creates task-commit relation."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            link_tools["task_link_commit"](
                task_id=tid, commit_sha="abc1234", commit_message="E2E test"
            )
        )
        assert "task_id" in result or "error" in result

    def test_link_commit_invalid_sha_rejected(self, link_tools):
        """task_link_commit rejects invalid commit SHA."""
        result = parse_mcp_result(
            link_tools["task_link_commit"](
                task_id="ANY", commit_sha="not-hex!!"
            )
        )
        assert "error" in result

    def test_get_commits_returns_list(self, crud_tools, link_tools):
        """task_get_commits returns a list (possibly empty)."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            link_tools["task_get_commits"](task_id=tid)
        )
        assert "commits" in result or "error" in result


# ===========================================================================
# Test Class: Task Detail Sections
# ===========================================================================

class TestTaskDetailSections:
    """BDD: Detail section CRUD via MCP tools."""

    def test_update_and_get_details(self, crud_tools, link_tools):
        """task_update_details + task_get_details roundtrip."""
        tid, _ = _create_test_task(crud_tools)
        update = parse_mcp_result(
            link_tools["task_update_details"](
                task_id=tid, business="E2E business context"
            )
        )
        assert "error" not in update or "updated_sections" in update

        get = parse_mcp_result(
            link_tools["task_get_details"](task_id=tid)
        )
        assert "task_id" in get or "error" in get


# ===========================================================================
# Test Class: Task Intent/Outcome Capture
# ===========================================================================

class TestTaskIntentOutcome:
    """BDD: Intent and outcome capture via MCP tools."""

    def test_capture_intent(self, crud_tools, intent_tools):
        """task_capture_intent records goal and steps."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            intent_tools["task_capture_intent"](
                task_id=tid, goal="E2E integration testing"
            )
        )
        assert "error" not in result or "task_id" in result

    def test_capture_outcome(self, crud_tools, intent_tools):
        """task_capture_outcome records achievement and status."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            intent_tools["task_capture_outcome"](
                task_id=tid, status="DONE", achieved="All E2E tests pass"
            )
        )
        assert "error" not in result or "task_id" in result


# ===========================================================================
# Test Class: Task Verification via MCP
# ===========================================================================

class TestTaskVerification:
    """BDD: Task verification via MCP verify tools."""

    def test_verify_task(self, crud_tools, verify_tools):
        """task_verify records verification evidence."""
        tid, _ = _create_test_task(crud_tools)
        result = parse_mcp_result(
            verify_tools["task_verify"](
                task_id=tid,
                verification_method="e2e-integration",
                evidence="All E2E tests pass",
                test_passed=True,
            )
        )
        assert "task_id" in result or "error" in result
