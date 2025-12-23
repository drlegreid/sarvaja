"""
Sync Agent for Sim.ai PoC.
Synchronizes skills, sessions, rules, and memories across environments.

Transports:
- Git: Skillbooks and rules (version controlled)
- ClearML: Sessions (MLOps integration)
- WebDAV: Local network sync (laptop ↔ server)
"""
import asyncio
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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


def load_config(path: str = "config/sync_config.yaml") -> dict:
    """Load sync configuration from file."""
    if Path(path).exists():
        with open(path) as f:
            return yaml.safe_load(f)
    return {}


if __name__ == "__main__":
    import sys
    
    config = load_config()
    agent = SyncAgent(config if config else None)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            result = asyncio.run(agent.sync_once())
            print(f"Sync result: {result}")
        elif sys.argv[1] == "--test":
            # Test mode: track some changes and sync
            agent.track_change("skills", "test_skill_001", {
                "name": "Test Skill",
                "description": "A test skill for validation",
                "created_at": datetime.utcnow().isoformat()
            })
            result = asyncio.run(agent.sync_once())
            print(f"Test sync result: {result}")
    else:
        try:
            asyncio.run(agent.run())
        except KeyboardInterrupt:
            agent.stop()
            print("\nSync agent stopped.")
