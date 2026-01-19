"""
Handoff Models and Data Types.

Per AGENT-WORKSPACES.md Phase 4: Delegation Protocol.
Per RULE-011: Multi-Agent Governance Protocol.
Per RULE-001: Evidence-Based Governance.
Per DOC-SIZE-01-v1: Split from handoff.py (431 lines).

Created: 2026-01-17
"""

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


# =============================================================================
# ENUMS
# =============================================================================

class HandoffStatus(str, Enum):
    """Status of a task handoff."""
    READY_FOR_RESEARCH = "READY_FOR_RESEARCH"
    READY_FOR_CODING = "READY_FOR_CODING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    READY_FOR_SYNC = "READY_FOR_SYNC"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class AgentRole(str, Enum):
    """Agent workspace roles."""
    RESEARCH = "RESEARCH"
    CODING = "CODING"
    CURATOR = "CURATOR"
    SYNC = "SYNC"


# =============================================================================
# UTILITY FUNCTIONS (for markdown parsing)
# =============================================================================

def _extract_section(content: str, header: str) -> str:
    """Extract text content after a section header."""
    lines = content.split("\n")
    in_section = False
    section_lines = []

    for line in lines:
        if line.startswith(header):
            in_section = True
            continue
        elif in_section:
            if line.startswith("##") or line.startswith("---"):
                break
            if line.startswith("###"):
                break
            section_lines.append(line)

    return "\n".join(section_lines).strip()


def _extract_list(content: str, header: str) -> List[str]:
    """Extract bullet list items after a header."""
    lines = content.split("\n")
    in_section = False
    items = []

    for line in lines:
        if line.startswith(header):
            in_section = True
            continue
        elif in_section:
            if line.startswith("#") or line.startswith("---"):
                break
            if line.strip().startswith("- "):
                item = line.strip()[2:]
                # Remove backticks from file paths
                item = item.strip("`")
                items.append(item)

    return items


def _extract_numbered_list(content: str, header: str) -> List[str]:
    """Extract numbered list items after a header."""
    lines = content.split("\n")
    in_section = False
    items = []

    for line in lines:
        if line.startswith(header):
            in_section = True
            continue
        elif in_section:
            if line.startswith("#") or line.startswith("---"):
                break
            match = re.match(r"^\d+\.\s+(.+)$", line.strip())
            if match:
                items.append(match.group(1))

    return items


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class TaskHandoff:
    """
    Evidence handoff for task delegation between workspaces.

    Per AGENT-WORKSPACES.md: Tasks flow between workspaces via evidence files.
    """
    task_id: str                          # Task ID (e.g., "GAP-UI-005")
    title: str                            # Handoff title
    from_agent: str                       # Source agent role
    to_agent: str                         # Target agent role
    status: str                           # HandoffStatus value

    # Context gathered by source agent
    context_summary: str = ""             # Brief summary of findings
    files_examined: List[str] = field(default_factory=list)
    evidence_gathered: List[str] = field(default_factory=list)

    # Recommended action for target agent
    recommended_action: str = ""
    action_steps: List[str] = field(default_factory=list)

    # Constraints and rules
    linked_rules: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_session_id: Optional[str] = None
    priority: str = "MEDIUM"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Render handoff as markdown evidence file."""
        lines = [
            f"# Task Handoff: {self.title}",
            "",
            f"**From:** {self.from_agent} Agent",
            f"**To:** {self.to_agent} Agent",
            f"**Task ID:** {self.task_id}",
            f"**Status:** {self.status}",
            f"**Priority:** {self.priority}",
            f"**Created:** {self.created_at}",
        ]

        if self.source_session_id:
            lines.append(f"**Source Session:** {self.source_session_id}")

        lines.extend(["", "---", "", "## Context Gathered", ""])

        if self.context_summary:
            lines.append(self.context_summary)
            lines.append("")

        if self.files_examined:
            lines.append("### Files Examined")
            for f in self.files_examined:
                lines.append(f"- `{f}`")
            lines.append("")

        if self.evidence_gathered:
            lines.append("### Evidence")
            for e in self.evidence_gathered:
                lines.append(f"- {e}")
            lines.append("")

        lines.extend(["---", "", "## Recommended Action", ""])

        if self.recommended_action:
            lines.append(self.recommended_action)
            lines.append("")

        if self.action_steps:
            lines.append("### Steps")
            for i, step in enumerate(self.action_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        lines.extend(["---", "", "## Constraints", ""])

        if self.constraints:
            for c in self.constraints:
                lines.append(f"- {c}")
            lines.append("")

        if self.linked_rules:
            lines.append("### Linked Rules")
            for r in self.linked_rules:
                lines.append(f"- {r}")
            lines.append("")

        lines.extend([
            "---",
            "",
            f"*Generated by {self.from_agent} Agent at {self.created_at}*",
            "*Per AGENT-WORKSPACES.md: Task Delegation Protocol*",
        ])

        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, content: str) -> Optional["TaskHandoff"]:
        """Parse handoff from markdown content."""
        lines = content.split("\n")

        # Extract header metadata
        task_id = ""
        title = ""
        from_agent = ""
        to_agent = ""
        status = ""
        priority = "MEDIUM"
        created_at = ""
        source_session_id = None

        for line in lines:
            if line.startswith("# Task Handoff:"):
                title = line.replace("# Task Handoff:", "").strip()
            elif line.startswith("**From:**"):
                from_agent = line.split("**From:**")[1].replace("Agent", "").strip()
            elif line.startswith("**To:**"):
                to_agent = line.split("**To:**")[1].replace("Agent", "").strip()
            elif line.startswith("**Task ID:**"):
                task_id = line.split("**Task ID:**")[1].strip()
            elif line.startswith("**Status:**"):
                status = line.split("**Status:**")[1].strip()
            elif line.startswith("**Priority:**"):
                priority = line.split("**Priority:**")[1].strip()
            elif line.startswith("**Created:**"):
                created_at = line.split("**Created:**")[1].strip()
            elif line.startswith("**Source Session:**"):
                source_session_id = line.split("**Source Session:**")[1].strip()

        if not task_id:
            return None

        # Extract sections
        context_summary = _extract_section(content, "## Context Gathered")
        recommended_action = _extract_section(content, "## Recommended Action")

        # Extract lists
        files_examined = _extract_list(content, "### Files Examined")
        evidence_gathered = _extract_list(content, "### Evidence")
        action_steps = _extract_numbered_list(content, "### Steps")
        constraints = _extract_list(content, "## Constraints")
        linked_rules = _extract_list(content, "### Linked Rules")

        return cls(
            task_id=task_id,
            title=title,
            from_agent=from_agent,
            to_agent=to_agent,
            status=status,
            context_summary=context_summary,
            files_examined=files_examined,
            evidence_gathered=evidence_gathered,
            recommended_action=recommended_action,
            action_steps=action_steps,
            linked_rules=linked_rules,
            constraints=constraints,
            created_at=created_at or datetime.now().isoformat(),
            source_session_id=source_session_id,
            priority=priority,
        )
