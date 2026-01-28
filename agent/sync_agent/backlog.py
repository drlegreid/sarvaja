"""
Task Backlog Agent.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: agent/sync_agent.py

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing

Created: 2026-01-04
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable

import httpx

from .models import TaskExecution


class TaskBacklogAgent:
    """
    Agent that picks up and executes tasks from the governance backlog.

    Per RULE-011: Multi-Agent Governance - agents operate with trust scores
    Per RULE-014: Autonomous Task Sequencing - HALT on STOP commands

    Usage:
        agent = TaskBacklogAgent(agent_id="sync-agent-001")
        await agent.run_loop()  # Continuous task pickup and execution

    Or single execution:
        task = await agent.claim_next_task()
        if task:
            result = await agent.execute_task(task)
            await agent.complete_task(result)
    """

    def __init__(
        self,
        agent_id: str,
        api_base_url: str = "http://localhost:8082",
        task_handler: Optional[Callable[[dict], TaskExecution]] = None,
        poll_interval: int = 30,
    ):
        self.agent_id = agent_id
        self.api_base_url = api_base_url
        self.task_handler = task_handler or self._default_handler
        self.poll_interval = poll_interval
        self.running = False
        self.current_task: Optional[dict] = None
        self.tasks_completed = 0
        self.tasks_failed = 0

    def _default_handler(self, task: dict) -> TaskExecution:
        """Default task handler - logs task info and marks complete."""
        start_time = datetime.now()
        task_id = task.get("task_id", task.get("id", "unknown"))

        # Simulate processing
        evidence = f"Task {task_id} processed by {self.agent_id} at {start_time.isoformat()}"
        evidence += f"\nDescription: {task.get('description', 'N/A')}"
        evidence += f"\nPhase: {task.get('phase', 'N/A')}"

        # Check for linked rules
        linked_rules = task.get("linked_rules", [])
        if linked_rules:
            evidence += f"\nLinked rules: {', '.join(linked_rules)}"

        duration = (datetime.now() - start_time).total_seconds()

        return TaskExecution(
            task_id=task_id,
            success=True,
            evidence=evidence,
            duration_seconds=duration,
            rules_applied=linked_rules
        )

    async def get_available_tasks(self) -> list[dict]:
        """Fetch available tasks from the backlog API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_base_url}/api/tasks/available")
                if response.status_code == 200:
                    return response.json()
                return []
        except Exception as e:
            print(f"[{self.agent_id}] Error fetching tasks: {e}")
            return []

    async def claim_task(self, task_id: str) -> Optional[dict]:
        """Claim a specific task."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.api_base_url}/api/tasks/{task_id}/claim",
                    params={"agent_id": self.agent_id}
                )
                if response.status_code == 200:
                    self.current_task = response.json()
                    print(f"[{self.agent_id}] Claimed task: {task_id}")
                    return self.current_task
                else:
                    print(f"[{self.agent_id}] Failed to claim {task_id}: {response.text}")
                    return None
        except Exception as e:
            print(f"[{self.agent_id}] Error claiming task: {e}")
            return None

    async def claim_next_task(self) -> Optional[dict]:
        """Claim the next available task."""
        tasks = await self.get_available_tasks()
        if not tasks:
            return None

        # Try to claim the first available task
        for task in tasks:
            task_id = task.get("task_id", task.get("id"))
            claimed = await self.claim_task(task_id)
            if claimed:
                return claimed

        return None

    async def complete_task(self, execution: TaskExecution) -> bool:
        """Complete a task with evidence."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.api_base_url}/api/tasks/{execution.task_id}/complete",
                    params={"evidence": execution.evidence}
                )
                if response.status_code == 200:
                    self.current_task = None
                    self.tasks_completed += 1
                    print(f"[{self.agent_id}] Completed task: {execution.task_id}")
                    return True
                else:
                    print(f"[{self.agent_id}] Failed to complete {execution.task_id}: {response.text}")
                    return False
        except Exception as e:
            print(f"[{self.agent_id}] Error completing task: {e}")
            return False

    async def execute_task(self, task: dict) -> TaskExecution:
        """Execute a task using the registered handler."""
        task_id = task.get("task_id", task.get("id", "unknown"))

        try:
            # Call the task handler
            result = self.task_handler(task)
            return result
        except Exception as e:
            self.tasks_failed += 1
            return TaskExecution(
                task_id=task_id,
                success=False,
                evidence=f"Task execution failed: {str(e)}",
                duration_seconds=0,
                error=str(e)
            )

    async def process_one_task(self) -> bool:
        """Process a single task from the backlog. Returns True if task was processed."""
        task = await self.claim_next_task()
        if not task:
            return False

        execution = await self.execute_task(task)
        await self.complete_task(execution)
        return True

    async def run_loop(self, max_tasks: Optional[int] = None):
        """
        Run the agent in a continuous loop, picking up and executing tasks.

        Args:
            max_tasks: Optional limit on tasks to process (None = unlimited)
        """
        self.running = True
        tasks_processed = 0

        print(f"[{self.agent_id}] Starting task backlog agent (poll interval: {self.poll_interval}s)")

        while self.running:
            if max_tasks and tasks_processed >= max_tasks:
                print(f"[{self.agent_id}] Reached max tasks limit ({max_tasks})")
                break

            processed = await self.process_one_task()
            if processed:
                tasks_processed += 1
            else:
                # No tasks available, wait before polling again
                await asyncio.sleep(self.poll_interval)

        print(f"[{self.agent_id}] Agent stopped. Completed: {self.tasks_completed}, Failed: {self.tasks_failed}")

    def stop(self):
        """Stop the agent loop."""
        self.running = False
        print(f"[{self.agent_id}] Stop requested")

    def get_stats(self) -> dict:
        """Get agent statistics."""
        return {
            "agent_id": self.agent_id,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "current_task": self.current_task.get("task_id") if self.current_task else None,
            "running": self.running,
        }


__all__ = ['TaskBacklogAgent']
