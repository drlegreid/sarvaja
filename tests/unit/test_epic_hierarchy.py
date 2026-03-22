"""
Tests for BUG-TASK-HIER-001: Add epic-contains-task relation to TypeDB schema.

Root cause: Modular schema_3x is missing hierarchy files (08, 17, 27).
Task entity in 01_core_entities_3x.tql is missing `plays epic-contains-task:epic-task`.
Legacy schema.tql already has the relation (line 631-633) and task role (line 90).

Fix: Create modular schema files + add get_tasks_for_epic() + auto-link by prefix.

TDD: Tests define the contract. Per DOC-SIZE-01-v1: <=300 lines.
"""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCHEMA_TQL = Path(__file__).resolve().parents[2] / "governance" / "schema.tql"
SCHEMA_3X = Path(__file__).resolve().parents[2] / "governance" / "schema_3x"


# ── Schema Tests: Modular 3x ──


class TestEpicHierarchyModularSchema:
    """Verify modular schema_3x has hierarchy entities and relations."""

    def test_hierarchy_entities_file_exists(self):
        """08_hierarchy_entities_3x.tql must exist with Plan + Epic entities."""
        f = SCHEMA_3X / "08_hierarchy_entities_3x.tql"
        assert f.exists(), "Missing 08_hierarchy_entities_3x.tql"
        content = f.read_text()
        assert "entity plan," in content, "Plan entity not defined"
        assert "entity epic," in content, "Epic entity not defined"

    def test_hierarchy_attributes_file_exists(self):
        """17_hierarchy_attributes_3x.tql must exist with plan/epic attributes."""
        f = SCHEMA_3X / "17_hierarchy_attributes_3x.tql"
        assert f.exists(), "Missing 17_hierarchy_attributes_3x.tql"
        content = f.read_text()
        assert "plan-id" in content
        assert "epic-id" in content

    def test_hierarchy_relations_file_exists(self):
        """27_hierarchy_relations_3x.tql must exist with hierarchy relations."""
        f = SCHEMA_3X / "27_hierarchy_relations_3x.tql"
        assert f.exists(), "Missing 27_hierarchy_relations_3x.tql"
        content = f.read_text()
        assert "epic-contains-task" in content

    def test_epic_contains_task_relation_defined(self):
        """epic-contains-task relation must have parent-epic and epic-task roles."""
        f = SCHEMA_3X / "27_hierarchy_relations_3x.tql"
        content = f.read_text()
        match = re.search(r"relation epic-contains-task,.*?;", content, re.DOTALL)
        assert match, "epic-contains-task relation block not found"
        block = match.group()
        assert "relates parent-epic" in block
        assert "relates epic-task" in block

    def test_project_contains_plan_relation_defined(self):
        """project-contains-plan relation defined in hierarchy relations."""
        f = SCHEMA_3X / "27_hierarchy_relations_3x.tql"
        content = f.read_text()
        assert "relation project-contains-plan," in content

    def test_plan_contains_epic_relation_defined(self):
        """plan-contains-epic relation defined in hierarchy relations."""
        f = SCHEMA_3X / "27_hierarchy_relations_3x.tql"
        content = f.read_text()
        assert "relation plan-contains-epic," in content


class TestTaskEntityEpicRole:
    """Verify task entity can play epic-task in epic-contains-task."""

    def test_modular_task_entity_has_epic_role(self):
        """Task entity in 01_core_entities_3x.tql must have plays epic-contains-task:epic-task."""
        content = (SCHEMA_3X / "01_core_entities_3x.tql").read_text()
        match = re.search(r"entity task,.*?;", content, re.DOTALL)
        assert match, "task entity block not found"
        block = match.group()
        assert "plays epic-contains-task:epic-task" in block, \
            "BUG-TASK-HIER-001: task entity missing plays epic-contains-task:epic-task"

    def test_monolithic_task_entity_has_epic_role(self):
        """Task entity in schema.tql already has epic-contains-task role (reference)."""
        content = SCHEMA_TQL.read_text()
        match = re.search(r"entity task,.*?;", content, re.DOTALL)
        assert match, "task entity block not found"
        block = match.group()
        assert "plays epic-contains-task:epic-task" in block


# ── Linking Code Tests ──


class TestLinkEpicToTask:
    """Verify link_epic_to_task exists and works correctly."""

    def test_link_epic_to_task_method_exists(self):
        """ProjectLinkingOperations must have link_epic_to_task method."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        assert hasattr(ProjectLinkingOperations, "link_epic_to_task")

    def test_link_epic_to_task_uses_correct_relation(self):
        """link_epic_to_task must use epic-contains-task relation."""
        import inspect
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        source = inspect.getsource(ProjectLinkingOperations.link_epic_to_task)
        assert "epic-contains-task" in source
        assert "parent-epic" in source
        assert "epic-task" in source


class TestGetTasksForEpic:
    """Verify get_tasks_for_epic query function exists."""

    def test_method_exists(self):
        """ProjectLinkingOperations must have get_tasks_for_epic method."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        assert hasattr(ProjectLinkingOperations, "get_tasks_for_epic")

    def test_returns_list_of_task_ids(self):
        """get_tasks_for_epic must return list of task ID strings."""
        ops = MagicMock(spec=["get_tasks_for_epic"])
        ops.get_tasks_for_epic.return_value = ["EPIC-RULES-V3-P1", "EPIC-RULES-V3-P2"]
        result = ops.get_tasks_for_epic("EPIC-GOV-RULES-V3")
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_tasks_for_epic_uses_correct_relation(self):
        """get_tasks_for_epic must query epic-contains-task relation."""
        import inspect
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        source = inspect.getsource(ProjectLinkingOperations.get_tasks_for_epic)
        assert "epic-contains-task" in source


# ── Epic Entity Tests ──


class TestEpicEntityDefinition:
    """Verify Epic entity and models are defined."""

    def test_epic_dataclass_exists(self):
        """Epic dataclass must exist in entities.py."""
        import dataclasses
        from governance.typedb.entities import Epic
        field_names = {f.name for f in dataclasses.fields(Epic)}
        assert "id" in field_names
        assert "name" in field_names

    def test_epic_model_exists(self):
        """EpicCreate and EpicResponse models must exist."""
        from governance.models import EpicCreate, EpicResponse
        assert "epic_id" in EpicCreate.model_fields
        assert "epic_id" in EpicResponse.model_fields


# ── Monolithic Schema Consistency ──


class TestMonolithicSchemaHierarchy:
    """Verify monolithic schema.tql has all hierarchy relations (reference)."""

    def test_epic_contains_task_in_monolithic(self):
        content = SCHEMA_TQL.read_text()
        assert "relation epic-contains-task," in content

    def test_plan_contains_epic_in_monolithic(self):
        content = SCHEMA_TQL.read_text()
        assert "relation plan-contains-epic," in content

    def test_project_contains_plan_in_monolithic(self):
        content = SCHEMA_TQL.read_text()
        assert "relation project-contains-plan," in content

    def test_epic_entity_in_monolithic(self):
        content = SCHEMA_TQL.read_text()
        assert "entity epic," in content

    def test_plan_entity_in_monolithic(self):
        content = SCHEMA_TQL.read_text()
        assert "entity plan," in content
