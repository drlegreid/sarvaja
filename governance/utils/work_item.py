# governance/utils/work_item.py
"""
Unified WorkItem Abstraction
============================
Per TASK 5: Common interface for gaps, tasks, and R&D items.

These are all "work items" with different types and metadata.
This abstraction provides:
- Common interface for to_dict, to_todo_format, priority ordering
- Unified backlog view across all work item sources
- Code reuse instead of duplicate implementations

Usage:
    from governance.utils.work_item import WorkItem, WorkItemType

    # Create from gap
    item = WorkItem.from_gap(gap)

    # Create from task
    item = WorkItem.from_task(task)

    # Unified backlog
    all_items = get_unified_backlog()
"""

from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import Optional, Dict, List, Any


class Priority(IntEnum):
    """Priority ordering (lower number = higher priority)."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    UNKNOWN = 5


class WorkItemType(str, Enum):
    """Types of work items."""
    GAP = "gap"
    TASK = "task"
    RD = "rd"


class WorkItemStatus(str, Enum):
    """Normalized status values."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    RESOLVED = "resolved"


@dataclass
class WorkItem:
    """
    Unified work item abstraction.

    Represents any trackable work: gaps, tasks, R&D items.
    Provides common interface for prioritization, serialization, and display.
    """
    id: str
    description: str
    priority: str
    status: str
    item_type: WorkItemType

    # Optional metadata
    name: str = ""
    category: str = ""
    phase: str = ""
    evidence: str = ""
    source: str = ""  # Where this came from (GAP-INDEX.md, TypeDB, TODO.md)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def priority_order(self) -> int:
        """Get numeric priority for sorting."""
        priority_upper = self.priority.upper().strip("*")
        try:
            return Priority[priority_upper].value
        except KeyError:
            return Priority.UNKNOWN.value

    @property
    def is_open(self) -> bool:
        """Check if work item is open/pending."""
        status_lower = self.status.lower()
        return status_lower in ("open", "pending", "in_progress", "todo")

    @property
    def is_resolved(self) -> bool:
        """Check if work item is resolved/completed."""
        status_lower = self.status.lower()
        return status_lower in ("resolved", "completed", "done")

    @property
    def display_name(self) -> str:
        """Get display name (name or description)."""
        return self.name if self.name else self.description

    def to_todo_format(self) -> str:
        """Format as todo item."""
        return f"[{self.priority.upper()}] {self.id}: {self.display_name}"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "item_type": self.item_type.value,
            "name": self.name,
            "category": self.category,
            "phase": self.phase,
            "evidence": self.evidence,
            "source": self.source,
            "priority_order": self.priority_order,
            "is_open": self.is_open,
            "is_resolved": self.is_resolved,
            "metadata": self.metadata,
        }

    @classmethod
    def from_gap(cls, gap: Any) -> "WorkItem":
        """
        Create WorkItem from a Gap object.

        Args:
            gap: Gap object from gap_parser.py

        Returns:
            WorkItem with gap data
        """
        status = "resolved" if getattr(gap, "is_resolved", False) else "open"
        return cls(
            id=gap.id,
            description=getattr(gap, "description", ""),
            priority=getattr(gap, "priority", "MEDIUM"),
            status=status,
            item_type=WorkItemType.GAP,
            category=getattr(gap, "category", ""),
            evidence=getattr(gap, "evidence", ""),
            source="GAP-INDEX.md",
        )

    @classmethod
    def from_task(cls, task: Any, source: str = "TypeDB") -> "WorkItem":
        """
        Create WorkItem from a Task object.

        Per GAP-GAPS-TASKS-001: Use item_type attribute when available.

        Args:
            task: Task object from entities.py or session_collector.py
            source: Where the task came from

        Returns:
            WorkItem with task data
        """
        task_id = getattr(task, "id", "") or getattr(task, "task_id", "")

        # GAP-GAPS-TASKS-001: Use item_type attribute if available
        task_item_type = getattr(task, "item_type", None)
        if task_item_type == "gap":
            item_type = WorkItemType.GAP
        elif task_item_type == "rd":
            item_type = WorkItemType.RD
        elif task_id.startswith("RD-"):
            # Fallback: infer from ID pattern
            item_type = WorkItemType.RD
        elif task_id.startswith("GAP-"):
            # Fallback: infer from ID pattern
            item_type = WorkItemType.GAP
        else:
            item_type = WorkItemType.TASK

        # GAP-GAPS-TASKS-001: Include document_path in metadata
        document_path = getattr(task, "document_path", None)

        return cls(
            id=task_id,
            description=getattr(task, "description", ""),
            priority=getattr(task, "priority", "MEDIUM"),
            status=getattr(task, "status", "pending"),
            item_type=item_type,
            name=getattr(task, "name", ""),
            phase=getattr(task, "phase", ""),
            source=source,
            metadata={
                "agent_id": getattr(task, "agent_id", None),
                "gap_id": getattr(task, "gap_id", None),
                "document_path": document_path,
            }
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkItem":
        """
        Create WorkItem from dictionary.

        Args:
            data: Dictionary with work item data

        Returns:
            WorkItem instance
        """
        item_type_str = data.get("item_type", "task")
        try:
            item_type = WorkItemType(item_type_str)
        except ValueError:
            item_type = WorkItemType.TASK

        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            priority=data.get("priority", "MEDIUM"),
            status=data.get("status", "pending"),
            item_type=item_type,
            name=data.get("name", ""),
            category=data.get("category", ""),
            phase=data.get("phase", ""),
            evidence=data.get("evidence", ""),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
        )


def sort_by_priority(items: List[WorkItem]) -> List[WorkItem]:
    """Sort work items by priority (CRITICAL first)."""
    return sorted(items, key=lambda x: x.priority_order)


def filter_open(items: List[WorkItem]) -> List[WorkItem]:
    """Filter to only open/pending items."""
    return [item for item in items if item.is_open]


def group_by_type(items: List[WorkItem]) -> Dict[str, List[WorkItem]]:
    """Group items by type."""
    result: Dict[str, List[WorkItem]] = {}
    for item in items:
        key = item.item_type.value
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


# CLI test
if __name__ == "__main__":
    # Test WorkItem creation
    item = WorkItem(
        id="GAP-TEST-001",
        description="Test gap",
        priority="HIGH",
        status="open",
        item_type=WorkItemType.GAP,
        source="test",
    )
    print(f"WorkItem: {item.to_todo_format()}")
    print(f"Priority order: {item.priority_order}")
    print(f"Is open: {item.is_open}")
    print(f"Dict: {item.to_dict()}")
