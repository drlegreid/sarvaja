"""Deep scan batch 180: Models + validation layer.

Batch 180 findings: 13 total, 0 confirmed fixes, 13 rejected/deferred.
All findings were design choices, migration concerns, or low-risk edge cases.
Tests verify current model contracts are stable.
"""
import pytest
from pathlib import Path


# ── Pydantic models contract defense ──────────────


class TestPydanticModelsContractDefense:
    """Verify key Pydantic model fields and defaults."""

    def test_task_create_has_status_default(self):
        """TaskCreate.status defaults to 'TODO'."""
        from governance.models import TaskCreate
        task = TaskCreate(task_id="TEST-001", description="test", phase="P1")
        assert task.status == "TODO"

    def test_task_response_has_resolution_field(self):
        """TaskResponse has resolution field."""
        from governance.models import TaskResponse
        assert "resolution" in TaskResponse.model_fields

    def test_session_response_has_project_id(self):
        """SessionResponse has project_id field."""
        from governance.models import SessionResponse
        assert "project_id" in SessionResponse.model_fields

    def test_decision_create_has_rules_applied(self):
        """DecisionCreate has rules_applied field."""
        from governance.models import DecisionCreate
        assert "rules_applied" in DecisionCreate.model_fields

    def test_agent_create_capabilities_default(self):
        """AgentCreate.capabilities defaults to empty list."""
        from governance.models import AgentCreate
        agent = AgentCreate(agent_id="test", name="Test")
        assert agent.capabilities == []


# ── TypeDB entities defense ──────────────


class TestTypeDBEntitiesDefense:
    """Verify TypeDB entity dataclass fields."""

    def test_task_entity_has_resolution(self):
        """Task entity has resolution field."""
        from governance.typedb.entities import Task
        task = Task(id="T-001", name="test", status="TODO", phase="P1")
        assert hasattr(task, "resolution")

    def test_task_entity_has_agent_id(self):
        """Task entity has agent_id field."""
        from governance.typedb.entities import Task
        task = Task(id="T-001", name="test", status="TODO", phase="P1")
        assert hasattr(task, "agent_id")

    def test_rule_entity_exists(self):
        """Rule entity exists in entities module."""
        from governance.typedb.entities import Rule
        assert Rule is not None

    def test_project_entity_exists(self):
        """Project entity exists in entities module."""
        from governance.typedb.entities import Project
        assert Project is not None


# ── Helpers conversion defense ──────────────


class TestHelpersConversionDefense:
    """Verify store helper conversion functions."""

    def test_task_to_response_importable(self):
        """task_to_response function is importable."""
        from governance.stores.helpers import task_to_response
        assert callable(task_to_response)

    def test_session_to_response_importable(self):
        """session_to_response function is importable."""
        from governance.stores.helpers import session_to_response
        assert callable(session_to_response)

    def test_synthesize_execution_events_exists(self):
        """synthesize_execution_events helper exists."""
        from governance.stores.helpers import synthesize_execution_events
        assert callable(synthesize_execution_events)


# ── Quality analyzer defense ──────────────


class TestQualityAnalyzerDefense:
    """Verify quality analyzer module structure."""

    def test_issue_severity_enum(self):
        """IssueSeverity enum has expected values."""
        from governance.quality.models import IssueSeverity
        assert hasattr(IssueSeverity, "CRITICAL")
        assert hasattr(IssueSeverity, "HIGH")
        assert hasattr(IssueSeverity, "MEDIUM")
        assert hasattr(IssueSeverity, "LOW")
        assert hasattr(IssueSeverity, "INFO")

    def test_rule_health_report_exists(self):
        """RuleHealthReport model exists."""
        from governance.quality.models import RuleHealthReport
        assert RuleHealthReport is not None

    def test_analyzer_importable(self):
        """RuleQualityAnalyzer is importable."""
        from governance.quality.analyzer import RuleQualityAnalyzer
        assert RuleQualityAnalyzer is not None
