"""
Sync Agent Orchestrator.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: agent/sync_agent.py

Created: 2026-01-04
"""

import asyncio
from datetime import datetime
from typing import Optional

from .models import Change, SyncResult
from .transports import (
    SyncTransport,
    LocalFileTransport,
    GitTransport,
    ClearMLTransport,
)
from .resolver import ConflictResolver


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


__all__ = ['SyncAgent']
