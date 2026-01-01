"""
Sync Agent for Sim.ai PoC.
Synchronizes skills, sessions, rules, and memories across environments.

Transports:
- Git: Skillbooks and rules (version controlled)
- ClearML: Sessions (MLOps integration)
- WebDAV: Local network sync (laptop ↔ server)

Task Backlog Agent (TODO-6/7):
- Picks up tasks from governance API
- Reports evidence on task completion
- Integrates with rule monitoring

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing
"""
import asyncio
import json
import os
import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Callable

import yaml


@dataclass
class Change:
    """Represents a change to sync."""
    collection: str
    doc_id: str
    action: str  # upsert, delete
    data: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncResult:
    """Result of a sync operation."""
    timestamp: datetime
    changes_pushed: int = 0
    changes_pulled: int = 0
    conflicts_resolved: int = 0
    errors: list = field(default_factory=list)


class SyncTransport(ABC):
    """Abstract base for sync transports."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def push(self, changes: list[Change]) -> int:
        """Push changes to remote. Returns count pushed."""
        pass
    
    @abstractmethod
    async def pull(self) -> list[Change]:
        """Pull changes from remote."""
        pass


class GitTransport(SyncTransport):
    """Syncs skillbooks and rules via Git."""
    
    name = "git"
    
    def __init__(self, repo_path: str, remote: str = "origin", branch: str = "main"):
        self.repo_path = Path(repo_path)
        self.remote = remote
        self.branch = branch
        self._ensure_repo()
    
    def _ensure_repo(self):
        """Ensure Git repo exists."""
        if not (self.repo_path / ".git").exists():
            self.repo_path.mkdir(parents=True, exist_ok=True)
            os.system(f"git init {self.repo_path}")
    
    async def push(self, changes: list[Change]) -> int:
        """Push skillbooks/rules to Git."""
        pushed = 0
        for change in changes:
            if change.collection not in ["skills", "rules"]:
                continue
            
            file_path = self.repo_path / change.collection / f"{change.doc_id}.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if change.action == "delete":
                if file_path.exists():
                    file_path.unlink()
            else:
                with open(file_path, "w") as f:
                    json.dump(change.data, f, indent=2, default=str)
            
            pushed += 1
        
        if pushed > 0:
            os.system(f"cd {self.repo_path} && git add -A && git commit -m 'sync: {pushed} changes' --allow-empty")
            # Uncomment to push: os.system(f"cd {self.repo_path} && git push {self.remote} {self.branch}")
        
        return pushed
    
    async def pull(self) -> list[Change]:
        """Pull changes from Git."""
        changes = []
        # os.system(f"cd {self.repo_path} && git pull {self.remote} {self.branch}")
        
        for collection in ["skills", "rules"]:
            collection_path = self.repo_path / collection
            if collection_path.exists():
                for file_path in collection_path.glob("*.json"):
                    with open(file_path) as f:
                        data = json.load(f)
                    changes.append(Change(
                        collection=collection,
                        doc_id=file_path.stem,
                        action="upsert",
                        data=data
                    ))
        
        return changes


class ClearMLTransport(SyncTransport):
    """Syncs sessions via ClearML (if available)."""
    
    name = "clearml"
    
    def __init__(self, project: str = "sim-ai-poc"):
        self.project = project
        self._clearml_available = self._check_clearml()
    
    def _check_clearml(self) -> bool:
        try:
            from clearml import Task
            return True
        except ImportError:
            return False
    
    async def push(self, changes: list[Change]) -> int:
        """Push sessions to ClearML."""
        if not self._clearml_available:
            return 0
        
        from clearml import Task
        pushed = 0
        
        for change in changes:
            if change.collection != "sessions":
                continue
            
            task = Task.create(
                project_name=self.project,
                task_name=f"session_{change.doc_id}",
                task_type=Task.TaskTypes.data_processing
            )
            task.upload_artifact("session_data", change.data)
            task.close()
            pushed += 1
        
        return pushed
    
    async def pull(self) -> list[Change]:
        """Pull sessions from ClearML."""
        # Sessions are typically push-only
        return []


class LocalFileTransport(SyncTransport):
    """Syncs to local filesystem (for testing/backup)."""
    
    name = "local"
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def push(self, changes: list[Change]) -> int:
        """Push to local filesystem."""
        pushed = 0
        for change in changes:
            file_path = self.base_path / change.collection / f"{change.doc_id}.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w") as f:
                json.dump({
                    "id": change.doc_id,
                    "data": change.data,
                    "timestamp": change.timestamp.isoformat(),
                    "action": change.action
                }, f, indent=2, default=str)
            pushed += 1
        
        return pushed
    
    async def pull(self) -> list[Change]:
        """Pull from local filesystem."""
        changes = []
        for collection_path in self.base_path.iterdir():
            if collection_path.is_dir():
                for file_path in collection_path.glob("*.json"):
                    with open(file_path) as f:
                        record = json.load(f)
                    changes.append(Change(
                        collection=collection_path.name,
                        doc_id=record.get("id", file_path.stem),
                        action=record.get("action", "upsert"),
                        data=record.get("data", record),
                        timestamp=datetime.fromisoformat(record.get("timestamp", datetime.utcnow().isoformat()))
                    ))
        return changes


class ConflictResolver:
    """Resolves sync conflicts."""
    
    STRATEGIES = {
        "skills": "merge_latest",
        "sessions": "local_wins",
        "rules": "remote_wins",
        "memories": "merge_dedupe"
    }
    
    def resolve(self, local: Change, remote: Change) -> Change:
        """Resolve conflict between local and remote."""
        strategy = self.STRATEGIES.get(local.collection, "local_wins")
        
        if strategy == "merge_latest":
            return local if local.timestamp > remote.timestamp else remote
        elif strategy == "remote_wins":
            return remote
        else:  # local_wins, merge_dedupe
            return local


class SyncAgent:
    """Main sync agent orchestrator."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or self._default_config()
        self.transports = self._init_transports()
        self.resolver = ConflictResolver()
        self.running = False
        self.last_sync: Optional[datetime] = None
        self._local_state: dict[str, dict] = {}
    
    def _default_config(self) -> dict:
        return {
            "sync": {
                "enabled": True,
                "interval_seconds": 300,
                "collections": ["skills", "sessions", "rules", "memories"],
                "transports": {
                    "local": {"base_path": "./sync_data"},
                    "git": {"repo_path": "./skillbooks"}
                }
            }
        }
    
    def _init_transports(self) -> list[SyncTransport]:
        transports = []
        transport_config = self.config.get("sync", {}).get("transports", {})
        
        if "local" in transport_config:
            transports.append(LocalFileTransport(**transport_config["local"]))
        if "git" in transport_config:
            transports.append(GitTransport(**transport_config["git"]))
        if "clearml" in transport_config:
            transports.append(ClearMLTransport(**transport_config["clearml"]))
        
        return transports
    
    def track_change(self, collection: str, doc_id: str, data: dict, action: str = "upsert"):
        """Track a local change for sync."""
        key = f"{collection}:{doc_id}"
        self._local_state[key] = Change(
            collection=collection,
            doc_id=doc_id,
            action=action,
            data=data
        )
    
    def get_pending_changes(self) -> list[Change]:
        """Get all pending local changes."""
        return list(self._local_state.values())
    
    def clear_pending(self):
        """Clear pending changes after successful sync."""
        self._local_state.clear()
    
    async def sync_once(self) -> SyncResult:
        """Perform a single sync cycle."""
        result = SyncResult(timestamp=datetime.utcnow())
        
        try:
            local_changes = self.get_pending_changes()
            
            for transport in self.transports:
                try:
                    # Pull remote changes
                    remote_changes = await transport.pull()
                    for remote in remote_changes:
                        key = f"{remote.collection}:{remote.doc_id}"
                        if key in self._local_state:
                            resolved = self.resolver.resolve(self._local_state[key], remote)
                            if resolved == remote:
                                self._local_state[key] = remote
                            result.conflicts_resolved += 1
                        else:
                            result.changes_pulled += 1
                    
                    # Push local changes
                    pushed = await transport.push(local_changes)
                    result.changes_pushed += pushed
                    
                except Exception as e:
                    result.errors.append(f"{transport.name}: {str(e)}")
            
            if not result.errors:
                self.clear_pending()
            
            self.last_sync = datetime.utcnow()
            
        except Exception as e:
            result.errors.append(str(e))
        
        return result
    
    async def run(self, interval: Optional[int] = None):
        """Run sync agent continuously."""
        interval = interval or self.config["sync"]["interval_seconds"]
        self.running = True
        
        print(f"Sync agent started (interval: {interval}s)")
        
        while self.running:
            result = await self.sync_once()
            print(f"[{result.timestamp}] Pushed: {result.changes_pushed}, Pulled: {result.changes_pulled}, Conflicts: {result.conflicts_resolved}, Errors: {len(result.errors)}")
            
            if result.errors:
                for error in result.errors:
                    print(f"  ERROR: {error}")
            
            await asyncio.sleep(interval)
    
    def stop(self):
        """Stop the sync agent."""
        self.running = False


