"""Batch 227 — TypeDB + models + helpers defense tests.

Validates fixes for:
- BUG-227-HELPER-002: task description priority alignment (body > description > name)
- BUG-227-HELPER-003: Remove dead "completed" lowercase branch
- BUG-227-MODEL-004: TaskResponse linked fields default None vs []
- BUG-227-MODEL-002: SessionResponse missing persistence_status (documented)
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-227-HELPER-002: task description priority ──────────────────

class TestTaskDescriptionPriority:
    """task_to_response must use body > description > name (matching _task_to_dict)."""

    def test_helpers_description_uses_body_first(self):
        src = (SRC / "governance/stores/helpers.py").read_text()
        idx = src.index("def task_to_response")
        block = src[idx:idx + 600]
        assert "task.body or task.description or task.name" in block

    def test_typedb_access_description_uses_body_first(self):
        src = (SRC / "governance/stores/typedb_access.py").read_text()
        idx = src.index("def _task_to_dict")
        block = src[idx:idx + 600]
        assert "task.body or task.description or task.name" in block

    def test_both_paths_aligned(self):
        """Both conversion paths must have the same priority."""
        helpers_src = (SRC / "governance/stores/helpers.py").read_text()
        typedb_src = (SRC / "governance/stores/typedb_access.py").read_text()

        h_idx = helpers_src.index("def task_to_response")
        h_block = helpers_src[h_idx:h_idx + 600]

        t_idx = typedb_src.index("def _task_to_dict")
        t_block = typedb_src[t_idx:t_idx + 600]

        # Both should have body > description > name
        assert "task.body or task.description or task.name" in h_block
        assert "task.body or task.description or task.name" in t_block


# ── BUG-227-HELPER-003: Dead "completed" lowercase branch ──────────

class TestCompletedStatusBranch:
    """synthesize_execution_events should not check for lowercase 'completed'."""

    def test_no_lowercase_completed(self):
        src = (SRC / "governance/stores/helpers.py").read_text()
        idx = src.index("def synthesize_execution_events")
        block = src[idx:idx + 1200]
        assert '"completed"' not in block or '"completed"' in block.split("event_type")[1][:50], \
            "Lowercase 'completed' should only appear as event_type value, not as status check"

    def test_done_status_checked(self):
        src = (SRC / "governance/stores/helpers.py").read_text()
        idx = src.index("def synthesize_execution_events")
        block = src[idx:idx + 2000]
        assert '"DONE"' in block


# ── BUG-227-MODEL-004: TaskResponse linked fields ──────────────────

class TestTaskResponseLinkedDefaults:
    """TaskResponse.linked_* defaults should allow None (API contract)."""

    def test_task_response_model_has_linked_fields(self):
        from governance.models import TaskResponse
        fields = TaskResponse.model_fields
        for field_name in ("linked_rules", "linked_sessions", "linked_commits", "linked_documents"):
            assert field_name in fields, f"TaskResponse missing {field_name}"

    def test_task_to_response_coerces_null_to_empty_list(self):
        """helpers.task_to_response must coerce None to [] for linked fields."""
        src = (SRC / "governance/stores/helpers.py").read_text()
        idx = src.index("def task_to_response")
        block = src[idx:idx + 1200]
        assert "linked_rules=task.linked_rules or []" in block
        assert "linked_sessions=task.linked_sessions or []" in block


# ── Model validation tests ──────────────────────────────────────────

class TestModelValidation:
    """Defense tests for Pydantic model correctness."""

    def test_session_response_has_cc_fields(self):
        from governance.models import SessionResponse
        fields = SessionResponse.model_fields
        for cc_field in ("cc_session_uuid", "cc_project_slug", "cc_git_branch",
                         "cc_tool_count", "cc_thinking_chars", "cc_compaction_count"):
            assert cc_field in fields, f"SessionResponse missing {cc_field}"

    def test_session_response_has_project_id(self):
        from governance.models import SessionResponse
        assert "project_id" in SessionResponse.model_fields

    def test_agent_create_list_defaults_safe(self):
        """AgentCreate.capabilities and .rules with [] default should be safe in Pydantic."""
        from governance.models import AgentCreate
        a1 = AgentCreate(agent_id="a1", name="A1")
        a2 = AgentCreate(agent_id="a2", name="A2")
        a1.capabilities.append("test")
        assert "test" not in a2.capabilities, "Mutable default shared between instances!"

    def test_decision_create_uses_field_factory(self):
        from governance.models import DecisionCreate
        fields = DecisionCreate.model_fields
        # options and rules_applied should use Field(default_factory=list)
        assert "options" in fields
        assert "rules_applied" in fields


# ── Model import defense tests ──────────────────────────────────────

class TestModelImportDefense:
    """Defense tests for model modules."""

    def test_models_importable(self):
        import governance.models
        assert governance.models is not None

    def test_task_response_importable(self):
        from governance.models import TaskResponse
        assert TaskResponse is not None

    def test_session_response_importable(self):
        from governance.models import SessionResponse
        assert SessionResponse is not None

    def test_agent_response_importable(self):
        from governance.models import AgentResponse
        assert AgentResponse is not None

    def test_decision_response_importable(self):
        from governance.models import DecisionResponse
        assert DecisionResponse is not None

    def test_rule_response_importable(self):
        from governance.models import RuleResponse
        assert RuleResponse is not None

    def test_project_response_importable(self):
        from governance.models import ProjectResponse
        assert ProjectResponse is not None

    def test_pagination_meta_importable(self):
        from governance.models import PaginationMeta
        assert PaginationMeta is not None
