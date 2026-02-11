"""
Orchestrator Dispatch Logic (Mixin).

Per DOC-SIZE-01-v1: Extracted from engine.py (478 lines).
Task dispatch, completion, agent selection, and constraint validation.
"""

from typing import Any, Dict, List, Optional

from .task_poller import PollableTask, TaskPriority
from .engine_models import AgentInfo, DispatchResult


class OrchestratorDispatchMixin:
    """Mixin providing task dispatch and validation methods.

    Expects host class to provide:
        self._queue: TaskPriorityQueue
        self._poller: TypeDBTaskPoller
        self._agents: Dict[str, AgentInfo]
        self._dispatch_count: int
        self.get_available_agents(role=None) -> List[AgentInfo]
    """

    async def dispatch_next(self) -> DispatchResult:
        """
        Dispatch next task from queue.

        Selects appropriate agent based on:
        - Task priority
        - Agent trust level (RULE-011)
        - Agent availability
        """
        # Get next task
        task = self._queue.pop()
        if not task:
            return DispatchResult(
                success=False,
                message="No tasks in queue",
            )

        # Select agent
        agent = self._select_agent_for_task(task)
        if not agent:
            self._queue.push(task)
            return DispatchResult(
                success=False,
                task_id=task.task_id,
                message="No suitable agent available",
            )

        # Validate with Kanren constraints
        validation = self._validate_assignment(agent, task)
        if not validation["valid"]:
            self._queue.push(task)
            return DispatchResult(
                success=False,
                task_id=task.task_id,
                agent_id=agent.agent_id,
                message=f"Constraint validation failed: {validation.get('reason', 'Unknown')}",
                constraints_checked=validation.get("constraints_checked", []),
            )

        # Claim task
        claimed = await self._poller.claim_task(task.task_id, agent.agent_id)
        if not claimed:
            return DispatchResult(
                success=False,
                task_id=task.task_id,
                agent_id=agent.agent_id,
                message="Failed to claim task (already claimed?)",
            )

        # Update agent status
        agent.status = "BUSY"
        agent.current_task = task.task_id

        self._dispatch_count += 1

        return DispatchResult(
            success=True,
            task_id=task.task_id,
            agent_id=agent.agent_id,
            message="Task dispatched successfully",
            requires_supervisor=validation.get("requires_supervisor", False),
            constraints_checked=validation.get("constraints_checked", []),
        )

    async def complete_task(
        self,
        task_id: str,
        agent_id: str,
        evidence: str = None,
    ) -> bool:
        """Mark task as completed."""
        result = await self._poller.complete_task(task_id, agent_id, evidence)

        if result and agent_id in self._agents:
            agent = self._agents[agent_id]
            agent.status = "AVAILABLE"
            agent.current_task = None
            agent.tasks_completed += 1

        return result

    def _select_agent_for_task(self, task: PollableTask) -> Optional[AgentInfo]:
        """
        Select best agent for task.

        Selection criteria:
        1. Agent must be available
        2. Trust level must match task priority (RULE-011)
        3. Prefer agent with matching role
        4. Prefer agent with fewer completed tasks (load balancing)
        """
        available = self.get_available_agents()
        if not available:
            return None

        # Filter by trust requirement
        min_trust = self._get_min_trust_for_priority(task.priority)
        candidates = [a for a in available if a.trust_score >= min_trust]

        if not candidates:
            return None

        # Sort by: trust (desc) -> tasks_completed (asc)
        candidates.sort(key=lambda a: (-a.trust_score, a.tasks_completed))

        return candidates[0]

    def _get_min_trust_for_priority(self, priority: TaskPriority) -> float:
        """
        Get minimum trust required for task priority.

        Per RULE-011:
        - CRITICAL: 0.7 (trusted/expert)
        - HIGH: 0.5 (supervised and above)
        - MEDIUM/LOW: 0.0 (any)
        """
        trust_map = {
            TaskPriority.CRITICAL: 0.7,
            TaskPriority.HIGH: 0.5,
            TaskPriority.MEDIUM: 0.0,
            TaskPriority.LOW: 0.0,
        }
        return trust_map.get(priority, 0.0)

    def _validate_assignment(
        self,
        agent: AgentInfo,
        task: PollableTask,
    ) -> Dict[str, Any]:
        """Validate task assignment using Kanren constraints."""
        constraints_checked: List[str] = []

        try:
            from governance.kanren_constraints import (
                validate_agent_for_task,
                trust_level,
                requires_supervisor,
            )

            result = validate_agent_for_task(
                agent.agent_id,
                agent.trust_score,
                task.priority.name,
            )

            return {
                "valid": result["valid"],
                "requires_supervisor": result.get("requires_supervisor", False),
                "constraints_checked": result.get("constraints_checked", []),
                "trust_level": result.get("trust_level"),
            }

        except ImportError:
            # Fallback to simple validation
            constraints_checked.append("RULE-011: Trust-based (fallback)")

            min_trust = self._get_min_trust_for_priority(task.priority)
            is_valid = agent.trust_score >= min_trust
            needs_supervisor = agent.trust_score < 0.7

            return {
                "valid": is_valid,
                "requires_supervisor": needs_supervisor,
                "constraints_checked": constraints_checked,
                "reason": None if is_valid else f"Trust {agent.trust_score} < required {min_trust}",
            }
