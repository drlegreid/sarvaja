"""
Task Handoff MCP Tools.

Per AGENT-WORKSPACES.md Phase 4: Delegation Protocol.
Per RULE-011: Multi-Agent Governance Protocol.

Provides MCP tools for creating, querying, and managing task handoffs
between agent workspaces.
"""

import json
from typing import Optional
from pathlib import Path

from governance.orchestrator.handoff import (
    create_handoff,
    write_handoff_evidence,
    read_handoff_evidence,
    get_pending_handoffs,
    TaskHandoff,
    HandoffStatus,
)


def register_handoff_tools(mcp) -> None:
    """Register handoff MCP tools."""

    @mcp.tool()
    def governance_create_handoff(
        task_id: str,
        title: str,
        from_agent: str,
        to_agent: str,
        context_summary: str,
        recommended_action: str,
        files_examined: Optional[str] = None,
        evidence_gathered: Optional[str] = None,
        action_steps: Optional[str] = None,
        linked_rules: Optional[str] = None,
        constraints: Optional[str] = None,
        priority: str = "MEDIUM",
        source_session_id: Optional[str] = None,
    ) -> str:
        """
        Create a task handoff for delegation to another agent workspace.

        Per AGENT-WORKSPACES.md: Tasks flow between workspaces via evidence files.

        Args:
            task_id: Task ID (e.g., "GAP-UI-005")
            title: Handoff title
            from_agent: Source agent role (RESEARCH, CODING, CURATOR, SYNC)
            to_agent: Target agent role
            context_summary: Brief summary of findings
            recommended_action: What the target agent should do
            files_examined: Pipe-separated list of files examined
            evidence_gathered: Pipe-separated list of evidence items
            action_steps: Pipe-separated list of action steps
            linked_rules: Comma-separated list of rule IDs
            constraints: Pipe-separated list of constraints
            priority: Task priority (LOW, MEDIUM, HIGH, CRITICAL)
            source_session_id: Source session ID for traceability

        Returns:
            JSON with handoff details and evidence file path
        """
        try:
            # Parse pipe-separated lists
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

            # Write evidence file
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
    def governance_get_pending_handoffs(
        for_agent: Optional[str] = None
    ) -> str:
        """
        Get pending task handoffs, optionally filtered by target agent.

        Args:
            for_agent: Filter by target agent role (RESEARCH, CODING, CURATOR, SYNC)

        Returns:
            JSON array of pending handoffs
        """
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
    def governance_complete_handoff(
        task_id: str,
        from_agent: str,
        to_agent: str,
        completion_notes: Optional[str] = None
    ) -> str:
        """
        Mark a handoff as completed.

        Args:
            task_id: Task ID of the handoff
            from_agent: Original source agent
            to_agent: Original target agent (who completed the work)
            completion_notes: Optional completion notes

        Returns:
            JSON with completion status
        """
        try:
            evidence_dir = Path(__file__).parent.parent.parent / "evidence"
            filename = f"HANDOFF-{task_id}-{from_agent.upper()}-{to_agent.upper()}.md"
            filepath = evidence_dir / filename

            if not filepath.exists():
                return json.dumps({"error": f"Handoff not found: {filename}"})

            handoff = read_handoff_evidence(filepath)
            if not handoff:
                return json.dumps({"error": "Failed to parse handoff file"})

            # Update status
            handoff.status = HandoffStatus.COMPLETED.value

            # Append completion notes if provided
            if completion_notes:
                handoff.evidence_gathered.append(f"Completion: {completion_notes}")

            # Write updated handoff
            write_handoff_evidence(handoff, evidence_dir)

            return json.dumps({
                "status": "completed",
                "task_id": task_id,
                "message": f"Handoff marked as completed by {to_agent} agent"
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def governance_get_handoff(
        task_id: str,
        from_agent: str,
        to_agent: str
    ) -> str:
        """
        Get a specific handoff by task ID and agents.

        Args:
            task_id: Task ID of the handoff
            from_agent: Source agent role
            to_agent: Target agent role

        Returns:
            JSON with handoff details or error
        """
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
    def governance_route_task_to_agent(task_id: str) -> str:
        """
        Determine which agent role should handle a task.

        Uses task type, priority, and phase to route to appropriate agent.
        Per AGENT-WORKSPACES.md: Task routing by role.

        Args:
            task_id: Task ID (e.g., "GAP-UI-005", "P12.1", "RD-001")

        Returns:
            JSON with recommended agent and reasoning
        """
        try:
            # Routing rules based on task ID patterns
            task_upper = task_id.upper()

            # R&D tasks -> RESEARCH
            if task_upper.startswith("RD-"):
                return json.dumps({
                    "task_id": task_id,
                    "recommended_agent": "RESEARCH",
                    "reason": "R&D tasks require exploration and analysis"
                }, indent=2)

            # GAP-UI tasks -> CODING (implementation)
            if task_upper.startswith("GAP-UI"):
                return json.dumps({
                    "task_id": task_id,
                    "recommended_agent": "CODING",
                    "reason": "UI gaps typically require code implementation"
                }, indent=2)

            # GAP-MCP tasks -> CODING (API implementation)
            if task_upper.startswith("GAP-MCP"):
                return json.dumps({
                    "task_id": task_id,
                    "recommended_agent": "CODING",
                    "reason": "MCP gaps require tool implementation"
                }, indent=2)

            # GAP-DATA tasks -> CURATOR (data integrity)
            if task_upper.startswith("GAP-DATA"):
                return json.dumps({
                    "task_id": task_id,
                    "recommended_agent": "CURATOR",
                    "reason": "Data gaps require validation and governance"
                }, indent=2)

            # Phase tasks -> based on phase number
            if task_upper.startswith("P"):
                # Extract phase number
                import re
                match = re.match(r"P(\d+)", task_upper)
                if match:
                    phase = int(match.group(1))
                    if phase >= 12:
                        # Later phases are orchestration
                        return json.dumps({
                            "task_id": task_id,
                            "recommended_agent": "CURATOR",
                            "reason": "Orchestration phase requires governance oversight"
                        }, indent=2)

            # Default: RESEARCH for exploration
            return json.dumps({
                "task_id": task_id,
                "recommended_agent": "RESEARCH",
                "reason": "Default: Start with research to gather context"
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})
