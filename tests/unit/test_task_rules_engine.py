"""Tests for Task Quality Rules Engine (SRVJ-FEAT-001 + SRVJ-FEAT-002).

Per BDD scenarios from Phase 5 plan:
- task_create rejects missing summary
- task_create enforces laconic summary format
- task_create enforces project acronym in ID
- task_update to DONE rejects missing session
- spec type is valid across all layers
- Backward compat — old IDs still readable
"""
import pytest
from unittest.mock import patch, MagicMock

from governance.services.task_rules import (
    validate_on_create,
    validate_on_complete,
    format_validation_result,
    ValidationError,
    LACONIC_PATTERN,
    LACONIC_MIN_PATTERN,
    VALID_ACRONYMS,
    VALID_TYPE_PREFIXES,
)


# =============================================================================
# validate_on_create tests
# =============================================================================


class TestValidateOnCreate:
    """Tests for on_create validation rules."""

    def test_valid_task_passes(self):
        """Well-formed task with laconic summary passes all rules."""
        errors = validate_on_create(
            task_id="SRVJ-BUG-001",
            summary="UI > Task Detail > Session Click > Freeze",
            task_type="bug",
        )
        assert errors == []

    def test_missing_summary_and_description_fails(self):
        """task_create without summary OR description fails."""
        errors = validate_on_create(
            task_id="SRVJ-BUG-001",
            summary=None,
            description=None,
        )
        assert len(errors) == 1
        assert errors[0].rule == "RequiredField"
        assert errors[0].field == "summary"

    def test_description_without_summary_passes_required(self):
        """Description alone satisfies the required field check."""
        errors = validate_on_create(
            task_id="SRVJ-BUG-001",
            summary=None,
            description="Fix the session click freeze bug",
        )
        # No RequiredField error (description counts)
        required_errors = [e for e in errors if e.rule == "RequiredField"]
        assert required_errors == []

    def test_non_laconic_summary_format_error(self):
        """Summary not in laconic format gets FormatRule error."""
        errors = validate_on_create(
            summary="Session click freezes dashboard",
            task_type="bug",
        )
        format_errors = [e for e in errors if e.rule == "FormatRule"]
        assert len(format_errors) == 1
        assert "laconic format" in format_errors[0].message

    def test_laconic_summary_passes(self):
        """Proper laconic summary passes format check."""
        errors = validate_on_create(
            summary="UI > Task Detail > Session Click > Freeze",
            task_type="bug",
        )
        format_errors = [e for e in errors if e.rule == "FormatRule"]
        assert format_errors == []

    def test_three_segment_laconic_passes(self):
        """Three-segment laconic also passes (min pattern)."""
        errors = validate_on_create(
            summary="API > Tasks > Create",
            task_type="feature",
        )
        format_errors = [e for e in errors if e.rule == "FormatRule"]
        assert format_errors == []

    def test_invalid_project_acronym(self):
        """Unknown project acronym in task_id fails."""
        errors = validate_on_create(
            task_id="XYZQ-BUG-001",
            summary="UI > Test > Fail > Bad",
            task_type="bug",
        )
        acronym_errors = [e for e in errors if e.rule == "ProjectAcronymRule"]
        assert len(acronym_errors) == 1
        assert "XYZQ" in acronym_errors[0].message

    def test_valid_project_acronym_passes(self):
        """Known project acronym passes."""
        errors = validate_on_create(
            task_id="SRVJ-BUG-001",
            summary="UI > Test > Pass > Good",
            task_type="bug",
        )
        acronym_errors = [e for e in errors if e.rule == "ProjectAcronymRule"]
        assert acronym_errors == []

    def test_invalid_type_prefix(self):
        """Unknown type prefix in task_id fails."""
        errors = validate_on_create(
            task_id="SRVJ-ZZZZZ-001",
            summary="UI > Test > Fail > Bad",
            task_type="bug",
        )
        type_errors = [e for e in errors if e.rule == "TypePrefixRule"]
        assert len(type_errors) == 1

    def test_type_prefix_mismatch(self):
        """Type prefix in ID must match task_type."""
        errors = validate_on_create(
            task_id="SRVJ-FEAT-001",
            summary="UI > Test > Fix > Bug",
            task_type="bug",  # bug → BUG, not FEAT
        )
        mismatch_errors = [e for e in errors if e.rule == "TypePrefixMismatch"]
        assert len(mismatch_errors) == 1
        assert "FEAT" in mismatch_errors[0].message
        assert "BUG" in mismatch_errors[0].message

    def test_type_prefix_matches_task_type(self):
        """Matching type prefix and task_type passes."""
        errors = validate_on_create(
            task_id="SRVJ-BUG-001",
            summary="UI > Test > Fix > Bug",
            task_type="bug",
        )
        mismatch_errors = [e for e in errors if e.rule == "TypePrefixMismatch"]
        assert mismatch_errors == []

    def test_legacy_id_no_acronym_check(self):
        """Legacy IDs (BUG-011) don't trigger acronym/prefix checks."""
        errors = validate_on_create(
            task_id="BUG-011",
            summary="UI > Task Detail > Session Click > Freeze",
            task_type="bug",
        )
        acronym_errors = [e for e in errors if e.rule in ("ProjectAcronymRule", "TypePrefixRule")]
        assert acronym_errors == []

    def test_auto_generated_id_no_validation(self):
        """When task_id is None (auto-gen), no ID validation."""
        errors = validate_on_create(
            task_id=None,
            summary="API > Tasks > Create > Validation",
            task_type="feature",
        )
        id_errors = [e for e in errors if "task_id" in e.field]
        assert id_errors == []

    def test_spec_type_valid(self):
        """spec type is valid for task creation."""
        errors = validate_on_create(
            task_id="SRVJ-SPEC-001",
            summary="Task > Issue > Naming > Convention Spec",
            task_type="spec",
        )
        assert errors == []


