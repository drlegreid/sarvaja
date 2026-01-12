"""
Sync Transport Implementations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: agent/sync_agent.py

Created: 2026-01-04
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from .models import Change


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


__all__ = [
    'SyncTransport',
    'GitTransport',
    'ClearMLTransport',
    'LocalFileTransport',
]
