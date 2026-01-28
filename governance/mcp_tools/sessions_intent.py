"""
Session Intent MCP Tools
========================
Session intent and outcome capture operations.

Per RD-INTENT: Session intent reconciliation for cross-session continuity.
Per RULE-032: File size <300 lines

Extracted from sessions_core.py per modularization plan.
Created: 2026-01-10
"""

from typing import Optional

from governance.mcp_tools.common import format_mcp_result

# Monitoring instrumentation per GAP-MONITOR-INSTRUMENT-001
try:
    from agent.governance_ui.data_access.monitoring import log_monitor_event
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

# Import session collector (with fallback)
try:
    from governance.session_collector import (
        get_or_create_session,
        list_active_sessions,
        SessionIntent,
        SessionOutcome
    )
    SESSION_COLLECTOR_AVAILABLE = True
except ImportError:
    SESSION_COLLECTOR_AVAILABLE = False


def register_session_intent_tools(mcp) -> None:
    """Register session intent MCP tools."""

    @mcp.tool()
    def session_capture_intent(
        goal: str,
        source: str,
        planned_tasks: Optional[str] = None,
        previous_session_id: Optional[str] = None,
        initial_prompt: Optional[str] = None,
        topic: Optional[str] = None
    ) -> str:
        """
        Capture session intent at start.

        Per RD-INTENT: Record what the session intends to accomplish.
        Per SESSION-PROMPT-01-v1: Initial prompt must be captured verbatim.
        Call this at session start to enable reconciliation tracking.

        Args:
            goal: Primary goal for the session
            source: Where the goal came from ("TODO.md", "User request", "Handoff from SESSION-XXX")
            planned_tasks: Comma-separated task IDs planned for this session (e.g., "P12.1,P12.2")
            previous_session_id: Link to previous session for continuity tracking
            initial_prompt: Verbatim copy of user's first message that started the session
            topic: Session topic (uses last session if not provided)

        Returns:
            JSON object with intent confirmation
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        # Get or create session
        sessions = list_active_sessions()
        if not sessions and not topic:
            return format_mcp_result({"error": "No active session. Call session_start first."})

        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

        # Parse comma-separated task IDs
        task_list = []
        if planned_tasks:
            task_list = [t.strip() for t in planned_tasks.split(",") if t.strip()]

        intent = collector.capture_intent(
            goal=goal,
            source=source,
            planned_tasks=task_list,
            previous_session_id=previous_session_id,
            initial_prompt=initial_prompt
        )

        # Instrument intent capture
        if MONITORING_AVAILABLE:
            log_monitor_event(
                event_type="session_event",
                source="mcp-session-capture-intent",
                details={"session_id": collector.session_id, "action": "capture_intent", "tasks_planned": len(task_list)}
            )

        return format_mcp_result({
            "session_id": collector.session_id,
            "goal": goal,
            "source": source,
            "planned_tasks": task_list,
            "previous_session_id": previous_session_id,
            "initial_prompt": initial_prompt[:200] + "..." if initial_prompt and len(initial_prompt) > 200 else initial_prompt,
            "captured_at": intent.captured_at,
            "message": f"Intent captured for {collector.session_id}"
        })

    @mcp.tool()
    def session_capture_outcome(
        status: str,
        achieved_tasks: Optional[str] = None,
        deferred_tasks: Optional[str] = None,
        handoff_items: Optional[str] = None,
        discoveries: Optional[str] = None,
        topic: Optional[str] = None
    ) -> str:
        """
        Capture session outcome at end.

        Per RD-INTENT: Record what the session accomplished.
        Call this before session_end for reconciliation tracking.

        Args:
            status: Outcome status (COMPLETE, PARTIAL, ABANDONED, DEFERRED)
            achieved_tasks: Comma-separated task IDs completed in this session
            deferred_tasks: Comma-separated task IDs deferred
            handoff_items: Pipe-separated items for next session to pick up
            discoveries: Pipe-separated new gaps, R&D items discovered
            topic: Session topic (uses last session if not provided)

        Returns:
            JSON object with outcome confirmation
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        # Get or create session
        sessions = list_active_sessions()
        if not sessions and not topic:
            return format_mcp_result({"error": "No active session. Call session_start first."})

        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

        # Parse comma-separated task IDs
        achieved_list = []
        if achieved_tasks:
            achieved_list = [t.strip() for t in achieved_tasks.split(",") if t.strip()]

        deferred_list = []
        if deferred_tasks:
            deferred_list = [t.strip() for t in deferred_tasks.split(",") if t.strip()]

        # Parse pipe-separated items (allow longer strings)
        handoff_list = []
        if handoff_items:
            handoff_list = [h.strip() for h in handoff_items.split("|") if h.strip()]

        discoveries_list = []
        if discoveries:
            discoveries_list = [d.strip() for d in discoveries.split("|") if d.strip()]

        outcome = collector.capture_outcome(
            status=status,
            achieved_tasks=achieved_list,
            deferred_tasks=deferred_list,
            handoff_items=handoff_list,
            discoveries=discoveries_list
        )

        # Calculate reconciliation if intent exists
        reconciliation = None
        if collector.intent:
            planned = set(collector.intent.planned_tasks)
            achieved = set(achieved_list)
            deferred = set(deferred_list)

            reconciliation = {
                "planned_count": len(planned),
                "achieved_count": len(achieved),
                "deferred_count": len(deferred),
                "completion_rate": len(achieved) / len(planned) * 100 if planned else 100,
                "untracked_achieved": list(achieved - planned),
                "planned_not_done": list(planned - achieved - deferred)
            }

        # Instrument outcome capture
        if MONITORING_AVAILABLE:
            log_monitor_event(
                event_type="session_event",
                source="mcp-session-capture-outcome",
                details={
                    "session_id": collector.session_id,
                    "action": "capture_outcome",
                    "status": status,
                    "achieved": len(achieved_list),
                    "deferred": len(deferred_list)
                }
            )

        return format_mcp_result({
            "session_id": collector.session_id,
            "status": status,
            "achieved_tasks": achieved_list,
            "deferred_tasks": deferred_list,
            "handoff_items": handoff_list,
            "discoveries": discoveries_list,
            "captured_at": outcome.captured_at,
            "reconciliation": reconciliation,
            "message": f"Outcome captured for {collector.session_id}"
        })
