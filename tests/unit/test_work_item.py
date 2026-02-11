"""
Unit tests for Unified WorkItem Abstraction.

Per TASK 5: Tests for WorkItem dataclass, WorkItemType/Status enums,
class methods, properties, and helper functions.
"""

import pytest
from unittest.mock import MagicMock

from governance.utils.work_item import (
    Priority,
    WorkItem,
    WorkItemType,
    WorkItemStatus,
    sort_by_priority,
    filter_open,
    group_by_type,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class TestEnums:
    """Tests for Priority, WorkItemType, WorkItemStatus enums."""

    def test_priority_ordering(self):
        assert Priority.CRITICAL < Priority.HIGH < Priority.MEDIUM < Priority.LOW

    def test_work_item_type_values(self):
        assert WorkItemType.GAP.value == "gap"
        assert WorkItemType.TASK.value == "task"
        assert WorkItemType.RD.value == "rd"

    def test_work_item_status_values(self):
        assert WorkItemStatus.OPEN.value == "open"
        assert WorkItemStatus.IN_PROGRESS.value == "in_progress"
        assert WorkItemStatus.COMPLETED.value == "completed"
        assert WorkItemStatus.BLOCKED.value == "blocked"
        assert WorkItemStatus.RESOLVED.value == "resolved"


# ---------------------------------------------------------------------------
# WorkItem basic
# ---------------------------------------------------------------------------
class TestWorkItemBasic:
    """Tests for WorkItem dataclass basics."""

    def test_defaults(self):
        item = WorkItem(id="T-1", description="Desc", priority="HIGH",
                        status="open", item_type=WorkItemType.TASK)
        assert item.name == ""
        assert item.category == ""
        assert item.phase == ""
        assert item.evidence == ""
        assert item.source == ""
        assert item.metadata == {}

    def test_priority_order_critical(self):
        item = WorkItem(id="T-1", description="", priority="CRITICAL",
                        status="open", item_type=WorkItemType.TASK)
        assert item.priority_order == 1

    def test_priority_order_with_stars(self):
        item = WorkItem(id="T-1", description="", priority="**HIGH**",
                        status="open", item_type=WorkItemType.TASK)
        assert item.priority_order == 2

    def test_priority_order_case_insensitive(self):
        item = WorkItem(id="T-1", description="", priority="low",
                        status="open", item_type=WorkItemType.TASK)
        assert item.priority_order == 4

    def test_priority_order_unknown(self):
        item = WorkItem(id="T-1", description="", priority="CUSTOM",
                        status="open", item_type=WorkItemType.TASK)
        assert item.priority_order == 5


# ---------------------------------------------------------------------------
# WorkItem properties
# ---------------------------------------------------------------------------
class TestWorkItemProperties:
    """Tests for WorkItem is_open, is_resolved, display_name."""

    def _make(self, **kw):
        defaults = {"id": "T-1", "description": "Desc", "priority": "HIGH",
                     "status": "open", "item_type": WorkItemType.TASK}
        defaults.update(kw)
        return WorkItem(**defaults)

    def test_is_open_statuses(self):
        for status in ("open", "pending", "in_progress", "todo"):
            assert self._make(status=status).is_open is True

    def test_is_open_false(self):
        for status in ("completed", "resolved", "done", "blocked"):
            assert self._make(status=status).is_open is False

    def test_is_resolved_statuses(self):
        for status in ("resolved", "completed", "done"):
            assert self._make(status=status).is_resolved is True

    def test_is_resolved_false(self):
        for status in ("open", "pending", "in_progress", "blocked"):
            assert self._make(status=status).is_resolved is False

    def test_display_name_uses_name(self):
        item = self._make(name="Task Name")
        assert item.display_name == "Task Name"

    def test_display_name_falls_back_to_description(self):
        item = self._make(name="", description="My Description")
        assert item.display_name == "My Description"


# ---------------------------------------------------------------------------
# to_todo_format / to_dict
# ---------------------------------------------------------------------------
class TestWorkItemSerialization:
    """Tests for to_todo_format() and to_dict()."""

    def _make(self, **kw):
        defaults = {"id": "GAP-TEST-001", "description": "Fix bug",
                     "priority": "HIGH", "status": "open",
                     "item_type": WorkItemType.GAP}
        defaults.update(kw)
        return WorkItem(**defaults)

    def test_to_todo_format(self):
        item = self._make()
        assert item.to_todo_format() == "[HIGH] GAP-TEST-001: Fix bug"

    def test_to_todo_format_with_name(self):
        item = self._make(name="Named Task")
        assert "Named Task" in item.to_todo_format()

    def test_to_dict_keys(self):
        item = self._make()
        d = item.to_dict()
        expected_keys = {"id", "description", "priority", "status", "item_type",
                         "name", "category", "phase", "evidence", "source",
                         "priority_order", "is_open", "is_resolved", "metadata"}
        assert set(d.keys()) == expected_keys

    def test_to_dict_item_type_serialized(self):
        item = self._make()
        assert item.to_dict()["item_type"] == "gap"

    def test_to_dict_computed_fields(self):
        item = self._make(status="open", priority="HIGH")
        d = item.to_dict()
        assert d["is_open"] is True
        assert d["is_resolved"] is False
        assert d["priority_order"] == 2


# ---------------------------------------------------------------------------
# from_gap
# ---------------------------------------------------------------------------
class TestFromGap:
    """Tests for WorkItem.from_gap() class method."""

    def _fake_gap(self, **kw):
        defaults = {"id": "GAP-001", "description": "Gap desc",
                     "priority": "HIGH", "category": "Testing",
                     "evidence": "ev.md", "is_resolved": False}
        defaults.update(kw)
        obj = MagicMock()
        for k, v in defaults.items():
            setattr(obj, k, v)
        return obj

    def test_basic_conversion(self):
        gap = self._fake_gap()
        item = WorkItem.from_gap(gap)
        assert item.id == "GAP-001"
        assert item.description == "Gap desc"
        assert item.priority == "HIGH"
        assert item.item_type == WorkItemType.GAP
        assert item.source == "GAP-INDEX.md"

    def test_open_status(self):
        gap = self._fake_gap(is_resolved=False)
        item = WorkItem.from_gap(gap)
        assert item.status == "open"

    def test_resolved_status(self):
        gap = self._fake_gap(is_resolved=True)
        item = WorkItem.from_gap(gap)
        assert item.status == "resolved"

    def test_missing_attributes_defaults(self):
        """When gap object lacks some attrs, getattr defaults work."""
        gap = MagicMock(spec=[])
        gap.id = "GAP-X"
        item = WorkItem.from_gap(gap)
        assert item.id == "GAP-X"
        assert item.priority == "MEDIUM"


# ---------------------------------------------------------------------------
# from_task
# ---------------------------------------------------------------------------
class TestFromTask:
    """Tests for WorkItem.from_task() class method."""

    def _fake_task(self, **kw):
        obj = MagicMock()
        for k, v in kw.items():
            setattr(obj, k, v)
        return obj

    def test_basic_task(self):
        task = self._fake_task(
            id="TASK-001", task_id="TASK-001", item_type=None,
            description="Do thing", priority="HIGH", status="IN_PROGRESS",
            name="Task Name", phase="implement", agent_id="code-agent",
            gap_id=None, document_path=None,
        )
        item = WorkItem.from_task(task)
        assert item.id == "TASK-001"
        assert item.item_type == WorkItemType.TASK
        assert item.metadata["agent_id"] == "code-agent"

    def test_gap_inferred_from_id(self):
        task = self._fake_task(
            id="GAP-AUTH-001", task_id="GAP-AUTH-001", item_type=None,
            description="", priority="HIGH", status="open",
            name="", phase="", agent_id=None, gap_id=None, document_path=None,
        )
        item = WorkItem.from_task(task)
        assert item.item_type == WorkItemType.GAP

    def test_rd_inferred_from_id(self):
        task = self._fake_task(
            id="RD-001", task_id="RD-001", item_type=None,
            description="", priority="MEDIUM", status="open",
            name="", phase="", agent_id=None, gap_id=None, document_path=None,
        )
        item = WorkItem.from_task(task)
        assert item.item_type == WorkItemType.RD

    def test_item_type_attribute_overrides_id(self):
        task = self._fake_task(
            id="TASK-001", task_id="TASK-001", item_type="gap",
            description="", priority="MEDIUM", status="open",
            name="", phase="", agent_id=None, gap_id=None, document_path=None,
        )
        item = WorkItem.from_task(task)
        assert item.item_type == WorkItemType.GAP

    def test_rd_item_type_attribute(self):
        task = self._fake_task(
            id="TASK-001", task_id="TASK-001", item_type="rd",
            description="", priority="MEDIUM", status="open",
            name="", phase="", agent_id=None, gap_id=None, document_path=None,
        )
        item = WorkItem.from_task(task)
        assert item.item_type == WorkItemType.RD

    def test_custom_source(self):
        task = self._fake_task(
            id="T-1", task_id="T-1", item_type=None,
            description="", priority="MEDIUM", status="open",
            name="", phase="", agent_id=None, gap_id=None,
            document_path="/docs/rule.md",
        )
        item = WorkItem.from_task(task, source="TODO.md")
        assert item.source == "TODO.md"
        assert item.metadata["document_path"] == "/docs/rule.md"

    def test_fallback_task_id_field(self):
        """When .id is empty, falls back to .task_id."""
        task = self._fake_task(
            id="", task_id="TASK-FALLBACK", item_type=None,
            description="", priority="MEDIUM", status="open",
            name="", phase="", agent_id=None, gap_id=None, document_path=None,
        )
        item = WorkItem.from_task(task)
        assert item.id == "TASK-FALLBACK"


# ---------------------------------------------------------------------------
# from_dict
# ---------------------------------------------------------------------------
class TestFromDict:
    """Tests for WorkItem.from_dict() class method."""

    def test_basic(self):
        data = {"id": "T-1", "description": "Desc", "priority": "HIGH",
                "status": "open", "item_type": "task"}
        item = WorkItem.from_dict(data)
        assert item.id == "T-1"
        assert item.item_type == WorkItemType.TASK

    def test_gap_type(self):
        data = {"id": "GAP-1", "item_type": "gap"}
        item = WorkItem.from_dict(data)
        assert item.item_type == WorkItemType.GAP

    def test_rd_type(self):
        data = {"id": "RD-1", "item_type": "rd"}
        item = WorkItem.from_dict(data)
        assert item.item_type == WorkItemType.RD

    def test_unknown_type_defaults_task(self):
        data = {"id": "X-1", "item_type": "unknown_type"}
        item = WorkItem.from_dict(data)
        assert item.item_type == WorkItemType.TASK

    def test_missing_type_defaults_task(self):
        data = {"id": "X-1"}
        item = WorkItem.from_dict(data)
        assert item.item_type == WorkItemType.TASK

    def test_all_fields(self):
        data = {
            "id": "T-1", "description": "Desc", "priority": "CRITICAL",
            "status": "in_progress", "item_type": "task", "name": "Name",
            "category": "Cat", "phase": "spec", "evidence": "ev.md",
            "source": "TypeDB", "metadata": {"key": "val"},
        }
        item = WorkItem.from_dict(data)
        assert item.name == "Name"
        assert item.category == "Cat"
        assert item.phase == "spec"
        assert item.evidence == "ev.md"
        assert item.source == "TypeDB"
        assert item.metadata == {"key": "val"}

    def test_empty_dict(self):
        item = WorkItem.from_dict({})
        assert item.id == ""
        assert item.priority == "MEDIUM"
        assert item.status == "pending"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
class TestHelperFunctions:
    """Tests for sort_by_priority, filter_open, group_by_type."""

    def _make(self, id, priority="MEDIUM", status="open", item_type=WorkItemType.TASK):
        return WorkItem(id=id, description="", priority=priority,
                        status=status, item_type=item_type)

    def test_sort_by_priority(self):
        items = [
            self._make("T-3", priority="LOW"),
            self._make("T-1", priority="CRITICAL"),
            self._make("T-2", priority="HIGH"),
        ]
        sorted_items = sort_by_priority(items)
        assert [i.id for i in sorted_items] == ["T-1", "T-2", "T-3"]

    def test_sort_by_priority_empty(self):
        assert sort_by_priority([]) == []

    def test_filter_open(self):
        items = [
            self._make("T-1", status="open"),
            self._make("T-2", status="completed"),
            self._make("T-3", status="in_progress"),
            self._make("T-4", status="resolved"),
        ]
        open_items = filter_open(items)
        assert len(open_items) == 2
        ids = [i.id for i in open_items]
        assert "T-1" in ids
        assert "T-3" in ids

    def test_filter_open_empty(self):
        assert filter_open([]) == []

    def test_group_by_type(self):
        items = [
            self._make("GAP-1", item_type=WorkItemType.GAP),
            self._make("T-1", item_type=WorkItemType.TASK),
            self._make("GAP-2", item_type=WorkItemType.GAP),
            self._make("RD-1", item_type=WorkItemType.RD),
        ]
        groups = group_by_type(items)
        assert len(groups["gap"]) == 2
        assert len(groups["task"]) == 1
        assert len(groups["rd"]) == 1

    def test_group_by_type_empty(self):
        assert group_by_type([]) == {}

    def test_group_by_type_single_type(self):
        items = [self._make("T-1"), self._make("T-2")]
        groups = group_by_type(items)
        assert len(groups) == 1
        assert len(groups["task"]) == 2