# =============================================================================
# validate_on_complete tests (DONE gate)
# =============================================================================


class TestValidateOnComplete:
    """Tests for on_complete (DONE gate) validation rules."""

    def test_valid_done_passes(self):
        """Task with all required DONE fields passes."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary="UI > Task Detail > Session Click > Freeze",
            agent_id="code-agent",
            completed_at="2026-03-22T20:36:58",
            linked_sessions=["SESSION-2026-03-22-P5"],
            linked_documents=[".claude/plans/unified-wibbling-lagoon.md"],
        )
        assert errors == []

    def test_missing_session_fails(self):
        """DONE without linked session fails (bug type requires sessions)."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary="UI > Task > Fix > Bug",
            agent_id="code-agent",
            linked_sessions=[],
            task_type="bug",
        )
        session_errors = [e for e in errors if e.field == "linked_sessions"]
        assert len(session_errors) == 1
        assert "session" in session_errors[0].message.lower()

    def test_none_sessions_fails(self):
        """DONE with None linked_sessions fails (bug type requires sessions)."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary="UI > Task > Fix > Bug",
            agent_id="code-agent",
            linked_sessions=None,
            task_type="bug",
        )
        session_errors = [e for e in errors if e.field == "linked_sessions"]
        assert len(session_errors) == 1

    def test_missing_summary_fails(self):
        """DONE without summary fails."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary=None,
            agent_id="code-agent",
            linked_sessions=["SESSION-123"],
        )
        summary_errors = [e for e in errors if e.field == "summary"]
        assert len(summary_errors) == 1

    def test_missing_agent_fails(self):
        """DONE without agent_id fails."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary="UI > Task > Fix > Bug",
            agent_id=None,
            linked_sessions=["SESSION-123"],
            linked_documents=[".claude/plans/test.md"],
        )
        agent_errors = [e for e in errors if e.field == "agent_id"]
        assert len(agent_errors) == 1

    def test_missing_completed_at_fails(self):
        """DONE without completed_at fails (SRVJ-BUG-002)."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary="UI > Task > Fix > Bug",
            agent_id="code-agent",
            completed_at=None,
            linked_sessions=["SESSION-123"],
            linked_documents=[".claude/plans/test.md"],
        )
        completed_errors = [e for e in errors if e.field == "completed_at"]
        assert len(completed_errors) == 1
        assert "completed_at" in completed_errors[0].message

    def test_missing_linked_documents_fails(self):
        """DONE without linked_documents fails (feature type requires docs)."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary="UI > Task > Fix > Bug",
            agent_id="code-agent",
            completed_at="2026-03-22T20:36:58",
            linked_sessions=["SESSION-123"],
            linked_documents=[],
            task_type="feature",
        )
        doc_errors = [e for e in errors if e.field == "linked_documents"]
        assert len(doc_errors) == 1
        assert "document" in doc_errors[0].message.lower()

    def test_none_linked_documents_fails(self):
        """DONE with None linked_documents fails (feature type requires docs)."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary="UI > Task > Fix > Bug",
            agent_id="code-agent",
            completed_at="2026-03-22T20:36:58",
            linked_sessions=["SESSION-123"],
            linked_documents=None,
            task_type="feature",
        )
        doc_errors = [e for e in errors if e.field == "linked_documents"]
        assert len(doc_errors) == 1

    def test_all_missing_returns_all_errors(self):
        """DONE with nothing returns all errors for bug type (5: summary, agent_id,
        linked_sessions, evidence, completed_at). EPIC-TASK-TAXONOMY-V2: type-specific DoD."""
        errors = validate_on_complete(
            task_id="SRVJ-BUG-001",
            summary=None,
            agent_id=None,
            completed_at=None,
            linked_sessions=None,
            linked_documents=None,
            evidence=None,
            task_type="bug",
        )
        assert len(errors) == 5
        fields = {e.field for e in errors}
        assert fields == {"linked_sessions", "summary", "agent_id", "completed_at", "evidence"}


