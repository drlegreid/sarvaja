"""
Synthetic TDD Suite — Entity Graph Validation.

Per RELIABILITY-PLAN-01-v1 P3: Seeds full entity graph
(Project > Task > Rule > Session > Agent) via service layer
and validates cross-references, heuristic checks, and lifecycle.

Uses in-memory stores only (no TypeDB dependency).
Services return plain dicts when TypeDB is unavailable.
"""
import pytest
from unittest.mock import patch


# ===== FIXTURES =====

@pytest.fixture(autouse=True)
def clean_stores():
    """Clear in-memory stores before each test."""
    from governance.stores.data_stores import _sessions_store, _tasks_store
    from governance.services.projects import _projects_store
    _sessions_store.clear()
    _tasks_store.clear()
    _projects_store.clear()
    yield
    _sessions_store.clear()
    _tasks_store.clear()
    _projects_store.clear()


@pytest.fixture
def no_typedb():
    """Mock TypeDB -> None to force in-memory fallback (returns dicts)."""
    with patch("governance.services.sessions_crud.get_typedb_client", return_value=None), \
         patch("governance.services.tasks.get_typedb_client", return_value=None), \
         patch("governance.services.tasks_mutations.get_typedb_client", return_value=None), \
         patch("governance.services.projects._get_client", return_value=None):
        yield


# ===== PROJECT > SESSION LINKAGE =====

class TestProjectSessionLinkage:
    """Validate Project > Session cross-references."""

    def test_create_project(self):
        from governance.services.projects import create_project
        with patch("governance.services.projects._get_client", return_value=None):
            result = create_project(name="Test Project", project_type="generic")
        assert result is not None
        assert result["name"] == "Test Project"
        assert "project_id" in result

    def test_session_links_to_project(self, no_typedb):
        from governance.services.sessions import create_session
        session = create_session(
            description="Test session",
            cc_project_slug="sarvaja-platform",
        )
        assert session["cc_project_slug"] == "sarvaja-platform"

    def test_project_has_session_count(self):
        from governance.services.projects import create_project
        with patch("governance.services.projects._get_client", return_value=None):
            proj = create_project(name="Counter Test")
        assert proj["session_count"] == 0

    def test_multiple_sessions_same_project(self, no_typedb):
        from governance.services.sessions import create_session
        s1 = create_session(description="Session 1", cc_project_slug="my-project")
        s2 = create_session(description="Session 2", cc_project_slug="my-project")
        assert s1["cc_project_slug"] == s2["cc_project_slug"]
        assert s1["session_id"] != s2["session_id"]


# ===== TASK > SESSION LINKAGE =====

class TestTaskSessionLinkage:
    """Validate Task > Session cross-references."""

    def test_task_links_to_session_explicitly(self, no_typedb):
        from governance.services.sessions import create_session
        from governance.services.tasks import create_task
        session = create_session(description="Work session")
        task = create_task(
            task_type="bug",
            description="Fix bug",
            linked_sessions=[session["session_id"]],
        )
        assert session["session_id"] in task["linked_sessions"]

    def test_task_has_linked_sessions_list(self, no_typedb):
        from governance.services.sessions import create_session
        from governance.services.tasks import create_task
        create_session(description="Active session")
        task = create_task(task_type="feature", description="New feature")
        assert isinstance(task["linked_sessions"], list)

    def test_task_links_multiple_sessions(self, no_typedb):
        from governance.services.sessions import create_session
        from governance.services.tasks import create_task
        s1 = create_session(description="Sprint 1")
        s2 = create_session(description="Sprint 2")
        task = create_task(
            task_type="epic",
            description="Cross-sprint epic",
            linked_sessions=[s1["session_id"], s2["session_id"]],
        )
        assert len(task["linked_sessions"]) == 2

    def test_task_status_lifecycle(self, no_typedb):
        from governance.services.tasks import create_task, update_task
        task = create_task(task_type="bug", description="Lifecycle test")
        assert task["status"] == "OPEN"
        updated = update_task(task["task_id"], status="IN_PROGRESS")
        assert updated["status"] == "IN_PROGRESS"


# ===== TASK > RULE LINKAGE =====

class TestTaskRuleLinkage:
    """Validate Task > Rule cross-references."""

    def test_task_links_to_rules(self, no_typedb):
        from governance.services.tasks import create_task
        task = create_task(
            task_type="feature",
            description="Implement session validation",
            linked_rules=["TEST-E2E-01-v1", "SESSION-EVID-01-v1"],
        )
        assert "TEST-E2E-01-v1" in task["linked_rules"]
        assert "SESSION-EVID-01-v1" in task["linked_rules"]

    def test_task_has_linked_documents_field(self, no_typedb):
        from governance.services.tasks import create_task
        task = create_task(task_type="chore", description="Update docs")
        assert "linked_documents" in task
        assert isinstance(task["linked_documents"], list)


# ===== SESSION > AGENT LINKAGE =====

