"""Session Capture Methods. Per RULE-032: Modularized from session_collector.py."""

from datetime import datetime, date
from typing import Dict, Any

from .models import SessionEvent, Task, Decision, SessionIntent, SessionOutcome, TYPEDB_AVAILABLE
from typing import List, Optional

class SessionCaptureMixin:
    """Mixin providing capture methods for SessionCollector. Requires session_id, events, decisions, tasks."""

    def capture_prompt(self, prompt: str, metadata: Dict[str, Any] = None) -> None:
        """Capture user prompt."""
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="prompt",
            content=prompt,
            metadata={
                "session_id": self.session_id,
                **(metadata or {})
            }
        ))

    def capture_response(self, response: str, metadata: Dict[str, Any] = None) -> None:
        """Capture assistant response."""
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="response",
            content=response,
            metadata={
                "session_id": self.session_id,
                **(metadata or {})
            }
        ))

    def capture_decision(self, decision_id: str, name: str, context: str,
                         rationale: str, status: str = "active") -> Decision:
        """Capture strategic decision."""
        decision = Decision(
            id=decision_id,
            name=name,
            context=context,
            rationale=rationale,
            status=status,
            decision_date=datetime.now()
        )
        self.decisions.append(decision)

        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="decision",
            content=f"{decision_id}: {name}",
            metadata={"decision_id": decision_id, "rationale": rationale}
        ))
        if TYPEDB_AVAILABLE:
            self._index_decision_to_typedb(decision)

        return decision

    def capture_task(self, task_id: str, name: str, description: str,
                     status: str = "pending", priority: str = "MEDIUM") -> Task:
        """Capture task for tracking."""
        task = Task(
            id=task_id,
            name=name,
            description=description,
            status=status,
            priority=priority,
            created_date=date.today().isoformat()
        )
        self.tasks.append(task)

        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="task",
            content=f"{task_id}: {name}",
            metadata={"task_id": task_id, "status": status, "priority": priority}
        ))
        if TYPEDB_AVAILABLE:
            self._index_task_to_typedb(task)

        return task

    def capture_error(self, error: str, context: str = None) -> None:
        """Capture error event."""
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="error",
            content=error,
            metadata={"session_id": self.session_id, "context": context}
        ))

    def capture_tool_call(self, tool_name: str, arguments: Dict[str, Any] = None,
                          result: str = None, duration_ms: int = None, success: bool = True,
                          correlation_id: str = None, applied_rules: List[str] = None) -> None:
        """Capture MCP tool call event. Per Task 2.3, RD-DEBUG-AUDIT."""
        result_summary = result[:500] + "..." if result and len(result) > 500 else result

        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="tool_call",
            content=f"{tool_name}({', '.join(f'{k}={v}' for k, v in (arguments or {}).items())[:100]})",
            metadata={
                "session_id": self.session_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "result_summary": result_summary,
                "duration_ms": duration_ms,
                "success": success,
                "correlation_id": correlation_id,
                "applied_rules": applied_rules or []
            }
        ))

    def capture_thought(self, thought: str, thought_type: str = "reasoning",
                        related_tools: Optional[List[str]] = None, confidence: float = None) -> None:
        """Capture assistant thought/reasoning event. Per Task 2.3."""
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="thought",
            content=thought,
            metadata={
                "session_id": self.session_id,
                "thought_type": thought_type,
                "related_tools": related_tools or [],
                "confidence": confidence
            }
        ))

    def capture_intent(self, goal: str, source: str, planned_tasks: Optional[List[str]] = None,
                       previous_session_id: Optional[str] = None,
                       initial_prompt: Optional[str] = None) -> SessionIntent:
        """Capture session intent at start. Per RD-INTENT, SESSION-PROMPT-01-v1."""
        intent = SessionIntent(
            goal=goal,
            source=source,
            planned_tasks=planned_tasks or [],
            previous_session_id=previous_session_id,
            initial_prompt=initial_prompt
        )
        self.intent = intent

        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="intent",
            content=f"Intent: {goal}",
            metadata={"source": source, "planned_tasks": planned_tasks or [],
                     "previous_session_id": previous_session_id, "initial_prompt": initial_prompt}
        ))

        return intent

    def capture_outcome(self, status: str, achieved_tasks: Optional[List[str]] = None,
                        deferred_tasks: Optional[List[str]] = None,
                        handoff_items: Optional[List[str]] = None,
                        discoveries: Optional[List[str]] = None) -> SessionOutcome:
        """Capture session outcome at end. Per RD-INTENT."""
        outcome = SessionOutcome(
            status=status,
            achieved_tasks=achieved_tasks or [],
            deferred_tasks=deferred_tasks or [],
            handoff_items=handoff_items or [],
            discoveries=discoveries or []
        )
        self.outcome = outcome

        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="outcome",
            content=f"Outcome: {status}",
            metadata={"achieved_tasks": achieved_tasks or [], "deferred_tasks": deferred_tasks or [],
                     "handoff_items": handoff_items or [], "discoveries": discoveries or []}
        ))

        return outcome
