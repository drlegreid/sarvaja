"""
Handoff Operations.

Per AGENT-WORKSPACES.md Phase 4: Delegation Protocol.
Per RULE-011: Multi-Agent Governance Protocol.
Per DOC-SIZE-01-v1: Split from handoff.py (431 lines).

Created: 2026-01-17
"""

from pathlib import Path
from typing import List, Optional

from .models import TaskHandoff, HandoffStatus


def create_handoff(
    task_id: str,
    title: str,
    from_agent: str,
    to_agent: str,
    context_summary: str,
    recommended_action: str,
    files_examined: Optional[List[str]] = None,
    evidence_gathered: Optional[List[str]] = None,
    action_steps: Optional[List[str]] = None,
    linked_rules: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    priority: str = "MEDIUM",
    source_session_id: Optional[str] = None,
) -> TaskHandoff:
    """
    Create a new task handoff.

    Args:
        task_id: Task ID (e.g., "GAP-UI-005")
        title: Handoff title
        from_agent: Source agent role (RESEARCH, CODING, CURATOR, SYNC)
        to_agent: Target agent role
        context_summary: Brief summary of findings
        recommended_action: What the target agent should do
        files_examined: Files examined by source agent
        evidence_gathered: Evidence collected
        action_steps: Step-by-step action plan
        linked_rules: Relevant rule IDs
        constraints: Constraints to follow
        priority: Task priority
        source_session_id: Source session ID for traceability

    Returns:
        TaskHandoff object
    """
    # Determine status based on target agent
    status_map = {
        "RESEARCH": HandoffStatus.READY_FOR_RESEARCH,
        "CODING": HandoffStatus.READY_FOR_CODING,
        "CURATOR": HandoffStatus.READY_FOR_REVIEW,
        "SYNC": HandoffStatus.READY_FOR_SYNC,
    }
    status = status_map.get(to_agent.upper(), HandoffStatus.IN_PROGRESS)

    return TaskHandoff(
        task_id=task_id,
        title=title,
        from_agent=from_agent.upper(),
        to_agent=to_agent.upper(),
        status=status.value,
        context_summary=context_summary,
        files_examined=files_examined or [],
        evidence_gathered=evidence_gathered or [],
        recommended_action=recommended_action,
        action_steps=action_steps or [],
        linked_rules=linked_rules or [],
        constraints=constraints or [],
        priority=priority,
        source_session_id=source_session_id,
    )


def parse_handoff(content: str) -> Optional[TaskHandoff]:
    """Parse handoff from markdown content."""
    return TaskHandoff.from_markdown(content)


def write_handoff_evidence(
    handoff: TaskHandoff,
    evidence_dir: Path = None
) -> Path:
    """
    Write handoff to evidence file.

    Args:
        handoff: TaskHandoff object
        evidence_dir: Evidence directory (default: evidence/)

    Returns:
        Path to written evidence file
    """
    if evidence_dir is None:
        evidence_dir = Path(__file__).parent.parent.parent.parent / "evidence"

    # BUG-HANDOFF-001: Use parents=True so intermediate dirs are created
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename: HANDOFF-{task_id}-{from}-{to}.md
    filename = f"HANDOFF-{handoff.task_id}-{handoff.from_agent}-{handoff.to_agent}.md"
    filepath = evidence_dir / filename

    content = handoff.to_markdown()
    # BUG-342-HND-001: Specify encoding for container compatibility (LANG=C defaults to ASCII)
    filepath.write_text(content, encoding="utf-8")

    return filepath


def read_handoff_evidence(filepath: Path) -> Optional[TaskHandoff]:
    """
    Read handoff from evidence file.

    Args:
        filepath: Path to evidence file

    Returns:
        TaskHandoff object or None if parsing fails
    """
    if not filepath.exists():
        return None

    # BUG-342-HND-001: Specify encoding for container compatibility
    content = filepath.read_text(encoding="utf-8")
    return parse_handoff(content)


def get_pending_handoffs(
    evidence_dir: Path = None,
    for_agent: Optional[str] = None
) -> List[TaskHandoff]:
    """
    Get all pending handoffs from evidence directory.

    Args:
        evidence_dir: Evidence directory (default: evidence/)
        for_agent: Filter by target agent role

    Returns:
        List of pending TaskHandoff objects
    """
    if evidence_dir is None:
        evidence_dir = Path(__file__).parent.parent.parent.parent / "evidence"

    if not evidence_dir.exists():
        return []

    handoffs = []
    for filepath in evidence_dir.glob("HANDOFF-*.md"):
        handoff = read_handoff_evidence(filepath)
        if handoff:
            # Filter by agent if specified
            if for_agent and handoff.to_agent.upper() != for_agent.upper():
                continue
            # Only include pending (not completed)
            if handoff.status != HandoffStatus.COMPLETED.value:
                handoffs.append(handoff)

    return handoffs