class TestSessionAgentLinkage:
    """Validate Session > Agent cross-references."""

    def test_session_tracks_agent(self, no_typedb):
        from governance.services.sessions import create_session
        session = create_session(description="Agent work", agent_id="code-agent")
        assert session["agent_id"] == "code-agent"

    def test_task_tracks_agent(self, no_typedb):
        from governance.services.tasks import create_task
        task = create_task(
            task_type="bug",
            description="Agent task",
            agent_id="code-agent",
        )
        assert task["agent_id"] == "code-agent"


# ===== FULL ENTITY GRAPH =====

class TestFullEntityGraph:
    """Validate complete entity graph: Project > Session > Task > Rule."""

    def test_full_graph_creation(self, no_typedb):
        from governance.services.projects import create_project
        from governance.services.sessions import create_session
        from governance.services.tasks import create_task

        project = create_project(name="Game Dev", project_type="generic")
        assert project["project_id"] is not None

        session = create_session(
            description="Implement player movement",
            agent_id="code-agent",
            cc_project_slug="game-dev",
        )
        assert session["session_id"] is not None
        assert session["cc_project_slug"] == "game-dev"

        task = create_task(
            task_type="feature",
            description="Add WASD movement controls",
            linked_sessions=[session["session_id"]],
            linked_rules=["TEST-E2E-01-v1"],
            agent_id="code-agent",
        )
        assert task["task_id"] is not None
        assert session["session_id"] in task["linked_sessions"]
        assert "TEST-E2E-01-v1" in task["linked_rules"]
        assert task["agent_id"] == "code-agent"

    def test_graph_traversal_task_to_session(self, no_typedb):
        from governance.services.sessions import create_session
        from governance.services.tasks import create_task
        from governance.stores.data_stores import _sessions_store

        session = create_session(description="Work session")
        task = create_task(
            task_type="bug",
            description="Fix issue",
            linked_sessions=[session["session_id"]],
        )

        assert session["session_id"] in _sessions_store
        linked = _sessions_store[session["session_id"]]
        assert linked["description"] == "Work session"
        assert session["session_id"] in task["linked_sessions"]

    def test_graph_traversal_session_to_project(self, no_typedb):
        from governance.services.projects import create_project
        from governance.services.sessions import create_session

        create_project(name="Nav Test")
        session = create_session(
            description="Nav session",
            cc_project_slug="nav-test",
        )
        assert session["cc_project_slug"] == "nav-test"


# ===== HEURISTIC COMPATIBILITY =====

class TestHeuristicCompatibility:
    """Validate entity data is compatible with heuristic checks."""

    def test_session_data_matches_heuristic_format(self, no_typedb):
        from governance.services.sessions import create_session
        session = create_session(
            description="CC session",
            cc_session_uuid="uuid-abc-123",
            cc_project_slug="my-project",
        )
        assert session["session_id"].startswith("SESSION-")
        assert session["cc_session_uuid"] == "uuid-abc-123"

    def test_task_response_has_required_fields(self, no_typedb):
        from governance.services.tasks import create_task
        task = create_task(
            task_type="bug",
            description="Test format",
            linked_rules=["RULE-001"],
            linked_sessions=["SESSION-2026-02-20-TEST"],
        )
        assert "task_id" in task
        assert "description" in task
        assert "status" in task
        assert "linked_rules" in task
        assert "linked_sessions" in task

    def test_session_exclude_test_works(self):
        from governance.services.sessions import _is_test_artifact
        assert not _is_test_artifact({"session_id": "SESSION-2026-02-20-GAME-DEV"})
        assert not _is_test_artifact({"session_id": "SESSION-2026-02-20-JOB-HUNTING"})
        assert _is_test_artifact({"session_id": "SESSION-FAIL"})
        assert _is_test_artifact({"session_id": "SESSION-TEST"})
        assert _is_test_artifact({"session_id": "SESSION-2026-02-20-E2E-TEST-SMOKE"})
        assert _is_test_artifact({"session_id": "SESSION-2026-02-20-INTTEST-RULES"})


# ===== DATA INTEGRITY =====

class TestDataIntegrity:
    """Validate data integrity constraints across entity graph."""

    def test_session_id_unique(self, no_typedb):
        from governance.services.sessions import create_session
        s1 = create_session(description="Session 1")
        s2 = create_session(description="Session 2")
        assert s1["session_id"] != s2["session_id"]

    def test_task_id_unique(self, no_typedb):
        from governance.services.tasks import create_task
        t1 = create_task(task_type="bug", description="Bug 1")
        t2 = create_task(task_type="bug", description="Bug 2")
        assert t1["task_id"] != t2["task_id"]

    def test_session_timestamps_present(self, no_typedb):
        from governance.services.sessions import create_session
        session = create_session(description="Timestamp test")
        assert session["start_time"] is not None

    def test_task_created_at_present(self, no_typedb):
        from governance.services.tasks import create_task
        task = create_task(task_type="feature", description="Ts test")
        assert task["created_at"] is not None

    def test_session_status_default(self, no_typedb):
        from governance.services.sessions import create_session
        session = create_session(description="Status test")
        assert session["status"] == "ACTIVE"

    def test_task_status_default(self, no_typedb):
        from governance.services.tasks import create_task
        task = create_task(task_type="chore", description="Status test")
        assert task["status"] == "OPEN"
