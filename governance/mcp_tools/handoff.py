"""Task Handoff MCP Tools. Per AGENT-WORKSPACES.md Phase 4, RULE-011."""

import json
import re
from typing import Optional
from pathlib import Path

from governance.orchestrator.handoff import (
    create_handoff,
    write_handoff_evidence,
    read_handoff_evidence,
    get_pending_handoffs,
    HandoffStatus,
)


def register_handoff_tools(mcp) -> None:
    """Register handoff MCP tools."""

    @mcp.tool()
    def handoff_create(task_id: str, title: str, from_agent: str, to_agent: str,
                       context_summary: str, recommended_action: str,
                       files_examined: Optional[str] = None, evidence_gathered: Optional[str] = None,
                       action_steps: Optional[str] = None, linked_rules: Optional[str] = None,
                       constraints: Optional[str] = None, priority: str = "MEDIUM",
                       source_session_id: Optional[str] = None) -> str:
        """Create a task handoff for delegation to another agent workspace."""
        try:
            files_list = [f.strip() for f in (files_examined or "").split("|") if f.strip()]
            evidence_list = [e.strip() for e in (evidence_gathered or "").split("|") if e.strip()]
            steps_list = [s.strip() for s in (action_steps or "").split("|") if s.strip()]
            rules_list = [r.strip() for r in (linked_rules or "").split(",") if r.strip()]
            constraints_list = [c.strip() for c in (constraints or "").split("|") if c.strip()]

            handoff = create_handoff(
                task_id=task_id,
                title=title,
                from_agent=from_agent,
                to_agent=to_agent,
                context_summary=context_summary,
                recommended_action=recommended_action,
                files_examined=files_list,
                evidence_gathered=evidence_list,
                action_steps=steps_list,
                linked_rules=rules_list,
                constraints=constraints_list,
                priority=priority,
                source_session_id=source_session_id,
            )

            filepath = write_handoff_evidence(handoff)
            return json.dumps({
                "status": "created",
                "handoff": handoff.to_dict(),
                "evidence_file": str(filepath),
                "message": f"Handoff created for {to_agent} agent"
            }, default=str, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def handoffs_pending(for_agent: Optional[str] = None) -> str:
        """Get pending task handoffs, optionally filtered by target agent."""
        try:
            handoffs = get_pending_handoffs(for_agent=for_agent)

            return json.dumps({
                "count": len(handoffs),
                "handoffs": [h.to_dict() for h in handoffs],
                "filter": {"for_agent": for_agent}
            }, default=str, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def handoff_complete(task_id: str, from_agent: str, to_agent: str,
                         completion_notes: Optional[str] = None) -> str:
        """Mark a handoff as completed."""
        try:
            evidence_dir = Path(__file__).parent.parent.parent / "evidence"
            filename = f"HANDOFF-{task_id}-{from_agent.upper()}-{to_agent.upper()}.md"
            filepath = evidence_dir / filename

            if not filepath.exists():
                return json.dumps({"error": f"Handoff not found: {filename}"})

            handoff = read_handoff_evidence(filepath)
            if not handoff:
                return json.dumps({"error": "Failed to parse handoff file"})

            handoff.status = HandoffStatus.COMPLETED.value
            if completion_notes:
                handoff.evidence_gathered.append(f"Completion: {completion_notes}")
            write_handoff_evidence(handoff, evidence_dir)

            return json.dumps({
                "status": "completed",
                "task_id": task_id,
                "message": f"Handoff marked as completed by {to_agent} agent"
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def handoff_get(task_id: str, from_agent: str, to_agent: str) -> str:
        """Get a specific handoff by task ID and agents."""
        try:
            evidence_dir = Path(__file__).parent.parent.parent / "evidence"
            filename = f"HANDOFF-{task_id}-{from_agent.upper()}-{to_agent.upper()}.md"
            filepath = evidence_dir / filename

            if not filepath.exists():
                return json.dumps({"error": f"Handoff not found: {filename}"})

            handoff = read_handoff_evidence(filepath)
            if not handoff:
                return json.dumps({"error": "Failed to parse handoff file"})

            return json.dumps({
                "handoff": handoff.to_dict(),
                "evidence_file": str(filepath)
            }, default=str, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def handoff_route(task_id: str) -> str:
        """Determine which agent role should handle a task. Per AGENT-WORKSPACES.md."""
        try:
            task_upper = task_id.upper()
            if task_upper.startswith("RD-"):
                return json.dumps({
                    "task_id": task_id,
                    "recommended_agent": "RESEARCH",
                    "reason": "R&D tasks require exploration and analysis"
                }, indent=2)

            if task_upper.startswith("GAP-UI"):
                return json.dumps({"task_id": task_id, "recommended_agent": "CODING",
                                   "reason": "UI gaps typically require code implementation"}, indent=2)
            if task_upper.startswith("GAP-MCP"):
                return json.dumps({"task_id": task_id, "recommended_agent": "CODING",
                                   "reason": "MCP gaps require tool implementation"}, indent=2)
            if task_upper.startswith("GAP-DATA"):
                return json.dumps({"task_id": task_id, "recommended_agent": "CURATOR",
                                   "reason": "Data gaps require validation and governance"}, indent=2)
            if task_upper.startswith("P"):
                match = re.match(r"P(\d+)", task_upper)
                if match and int(match.group(1)) >= 12:
                    return json.dumps({"task_id": task_id, "recommended_agent": "CURATOR",
                                       "reason": "Orchestration phase requires governance oversight"}, indent=2)
            return json.dumps({"task_id": task_id, "recommended_agent": "RESEARCH",
                               "reason": "Default: Start with research to gather context"}, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})