# =============================================================================
# format_validation_result tests
# =============================================================================


class TestFormatValidationResult:
    """Tests for validation result formatting."""

    def test_empty_errors_valid(self):
        """No errors → valid=True."""
        result = format_validation_result([])
        assert result["valid"] is True
        assert result["validation_errors"] == []

    def test_errors_invalid(self):
        """Errors → valid=False with structured details."""
        errors = [
            ValidationError("RequiredField", "summary", "summary is required"),
        ]
        result = format_validation_result(errors)
        assert result["valid"] is False
        assert len(result["validation_errors"]) == 1
        assert result["validation_errors"][0]["rule"] == "RequiredField"
        assert result["validation_errors"][0]["field"] == "summary"

    def test_validation_error_to_dict(self):
        """ValidationError.to_dict() returns proper structure."""
        err = ValidationError("FormatRule", "summary", "bad format")
        d = err.to_dict()
        assert d == {"rule": "FormatRule", "field": "summary", "message": "bad format"}


# =============================================================================
# Laconic pattern tests
# =============================================================================


class TestLaconicPatterns:
    """Tests for laconic summary regex patterns."""

    @pytest.mark.parametrize("summary", [
        "UI > Task Detail > Session Click > Freeze",
        "API > Tasks > Create > Missing Validation",
        "Schema > Story Entity > Insert > Relation Mismatch",
        "MCP > task_update > Status Change > No Session Link",
    ])
    def test_valid_four_segment(self, summary):
        """Four-segment laconic summaries match."""
        assert LACONIC_PATTERN.match(summary)
        assert LACONIC_MIN_PATTERN.match(summary)

    @pytest.mark.parametrize("summary", [
        "API > Tasks > Create",
        "Schema > Story > Insert",
    ])
    def test_valid_three_segment(self, summary):
        """Three-segment laconic summaries match min pattern."""
        assert LACONIC_MIN_PATTERN.match(summary)

    @pytest.mark.parametrize("summary", [
        "Session click freezes dashboard",
        "Fix the bug",
        "BUG-011",
        "",
    ])
    def test_invalid_not_laconic(self, summary):
        """Non-laconic summaries don't match."""
        assert not LACONIC_MIN_PATTERN.match(summary)


# =============================================================================
# Constants tests (SRVJ-FEAT-003 + SRVJ-FEAT-004)
# =============================================================================


class TestConstants:
    """Tests for spec type and project acronyms in constants."""

    def test_spec_in_task_types(self):
        """'spec' is in TASK_TYPES list."""
        from agent.governance_ui.state.constants import TASK_TYPES
        assert 'spec' in TASK_TYPES

    def test_specification_removed_from_task_types(self):
        """'specification' removed — 'spec' is canonical (EPIC-TASK-TAXONOMY-V2)."""
        from agent.governance_ui.state.constants import TASK_TYPES
        assert 'spec' in TASK_TYPES
        assert 'specification' not in TASK_TYPES

    def test_spec_has_prefix(self):
        """'spec' maps to 'SPEC' prefix."""
        from agent.governance_ui.state.constants import TASK_TYPE_PREFIX
        assert TASK_TYPE_PREFIX['spec'] == 'SPEC'

    def test_specification_not_in_prefix(self):
        """'specification' removed from TASK_TYPE_PREFIX (EPIC-TASK-TAXONOMY-V2)."""
        from agent.governance_ui.state.constants import TASK_TYPE_PREFIX
        assert 'specification' not in TASK_TYPE_PREFIX

    def test_project_acronyms_exist(self):
        """PROJECT_ACRONYMS dict is defined and populated."""
        from agent.governance_ui.state.constants import PROJECT_ACRONYMS
        assert 'sarvaja' in PROJECT_ACRONYMS
        assert PROJECT_ACRONYMS['sarvaja'] == 'SRVJ'
        assert PROJECT_ACRONYMS['gamedev'] == 'GAMD'
        assert PROJECT_ACRONYMS['jobhunt'] == 'JBHT'

    def test_sarvaja_platform_alias(self):
        """sarvaja-platform also maps to SRVJ."""
        from agent.governance_ui.state.constants import PROJECT_ACRONYMS
        assert PROJECT_ACRONYMS['sarvaja-platform'] == 'SRVJ'