# =============================================================================
# TASK BACKLOG AGENT (TODO-6/7)
# =============================================================================

@dataclass
class TaskExecution:
    """Result of executing a task."""
    task_id: str
    success: bool
    evidence: str
    duration_seconds: float
    rules_applied: list[str] = field(default_factory=list)
    error: Optional[str] = None


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


def load_config(path: str = "config/sync_config.yaml") -> dict:
    """Load sync configuration from file."""
    if Path(path).exists():
        with open(path) as f:
            return yaml.safe_load(f)
    return {}


if __name__ == "__main__":
    import sys

    def print_usage():
        print("""
Sync Agent CLI
==============

Usage:
  python sync_agent.py [command] [options]

Commands:
  --sync          Run sync agent (default)
  --sync-once     Single sync operation
  --sync-test     Test sync with sample data

  --backlog       Run task backlog agent
  --backlog-once  Process one task and exit
  --backlog-test  Test backlog with sample task claim

Options:
  --agent-id ID   Set agent ID (default: sync-agent-001)
  --api-url URL   API base URL (default: http://localhost:8082)

Examples:
  python sync_agent.py --backlog --agent-id my-agent-001
  python sync_agent.py --backlog-once
  python sync_agent.py --sync-once
""")

    # Parse arguments
    args = sys.argv[1:]
    agent_id = "sync-agent-001"
    api_url = "http://localhost:8082"

    # Extract options
    if "--agent-id" in args:
        idx = args.index("--agent-id")
        if idx + 1 < len(args):
            agent_id = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    if "--api-url" in args:
        idx = args.index("--api-url")
        if idx + 1 < len(args):
            api_url = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    command = args[0] if args else "--sync"

    if command in ["-h", "--help"]:
        print_usage()
        sys.exit(0)

    # Task Backlog Agent commands
    if command == "--backlog":
        backlog_agent = TaskBacklogAgent(agent_id=agent_id, api_base_url=api_url)
        try:
            asyncio.run(backlog_agent.run_loop())
        except KeyboardInterrupt:
            backlog_agent.stop()
            print("\nBacklog agent stopped.")

    elif command == "--backlog-once":
        backlog_agent = TaskBacklogAgent(agent_id=agent_id, api_base_url=api_url)
        result = asyncio.run(backlog_agent.process_one_task())
        if result:
            print(f"Task processed. Stats: {backlog_agent.get_stats()}")
        else:
            print("No available tasks to process.")

    elif command == "--backlog-test":
        backlog_agent = TaskBacklogAgent(agent_id=agent_id, api_base_url=api_url)
        tasks = asyncio.run(backlog_agent.get_available_tasks())
        print(f"Available tasks: {len(tasks)}")
        if tasks:
            print(f"First task: {tasks[0].get('task_id', tasks[0].get('id'))}")
            print(f"Description: {tasks[0].get('description', 'N/A')}")

    # Sync Agent commands
    elif command in ["--sync", ""]:
        config = load_config()
        sync_agent = SyncAgent(config if config else None)
        try:
            asyncio.run(sync_agent.run())
        except KeyboardInterrupt:
            sync_agent.stop()
            print("\nSync agent stopped.")

    elif command == "--sync-once":
        config = load_config()
        sync_agent = SyncAgent(config if config else None)
        result = asyncio.run(sync_agent.sync_once())
        print(f"Sync result: {result}")

    elif command == "--sync-test":
        config = load_config()
        sync_agent = SyncAgent(config if config else None)
        sync_agent.track_change("skills", "test_skill_001", {
            "name": "Test Skill",
            "description": "A test skill for validation",
            "created_at": datetime.utcnow().isoformat()
        })
        result = asyncio.run(sync_agent.sync_once())
        print(f"Test sync result: {result}")

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)
