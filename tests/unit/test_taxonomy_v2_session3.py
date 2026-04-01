"""
EPIC-TASK-TAXONOMY-V2 Session 3: Quality Gates + Status Consolidation.

Tests cover:
1. normalize_status() — CLOSED→DONE mapping
2. STATUS_ALIASES dict
3. TYPE_DOD_REQUIREMENTS — per-type mandatory fields
4. validate_on_complete() — type-specific DoD enforcement
5. TYPE_RESOLUTION_TEMPLATES — per-type template definitions
6. build_resolution_summary() — type-specific template rendering
7. Service boundary normalization (create_task, update_task)
"""

from unittest.mock import patch, MagicMock

import pytest


# =============================================================================
# 1. Status Normalization (CLOSED → DONE)
# =============================================================================


class TestNormalizeStatus:
    """normalize_status() maps CLOSED→DONE, leaves others unchanged."""

    def test_closed_maps_to_done(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("CLOSED") == "DONE"

    def test_closed_lowercase_maps_to_done(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("closed") == "DONE"

    def test_closed_mixed_case_maps_to_done(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("Closed") == "DONE"

    def test_done_unchanged(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("DONE") == "DONE"

    def test_open_unchanged(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("OPEN") == "OPEN"

    def test_in_progress_unchanged(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("IN_PROGRESS") == "IN_PROGRESS"

    def test_todo_unchanged(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("TODO") == "TODO"

    def test_blocked_unchanged(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("BLOCKED") == "BLOCKED"

    def test_canceled_unchanged(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("CANCELED") == "CANCELED"

    def test_empty_string_passthrough(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status("") == ""

    def test_none_passthrough(self):
        from governance.task_lifecycle import normalize_status
        assert normalize_status(None) is None


class TestStatusAliases:
    """STATUS_ALIASES dict structure."""

    def test_aliases_contains_closed(self):
        from governance.task_lifecycle import STATUS_ALIASES
        assert "CLOSED" in STATUS_ALIASES

    def test_closed_maps_to_done(self):
        from governance.task_lifecycle import STATUS_ALIASES
        assert STATUS_ALIASES["CLOSED"] == "DONE"

    def test_aliases_only_contains_closed(self):
        from governance.task_lifecycle import STATUS_ALIASES
        assert len(STATUS_ALIASES) == 1


class TestCanonicalValues:
    """TaskStatus.canonical_values() excludes CLOSED."""

    def test_canonical_excludes_closed(self):
        from governance.task_lifecycle import TaskStatus
        canonical = TaskStatus.canonical_values()
        assert "CLOSED" not in canonical

    def test_canonical_includes_done(self):
        from governance.task_lifecycle import TaskStatus
        canonical = TaskStatus.canonical_values()
        assert "DONE" in canonical

    def test_canonical_includes_all_non_deprecated(self):
        from governance.task_lifecycle import TaskStatus
        canonical = TaskStatus.canonical_values()
        for expected in ["OPEN", "TODO", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELED"]:
            assert expected in canonical


# =============================================================================
# 2. Type-Specific DoD Requirements
# =============================================================================


class TestTypeDodRequirements:
    """TYPE_DOD_REQUIREMENTS structure and coverage."""

    def test_all_canonical_types_have_dod(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        for task_type in ["bug", "feature", "chore", "research", "spec", "test"]:
            assert task_type in TYPE_DOD_REQUIREMENTS, f"Missing DoD for {task_type}"

    def test_bug_requires_evidence(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        assert "evidence" in TYPE_DOD_REQUIREMENTS["bug"]

    def test_bug_requires_linked_sessions(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        assert "linked_sessions" in TYPE_DOD_REQUIREMENTS["bug"]

    def test_feature_requires_linked_documents(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        assert "linked_documents" in TYPE_DOD_REQUIREMENTS["feature"]

    def test_feature_does_not_require_evidence(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        assert "evidence" not in TYPE_DOD_REQUIREMENTS["feature"]

    def test_chore_minimal_requirements(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        chore_dod = TYPE_DOD_REQUIREMENTS["chore"]
        assert "summary" in chore_dod
        assert "agent_id" in chore_dod
        assert "linked_sessions" not in chore_dod
        assert "evidence" not in chore_dod

    def test_research_requires_evidence(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        assert "evidence" in TYPE_DOD_REQUIREMENTS["research"]

    def test_spec_requires_linked_documents(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        assert "linked_documents" in TYPE_DOD_REQUIREMENTS["spec"]

    def test_test_requires_evidence(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        assert "evidence" in TYPE_DOD_REQUIREMENTS["test"]

    def test_all_types_require_summary_and_agent(self):
        from governance.services.task_rules import TYPE_DOD_REQUIREMENTS
        for task_type, dod in TYPE_DOD_REQUIREMENTS.items():
            assert "summary" in dod, f"{task_type} missing summary"
            assert "agent_id" in dod, f"{task_type} missing agent_id"


# =============================================================================
# 3. validate_on_complete() Type-Specific DoD
# =============================================================================


class TestValidateOnCompleteTyped:
    """validate_on_complete() enforces type-specific DoD gates."""

    def _valid_base(self, **overrides):
        """Base valid task data for DONE gate."""
        base = dict(
            task_id="SRVJ-BUG-999",
            summary="test > unit > validate > dod",
            agent_id="code-agent",
            completed_at="2026-03-24T12:00:00",
            linked_sessions=["SESSION-2026-03-24-test"],
            linked_documents=["docs/plan.md"],
            evidence="Tests pass: 100/100",
        )
        base.update(overrides)
        return base

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_bug_passes_with_all_fields(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(task_type="bug", **self._valid_base())
        assert errors == []

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_bug_fails_without_evidence(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(task_type="bug", **self._valid_base(evidence=None))
        fields = [e.field for e in errors]
        assert "evidence" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_bug_fails_without_linked_sessions(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(task_type="bug", **self._valid_base(linked_sessions=None))
        fields = [e.field for e in errors]
        assert "linked_sessions" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_feature_passes_without_evidence(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(task_type="feature", **self._valid_base(evidence=None))
        assert errors == []

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_feature_fails_without_linked_documents(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type="feature", **self._valid_base(linked_documents=None),
        )
        fields = [e.field for e in errors]
        assert "linked_documents" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_chore_passes_with_minimal_fields(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type="chore",
            **self._valid_base(
                evidence=None, linked_sessions=None, linked_documents=None,
            ),
        )
        assert errors == []

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_research_fails_without_evidence(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type="research", **self._valid_base(evidence=None),
        )
        fields = [e.field for e in errors]
        assert "evidence" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_spec_fails_without_linked_documents(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type="spec", **self._valid_base(linked_documents=None),
        )
        fields = [e.field for e in errors]
        assert "linked_documents" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_test_fails_without_evidence(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type="test", **self._valid_base(evidence=None),
        )
        fields = [e.field for e in errors]
        assert "evidence" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_unknown_type_uses_default_dod(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type="unknown_type",
            **self._valid_base(
                evidence=None, linked_sessions=None, linked_documents=None,
            ),
        )
        # Default requires only summary + agent_id
        assert errors == []

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_none_type_uses_default_dod(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type=None,
            **self._valid_base(
                evidence=None, linked_sessions=None, linked_documents=None,
            ),
        )
        assert errors == []

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_always_requires_completed_at(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type="chore", **self._valid_base(completed_at=None),
        )
        fields = [e.field for e in errors]
        assert "completed_at" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_error_message_includes_type(self):
        from governance.services.task_rules import validate_on_complete
        errors = validate_on_complete(
            task_type="bug", **self._valid_base(evidence=None),
        )
        assert any("bug" in e.message for e in errors)


# =============================================================================
# 4. Type-Specific Resolution Templates
# =============================================================================


class TestTypeResolutionTemplates:
    """TYPE_RESOLUTION_TEMPLATES structure."""

    def test_all_canonical_types_have_templates(self):
        from governance.services.resolution_collator import TYPE_RESOLUTION_TEMPLATES
        for task_type in ["bug", "feature", "chore", "research", "spec", "test"]:
            assert task_type in TYPE_RESOLUTION_TEMPLATES, f"Missing template for {task_type}"

    def test_bug_has_root_cause_section(self):
        from governance.services.resolution_collator import TYPE_RESOLUTION_TEMPLATES
        titles = [s["title"] for s in TYPE_RESOLUTION_TEMPLATES["bug"]]
        assert "Root Cause" in titles

    def test_bug_has_regression_test_section(self):
        from governance.services.resolution_collator import TYPE_RESOLUTION_TEMPLATES
        titles = [s["title"] for s in TYPE_RESOLUTION_TEMPLATES["bug"]]
        assert "Regression Test" in titles

    def test_feature_has_requirements_section(self):
        from governance.services.resolution_collator import TYPE_RESOLUTION_TEMPLATES
        titles = [s["title"] for s in TYPE_RESOLUTION_TEMPLATES["feature"]]
        assert "Requirements Met" in titles

    def test_research_has_findings_section(self):
        from governance.services.resolution_collator import TYPE_RESOLUTION_TEMPLATES
        titles = [s["title"] for s in TYPE_RESOLUTION_TEMPLATES["research"]]
        assert "Findings" in titles

    def test_test_has_test_results_section(self):
        from governance.services.resolution_collator import TYPE_RESOLUTION_TEMPLATES
        titles = [s["title"] for s in TYPE_RESOLUTION_TEMPLATES["test"]]
        assert "Test Results" in titles

    def test_all_sections_have_required_keys(self):
        from governance.services.resolution_collator import TYPE_RESOLUTION_TEMPLATES
        for task_type, sections in TYPE_RESOLUTION_TEMPLATES.items():
            for section in sections:
                assert "title" in section, f"{task_type} section missing title"
                assert "key" in section, f"{task_type} section missing key"
                assert "fallback" in section, f"{task_type} section missing fallback"


# =============================================================================
# 5. build_resolution_summary() Type Dispatch
# =============================================================================


class TestBuildResolutionSummaryTyped:
    """build_resolution_summary() selects template by task_type."""

    def _task(self, task_type=None, **overrides):
        base = {
            "task_type": task_type,
            "linked_sessions": ["SESSION-001"],
            "linked_documents": ["docs/plan.md"],
            "linked_commits": ["abc123"],
            "evidence": "All tests pass",
        }
        base.update(overrides)
        return base

    def test_bug_includes_root_cause(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("bug"))
        assert "Root Cause" in result

    def test_bug_includes_regression_test(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("bug"))
        assert "Regression Test" in result

    def test_bug_header_includes_type(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("bug"))
        assert "## Resolution Summary (bug)" in result

    def test_feature_includes_requirements(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("feature"))
        assert "Requirements Met" in result

    def test_chore_includes_what_changed(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("chore"))
        assert "What Changed" in result

    def test_research_includes_findings(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("research"))
        assert "Findings" in result

    def test_research_includes_recommendation(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("research"))
        assert "Recommendation" in result

    def test_spec_includes_document(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("spec"))
        assert "Spec Document" in result

    def test_test_includes_results(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("test"))
        assert "Test Results" in result

    def test_none_type_uses_generic(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task(None))
        assert "## Resolution Summary\n" in result
        assert "## Resolution Summary (" not in result

    def test_unknown_type_uses_generic(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task("unknown"))
        assert "## Resolution Summary\n" in result

    def test_generic_preserves_original_behavior(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary(self._task(None))
        assert "### Sessions" in result
        assert "SESSION-001" in result
        assert "### Linked Documents" in result
        assert "docs/plan.md" in result

    def test_empty_task_returns_minimal(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary({"task_type": None})
        assert result == "Task completed."

    def test_typed_empty_returns_fallbacks(self):
        from governance.services.resolution_collator import build_resolution_summary
        result = build_resolution_summary({"task_type": "bug"})
        assert "Not documented" in result  # evidence fallback

    def test_session_metadata_used_in_typed(self):
        from governance.services.resolution_collator import build_resolution_summary
        task = self._task("bug")
        meta = [{"session_id": "SESSION-001", "description": "Fix crash", "duration": "30m"}]
        result = build_resolution_summary(task, session_metadata=meta)
        assert "Fix crash" in result
        assert "30m" in result

    def test_bug_evidence_renders_in_root_cause(self):
        from governance.services.resolution_collator import build_resolution_summary
        task = self._task("bug", evidence="Null pointer in parse()")
        result = build_resolution_summary(task)
        assert "Null pointer in parse()" in result

    def test_feature_documents_render(self):
        from governance.services.resolution_collator import build_resolution_summary
        task = self._task("feature", linked_documents=["docs/spec.md", "docs/design.md"])
        result = build_resolution_summary(task)
        assert "docs/spec.md" in result
        assert "docs/design.md" in result


# =============================================================================
# 6. Service Boundary CLOSED→DONE Normalization
# =============================================================================


class TestServiceBoundaryNormalization:
    """Service layer normalizes CLOSED→DONE before processing."""

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    def test_create_task_normalizes_closed_to_done(self, mock_client):
        from governance.services.tasks import create_task
        from governance.stores import _tasks_store
        with patch("governance.services.tasks.record_audit"):
            with patch("governance.services.tasks.log_event"):
                result = create_task(
                    task_id="SRVJ-CHORE-900",
                    description="test > normalize > closed > done",
                    status="CLOSED",
                    task_type="chore",
                )
        assert result["status"] == "DONE"
        _tasks_store.pop("SRVJ-CHORE-900", None)

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    def test_update_task_normalizes_closed_to_done(self, mock_client):
        from governance.stores import _tasks_store
        from governance.services.tasks_mutations import update_task

        # Seed a task
        _tasks_store["SRVJ-CHORE-901"] = {
            "task_id": "SRVJ-CHORE-901",
            "description": "test > normalize > update",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "test > normalize > update > status",
            "linked_sessions": ["SESSION-001"],
            "linked_documents": ["docs/plan.md"],
            "task_type": "chore",
        }

        with patch("governance.services.tasks_mutations._preload_task_from_typedb"):
            with patch("governance.services.tasks_mutations.record_audit"):
                with patch("governance.services.tasks_mutations.log_event"):
                    result = update_task("SRVJ-CHORE-901", status="CLOSED")

        assert result["status"] == "DONE"

        # Cleanup
        _tasks_store.pop("SRVJ-CHORE-901", None)