# =============================================================================
# Pydantic model tests (spec type)
# =============================================================================


class TestPydanticModels:
    """Tests for spec type in Pydantic task models."""

    def test_task_create_accepts_spec(self):
        """TaskCreate model accepts task_type='spec'."""
        from governance.models import TaskCreate
        task = TaskCreate(
            description="Convention spec",
            phase="P10",
            task_type="spec",
        )
        assert task.task_type == "spec"

    def test_task_create_rejects_specification(self):
        """TaskCreate model rejects deprecated 'specification' — use 'spec' (META-TAXON-02-v1)."""
        from governance.models import TaskCreate
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            TaskCreate(
                description="Old style",
                phase="P10",
                task_type="specification",
            )

    def test_task_update_accepts_spec(self):
        """TaskUpdate model accepts task_type='spec'."""
        from governance.models import TaskUpdate
        update = TaskUpdate(task_type="spec")
        assert update.task_type == "spec"

    def test_task_create_rejects_invalid_type(self):
        """TaskCreate rejects unknown task types."""
        from governance.models import TaskCreate
        with pytest.raises(Exception):  # Pydantic ValidationError
            TaskCreate(
                description="Bad type",
                phase="P10",
                task_type="invalid_type",
            )


# =============================================================================
# Integration: create_task with rules engine
# =============================================================================


class TestCreateTaskRulesIntegration:
    """Tests for rules engine wired into create_task service."""

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_missing_summary_and_desc_raises(self, mock_client):
        """create_task with no summary and no description raises ValueError."""
        from governance.services.tasks import create_task
        mock_client.return_value = None

        with pytest.raises(ValueError, match="Validation failed"):
            create_task(
                task_id="SRVJ-BUG-001",
                description="",
                phase="P10",
                task_type="bug",
            )

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_type_prefix_mismatch_raises(self, mock_client):
        """create_task with mismatched ID type and task_type raises ValueError."""
        from governance.services.tasks import create_task
        mock_client.return_value = None

        with pytest.raises(ValueError, match="Validation failed"):
            create_task(
                task_id="SRVJ-FEAT-001",
                description="UI > Task > Fix > Bug",
                phase="P10",
                task_type="bug",  # BUG != FEAT
                summary="UI > Task > Fix > Bug",
            )

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_non_laconic_summary_warns_but_creates(self, mock_client):
        """Non-laconic summary triggers warning but doesn't block (FormatRule is soft)."""
        from governance.services.tasks import create_task
        mock_client.return_value = None

        # Should NOT raise — FormatRule is a warning, not a hard error
        result = create_task(
            task_id="SRVJ-BUG-042",
            description="Session click freezes dashboard",
            phase="P10",
            task_type="bug",
            summary="Session click freezes dashboard",
        )
        assert result is not None

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_valid_laconic_creates(self, mock_client):
        """Valid laconic summary creates task successfully."""
        from governance.services.tasks import create_task
        mock_client.return_value = None

        result = create_task(
            task_id="SRVJ-BUG-099",
            description="Fix the session click freeze",
            phase="P10",
            task_type="bug",
            summary="UI > Task Detail > Session Click > Freeze",
        )
        assert result is not None


# =============================================================================
# Integration: update_task DONE gate
# =============================================================================


