"""Tests for FIX-HIER-002: Story entity + epic-contains-story, story-contains-task.

Validates:
1. Schema files define story entity with correct attributes and roles
2. Story linking operations generate correct TypeQL queries
3. Hierarchy: Project → Workspace → Epic → Story → Task → Bug
"""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path


# ── Schema tests ─────────────────────────────────────────────────────


class TestStorySchemaFiles:
    """Verify story schema files exist with correct content."""

    SCHEMA_DIR = Path("governance/schema_3x")

    def test_story_entity_file_exists(self):
        assert (self.SCHEMA_DIR / "09_story_entities_3x.tql").exists()

    def test_story_attributes_file_exists(self):
        assert (self.SCHEMA_DIR / "18_story_attributes_3x.tql").exists()

    def test_story_relations_file_exists(self):
        assert (self.SCHEMA_DIR / "28_story_relations_3x.tql").exists()

    def test_story_entity_owns_story_id(self):
        content = (self.SCHEMA_DIR / "09_story_entities_3x.tql").read_text()
        assert "owns story-id" in content

    def test_story_entity_plays_epic_role(self):
        content = (self.SCHEMA_DIR / "09_story_entities_3x.tql").read_text()
        assert "plays epic-contains-story:child-story" in content

    def test_story_entity_plays_task_role(self):
        content = (self.SCHEMA_DIR / "09_story_entities_3x.tql").read_text()
        assert "plays story-contains-task:parent-story" in content

    def test_story_attributes_defined(self):
        content = (self.SCHEMA_DIR / "18_story_attributes_3x.tql").read_text()
        for attr in ["story-id", "story-name", "story-description",
                      "story-status", "story-priority", "story-created-at"]:
            assert f"attribute {attr}" in content, f"Missing: {attr}"

    def test_story_relations_defined(self):
        content = (self.SCHEMA_DIR / "28_story_relations_3x.tql").read_text()
        assert "relation epic-contains-story" in content
        assert "relation story-contains-task" in content

    def test_epic_entity_plays_story_role(self):
        """Epic updated to play epic-contains-story:parent-epic."""
        content = (self.SCHEMA_DIR / "08_hierarchy_entities_3x.tql").read_text()
        assert "plays epic-contains-story:parent-epic" in content

    def test_task_entity_plays_story_role(self):
        """Task updated to play story-contains-task:story-task."""
        content = (self.SCHEMA_DIR / "01_core_entities_3x.tql").read_text()
        assert "plays story-contains-task:story-task" in content


class TestMonolithicSchemaStory:
    """Verify story additions in monolithic schema.tql."""

    def _read_schema(self):
        return Path("governance/schema.tql").read_text()

    def test_story_entity_defined(self):
        content = self._read_schema()
        assert "entity story," in content

    def test_story_attributes_defined(self):
        content = self._read_schema()
        assert "attribute story-id, value string;" in content
        assert "attribute story-name, value string;" in content

    def test_epic_contains_story_relation(self):
        content = self._read_schema()
        assert "relation epic-contains-story," in content

    def test_story_contains_task_relation(self):
        content = self._read_schema()
        assert "relation story-contains-task," in content

    def test_epic_plays_story_role(self):
        content = self._read_schema()
        assert "plays epic-contains-story:parent-epic" in content

    def test_task_plays_story_role(self):
        content = self._read_schema()
        assert "plays story-contains-task:story-task" in content


# ── Linking operations tests ─────────────────────────────────────────


class TestStoryLinkingOperations:
    """Test TypeQL query generation for story linking."""

    def _make_ops(self):
        """Create StoryLinkingOperations with mocked TypeDB driver."""
        from governance.typedb.queries.stories.linking import StoryLinkingOperations
        ops = StoryLinkingOperations()
        ops._driver = MagicMock()
        ops.database = "test_db"
        ops._execute_query = MagicMock(return_value=[])
        return ops

    def test_link_story_to_epic_query(self):
        ops = self._make_ops()
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        ops._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        ops._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = ops.link_story_to_epic("STORY-001", "EPIC-001")

        assert result is True
        query_arg = mock_tx.query.call_args[0][0]
        assert 'epic-id "EPIC-001"' in query_arg
        assert 'story-id "STORY-001"' in query_arg
        assert "epic-contains-story" in query_arg

    def test_link_task_to_story_query(self):
        ops = self._make_ops()
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        ops._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        ops._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        result = ops.link_task_to_story("TASK-001", "STORY-001")

        assert result is True
        query_arg = mock_tx.query.call_args[0][0]
        assert 'story-id "STORY-001"' in query_arg
        assert 'task-id "TASK-001"' in query_arg
        assert "story-contains-task" in query_arg

    def test_link_story_to_epic_failure(self):
        ops = self._make_ops()
        ops._driver.transaction.side_effect = Exception("TypeDB down")
        result = ops.link_story_to_epic("STORY-001", "EPIC-001")
        assert result is False

    def test_link_task_to_story_failure(self):
        ops = self._make_ops()
        ops._driver.transaction.side_effect = Exception("TypeDB down")
        result = ops.link_task_to_story("TASK-001", "STORY-001")
        assert result is False

    def test_get_stories_for_epic(self):
        ops = self._make_ops()
        ops._execute_query.return_value = [
            {"sid": "STORY-001"},
            {"sid": "STORY-002"},
        ]
        result = ops.get_stories_for_epic("EPIC-001")
        assert result == ["STORY-001", "STORY-002"]

    def test_get_tasks_for_story(self):
        ops = self._make_ops()
        ops._execute_query.return_value = [
            {"tid": "TASK-001"},
            {"tid": "TASK-002"},
        ]
        result = ops.get_tasks_for_story("STORY-001")
        assert result == ["TASK-001", "TASK-002"]

    def test_get_story_for_task_found(self):
        ops = self._make_ops()
        ops._execute_query.return_value = [{"sid": "STORY-001"}]
        result = ops.get_story_for_task("TASK-001")
        assert result == "STORY-001"

    def test_get_story_for_task_not_found(self):
        ops = self._make_ops()
        ops._execute_query.return_value = []
        result = ops.get_story_for_task("TASK-001")
        assert result == ""

    def test_escape_special_characters(self):
        from governance.typedb.queries.stories.linking import _escape
        assert _escape('test"value') == 'test\\"value'
        assert _escape('test\\path') == 'test\\\\path'


# ── Hierarchy coherence tests ────────────────────────────────────────


class TestHierarchyCoherence:
    """Verify the full hierarchy chain is represented."""

    def test_full_hierarchy_path(self):
        """Project → Plan → Epic → Story → Task is expressible."""
        schema = Path("governance/schema.tql").read_text()
        # Each relation in the chain must exist
        assert "relation project-contains-plan" in schema
        assert "relation plan-contains-epic" in schema
        assert "relation epic-contains-task" in schema
        assert "relation epic-contains-story" in schema
        assert "relation story-contains-task" in schema

    def test_story_does_not_duplicate_epic_task(self):
        """epic-contains-task still exists — story is optional intermediate."""
        schema = Path("governance/schema.tql").read_text()
        assert "relation epic-contains-task" in schema
        # Tasks can be under epics directly OR via stories
