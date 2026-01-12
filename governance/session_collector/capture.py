"""
Session Capture Methods.

Per RULE-032: Modularized from session_collector.py (591 lines).
Contains: Capture methods for prompts, responses, decisions, tasks, errors.
"""

from datetime import datetime, date
from typing import Dict, Any

from .models import SessionEvent, Task, Decision, SessionIntent, SessionOutcome, TYPEDB_AVAILABLE
from typing import List, Optional


class SessionCaptureMixin:
    """
    Mixin class providing capture methods for SessionCollector.

    Requires the following attributes on the parent class:
    - session_id: str
    - events: List[SessionEvent]
    - decisions: List[Decision]
    - tasks: List[Task]
    """

    def capture_prompt(self, prompt: str, metadata: Dict[str, Any] = None) -> None:
        """
        Capture user prompt.

        Args:
            prompt: User prompt text
            metadata: Additional metadata
        """
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
        """
        Capture assistant response.

        Args:
            response: Assistant response text
            metadata: Additional metadata
        """
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="response",
            content=response,
            metadata={
                "session_id": self.session_id,
                **(metadata or {})
            }
        ))

    def capture_decision(
        self,
        decision_id: str,
        name: str,
        context: str,
        rationale: str,
        status: str = "active"
    ) -> Decision:
        """
        Capture strategic decision.

        Args:
            decision_id: Decision ID (e.g., "DECISION-007")
            name: Decision title
            context: Context/problem statement
            rationale: Reasoning for the decision
            status: Decision status

        Returns:
            Created Decision object
        """
        decision = Decision(
            id=decision_id,
            name=name,
            context=context,
            rationale=rationale,
            status=status,
            decision_date=datetime.now()
        )
        self.decisions.append(decision)

        # Record as event
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="decision",
            content=f"{decision_id}: {name}",
            metadata={
                "decision_id": decision_id,
                "rationale": rationale
            }
        ))

        # Auto-index to TypeDB if available
        if TYPEDB_AVAILABLE:
            self._index_decision_to_typedb(decision)

        return decision

    def capture_task(
        self,
        task_id: str,
        name: str,
        description: str,
        status: str = "pending",
        priority: str = "MEDIUM"
    ) -> Task:
        """
        Capture task for tracking.

        Args:
            task_id: Task ID (e.g., "P4.2", "RD-001")
            name: Task name
            description: Task description
            status: Task status
            priority: Task priority

        Returns:
            Created Task object
        """
        task = Task(
            id=task_id,
            name=name,
            description=description,
            status=status,
            priority=priority,
            created_date=date.today().isoformat()
        )
        self.tasks.append(task)

        # Record as event
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="task",
            content=f"{task_id}: {name}",
            metadata={
                "task_id": task_id,
                "status": status,
                "priority": priority
            }
        ))

        # Auto-index to TypeDB with session link if available
        if TYPEDB_AVAILABLE:
            self._index_task_to_typedb(task)

        return task

    def capture_error(self, error: str, context: str = None) -> None:
        """
        Capture error event.

        Args:
            error: Error message
            context: Error context
        """
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="error",
            content=error,
            metadata={
                "session_id": self.session_id,
                "context": context
            }
        ))

    def capture_intent(
        self,
        goal: str,
        source: str,
        planned_tasks: Optional[List[str]] = None,
        previous_session_id: Optional[str] = None
    ) -> SessionIntent:
        """
        Capture session intent at start.

        Per RD-INTENT: Record what the session intends to accomplish.

        Args:
            goal: Primary goal for the session
            source: Where the goal came from ("TODO.md", "User request", "Handoff from SESSION-XXX")
            planned_tasks: List of task IDs planned for this session
            previous_session_id: Link to previous session for continuity tracking

        Returns:
            Created SessionIntent object
        """
        intent = SessionIntent(
            goal=goal,
            source=source,
            planned_tasks=planned_tasks or [],
            previous_session_id=previous_session_id
        )
        self.intent = intent

        # Record as event
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="intent",
            content=f"Intent: {goal}",
            metadata={
                "source": source,
                "planned_tasks": planned_tasks or [],
                "previous_session_id": previous_session_id
            }
        ))

        return intent

    def capture_outcome(
        self,
        status: str,
        achieved_tasks: Optional[List[str]] = None,
        deferred_tasks: Optional[List[str]] = None,
        handoff_items: Optional[List[str]] = None,
        discoveries: Optional[List[str]] = None
    ) -> SessionOutcome:
        """
        Capture session outcome at end.

        Per RD-INTENT: Record what the session accomplished.

        Args:
            status: Outcome status (COMPLETE, PARTIAL, ABANDONED, DEFERRED)
            achieved_tasks: Task IDs completed in this session
            deferred_tasks: Task IDs deferred (with reasons)
            handoff_items: Items for next session to pick up
            discoveries: New gaps, R&D items discovered during session

        Returns:
            Created SessionOutcome object
        """
        outcome = SessionOutcome(
            status=status,
            achieved_tasks=achieved_tasks or [],
            deferred_tasks=deferred_tasks or [],
            handoff_items=handoff_items or [],
            discoveries=discoveries or []
        )
        self.outcome = outcome

        # Record as event
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="outcome",
            content=f"Outcome: {status}",
            metadata={
                "achieved_tasks": achieved_tasks or [],
                "deferred_tasks": deferred_tasks or [],
                "handoff_items": handoff_items or [],
                "discoveries": discoveries or []
            }
        ))

        return outcome