class TestUpdateTaskDoneGate:
    """Tests for DONE gate wired into update_task service."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_done_without_session_raises(self, mock_client):
        """Transitioning to DONE without linked_sessions raises ValueError."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        mock_client.return_value = None

        # Seed fallback store
        _tasks_store["TEST-DONE-001"] = {
            "task_id": "TEST-DONE-001",
            "description": "Test task",
            "phase": "P10",
            "status": "IN_PROGRESS",
            "agent_id": None,
            "summary": None,
            "linked_sessions": [],
            "linked_documents": [],
        }

        try:
            with pytest.raises(ValueError, match="DONE gate"):
                update_task(
                    task_id="TEST-DONE-001",
                    status="DONE",
                )
        finally:
            _tasks_store.pop("TEST-DONE-001", None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_done_with_all_fields_passes(self, mock_client):
        """Transitioning to DONE with all required fields passes."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        mock_client.return_value = None

        _tasks_store["TEST-DONE-002"] = {
            "task_id": "TEST-DONE-002",
            "description": "Test task",
            "phase": "P10",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "UI > Test > Done > Gate",
            "linked_sessions": ["SESSION-123"],
            "linked_documents": [".claude/plans/test.md"],
            "created_at": "2026-03-22T00:00:00",
        }

        try:
            result = update_task(
                task_id="TEST-DONE-002",
                status="DONE",
            )
            assert result is not None
            assert result["status"] == "DONE"
        finally:
            _tasks_store.pop("TEST-DONE-002", None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_done_with_provided_fields_passes(self, mock_client):
        """DONE with fields provided in the update call itself passes."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        mock_client.return_value = None

        _tasks_store["TEST-DONE-003"] = {
            "task_id": "TEST-DONE-003",
            "description": "Test task",
            "phase": "P10",
            "status": "IN_PROGRESS",
            "agent_id": None,
            "summary": None,
            "linked_sessions": [],
            "linked_documents": [],
            "created_at": "2026-03-22T00:00:00",
        }

        try:
            result = update_task(
                task_id="TEST-DONE-003",
                status="DONE",
                agent_id="code-agent",
                summary="UI > Test > Done > WithFields",
                linked_sessions=["SESSION-456"],
                linked_documents=[".claude/plans/test.md"],
            )
            assert result is not None
            assert result["status"] == "DONE"
        finally:
            _tasks_store.pop("TEST-DONE-003", None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_done_without_linked_documents_raises(self, mock_client):
        """DONE without linked_documents raises ValueError (SRVJ-BUG-002)."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        mock_client.return_value = None

        _tasks_store["TEST-DONE-NODOC"] = {
            "task_id": "TEST-DONE-NODOC",
            "description": "Test task",
            "phase": "P10",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "UI > Test > Done > NoDocs",
            "task_type": "feature",  # feature requires linked_documents
            "linked_sessions": ["SESSION-123"],
            "linked_documents": [],
            "created_at": "2026-03-22T00:00:00",
        }

        try:
            with pytest.raises(ValueError, match="DONE gate"):
                update_task(
                    task_id="TEST-DONE-NODOC",
                    status="DONE",
                )
        finally:
            _tasks_store.pop("TEST-DONE-NODOC", None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_non_done_status_no_gate(self, mock_client):
        """Non-DONE status changes don't trigger the gate."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store
        mock_client.return_value = None

        _tasks_store["TEST-NONDONE-001"] = {
            "task_id": "TEST-NONDONE-001",
            "description": "Test task",
            "phase": "P10",
            "status": "TODO",
            "agent_id": None,
            "summary": None,
            "linked_sessions": [],
            "linked_documents": [],
            "created_at": "2026-03-22T00:00:00",
        }

        try:
            result = update_task(
                task_id="TEST-NONDONE-001",
                status="IN_PROGRESS",
            )
            assert result is not None
            assert result["status"] == "IN_PROGRESS"
        finally:
            _tasks_store.pop("TEST-NONDONE-001", None)


# =============================================================================
# Taxonomy endpoint test
# =============================================================================


class TestTaxonomyEndpoint:
    """Tests for taxonomy API including spec type and project acronyms."""

    def test_taxonomy_includes_spec(self):
        """Taxonomy includes 'spec' in task_types."""
        from agent.governance_ui.state.constants import TASK_TYPES
        assert 'spec' in TASK_TYPES

    def test_taxonomy_includes_project_acronyms(self):
        """Taxonomy includes PROJECT_ACRONYMS dict."""
        from agent.governance_ui.state.constants import PROJECT_ACRONYMS
        assert isinstance(PROJECT_ACRONYMS, dict)
        assert len(PROJECT_ACRONYMS) >= 3
