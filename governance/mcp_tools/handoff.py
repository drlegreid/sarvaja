"""Task Handoff MCP Tools. Per AGENT-WORKSPACES.md Phase 4, RULE-011."""

import logging
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
from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)


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
            # BUG-299-HND-001: Sanitize task_id, from_agent, to_agent to prevent path
            # traversal via write_handoff_evidence which builds filename from these fields
            task_id = re.sub(r'[^A-Za-z0-9_\-]', '_', task_id)
            from_agent = re.sub(r'[^A-Za-z0-9_\-]', '_', from_agent)
            to_agent = re.sub(r'[^A-Za-z0-9_\-]', '_', to_agent)
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
            return format_mcp_result({
                "status": "created",
                "handoff": handoff.to_dict(),
                "evidence_file": str(filepath),
                "message": f"Handoff created for {to_agent} agent"
            })

        except Exception as e:
            # BUG-361-HND-001: Log full error but return only type name to prevent info disclosure
            logger.error(f"handoff_create failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"handoff_create failed: {type(e).__name__}"})

    @mcp.tool()
    def handoffs_pending(for_agent: Optional[str] = None) -> str:
        """Get pending task handoffs, optionally filtered by target agent."""
        try:
            handoffs = get_pending_handoffs(for_agent=for_agent)

            return format_mcp_result({
                "count": len(handoffs),
                "handoffs": [h.to_dict() for h in handoffs],
                "filter": {"for_agent": for_agent}
            })

        except Exception as e:
            # BUG-361-HND-001: Log full error but return only type name
            logger.error(f"handoffs_pending failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"handoffs_pending failed: {type(e).__name__}"})

    @mcp.tool()
    def handoff_complete(task_id: str, from_agent: str, to_agent: str,
                         completion_notes: Optional[str] = None) -> str:
        """Mark a handoff as completed."""
        try:
            evidence_dir = Path(__file__).parent.parent.parent / "evidence"
            # BUG-229-HANDOFF-001: Whitelist sanitize to prevent path traversal
            safe_task = re.sub(r'[^A-Za-z0-9_\-]', '_', task_id)
            safe_from = re.sub(r'[^A-Za-z0-9_\-]', '_', from_agent.upper())
            safe_to = re.sub(r'[^A-Za-z0-9_\-]', '_', to_agent.upper())
            filename = f"HANDOFF-{safe_task}-{safe_from}-{safe_to}.md"
            filepath = evidence_dir / filename

            if not filepath.exists():
                return format_mcp_result({"error": f"Handoff not found: {filename}"})

            handoff = read_handoff_evidence(filepath)
            if not handoff:
                return format_mcp_result({"error": "Failed to parse handoff file"})

            handoff.status = HandoffStatus.COMPLETED.value
            if completion_notes:
                # BUG-288-HND-001: Guard against None evidence_gathered list
                if handoff.evidence_gathered is None:
                    handoff.evidence_gathered = []
                handoff.evidence_gathered.append(f"Completion: {completion_notes}")
            write_handoff_evidence(handoff, evidence_dir)

            return format_mcp_result({
                "status": "completed",
                "task_id": task_id,
                "message": f"Handoff marked as completed by {to_agent} agent"
            })

        except Exception as e:
            # BUG-361-HND-001: Log full error but return only type name
            logger.error(f"handoff_complete failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"handoff_complete failed: {type(e).__name__}"})

    @mcp.tool()
    def handoff_get(task_id: str, from_agent: str, to_agent: str) -> str:
        """Get a specific handoff by task ID and agents."""
        try:
            evidence_dir = Path(__file__).parent.parent.parent / "evidence"
            # BUG-240-HND-001: Whitelist sanitize to prevent path traversal (matches handoff_complete)
            safe_task = re.sub(r'[^A-Za-z0-9_\-]', '_', task_id)
            safe_from = re.sub(r'[^A-Za-z0-9_\-]', '_', from_agent.upper())
            safe_to = re.sub(r'[^A-Za-z0-9_\-]', '_', to_agent.upper())
            filename = f"HANDOFF-{safe_task}-{safe_from}-{safe_to}.md"
            filepath = evidence_dir / filename

            if not filepath.exists():
                return format_mcp_result({"error": f"Handoff not found: {filename}"})

            handoff = read_handoff_evidence(filepath)
            if not handoff:
                return format_mcp_result({"error": "Failed to parse handoff file"})

            return format_mcp_result({
                "handoff": handoff.to_dict(),
                "evidence_file": str(filepath)
            })

        except Exception as e:
            # BUG-361-HND-001: Log full error but return only type name
            logger.error(f"handoff_get failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"handoff_get failed: {type(e).__name__}"})

    @mcp.tool()
    def handoff_route(task_id: str) -> str:
        """Determine which agent role should handle a task. Per AGENT-WORKSPACES.md."""
        try:
            task_upper = task_id.upper()
            if task_upper.startswith("RD-"):
                return format_mcp_result({
                    "task_id": task_id,
                    "recommended_agent": "RESEARCH",
                    "reason": "R&D tasks require exploration and analysis"
                })

            if task_upper.startswith("GAP-UI"):
                return format_mcp_result({"task_id": task_id, "recommended_agent": "CODING",
                                   "reason": "UI gaps typically require code implementation"})
            if task_upper.startswith("GAP-MCP"):
                return format_mcp_result({"task_id": task_id, "recommended_agent": "CODING",
                                   "reason": "MCP gaps require tool implementation"})
            if task_upper.startswith("GAP-DATA"):
                return format_mcp_result({"task_id": task_id, "recommended_agent": "CURATOR",
                                   "reason": "Data gaps require validation and governance"})
            if task_upper.startswith("P"):
                match = re.match(r"P(\d+)", task_upper)
                if match and int(match.group(1)) >= 12:
                    return format_mcp_result({"task_id": task_id, "recommended_agent": "CURATOR",
                                       "reason": "Orchestration phase requires governance oversight"})
            return format_mcp_result({"task_id": task_id, "recommended_agent": "RESEARCH",
                               "reason": "Default: Start with research to gather context"})

        except Exception as e:
            # BUG-361-HND-001: Log full error but return only type name
            logger.error(f"handoff_route failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"handoff_route failed: {type(e).__name__}"})
