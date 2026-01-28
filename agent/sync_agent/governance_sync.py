"""
Governance Sync - TypeDB ↔ Filesystem synchronization.

Per RULE-032: File Size Limit (< 300 lines)
Per GAP-006: Sync Agent implementation

This module provides sync operations between:
- TypeDB (rules, tasks, sessions)
- Filesystem (TODO.md, evidence/, docs/rules/)
- ChromaDB (semantic search, claude-mem)

Created: 2026-01-11
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import httpx


@dataclass
class SyncStatus:
    """Sync divergence status."""
    rules_synced: bool
    tasks_synced: bool
    sessions_synced: bool
    sync_needed: bool
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    tasks_synced: int = 0
    rules_linked: int = 0
    handoffs_processed: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class GovernanceSync:
    """
    Sync operations using governance MCP tools.

    Integrates with:
    - governance_sync_status: Detect TypeDB ↔ filesystem divergence
    - workspace_capture_tasks: Sync tasks from files to TypeDB
    - workspace_link_rules_to_documents: Link rules to markdown files
    - governance_get_pending_handoffs: Process cross-workspace handoffs

    Usage:
        sync = GovernanceSync()
        status = await sync.get_sync_status()
        if status.sync_needed:
            result = await sync.sync_all()
    """

    def __init__(
        self,
        api_base_url: str = "http://localhost:8082",
        timeout: float = 30.0
    ):
        self.api_base_url = api_base_url
        self.timeout = timeout

    async def _call_mcp(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Call governance API endpoint."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.api_base_url}{endpoint}"
                if method == "GET":
                    response = await client.get(url)
                elif method == "POST":
                    response = await client.post(url, json=data)
                elif method == "PUT":
                    response = await client.put(url, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            return {"error": str(e)}

    async def get_sync_status(self) -> SyncStatus:
        """
        Get current sync status between TypeDB and filesystem.

        Uses governance_sync_status MCP tool.
        """
        result = await self._call_mcp("/api/sync/status")

        if "error" in result:
            return SyncStatus(
                rules_synced=False,
                tasks_synced=False,
                sessions_synced=False,
                sync_needed=True,
                details={"error": result["error"]},
                timestamp=datetime.now()
            )

        rules = result.get("rules", {})
        tasks = result.get("tasks", {})
        sessions = result.get("sessions", {})

        return SyncStatus(
            rules_synced=rules.get("synced", False),
            tasks_synced=tasks.get("synced", False),
            sessions_synced=sessions.get("synced", False),
            sync_needed=result.get("sync_needed", True),
            details=result,
            timestamp=datetime.fromisoformat(result.get("timestamp", datetime.now().isoformat()))
        )

    async def capture_tasks(self) -> SyncResult:
        """
        Capture tasks from workspace files to TypeDB.

        Uses workspace_capture_tasks MCP tool.
        """
        result = await self._call_mcp("/api/tasks/capture", method="POST")

        if "error" in result:
            return SyncResult(success=False, errors=[result["error"]])

        return SyncResult(
            success=True,
            tasks_synced=result.get("inserted", 0) + result.get("updated", 0),
            errors=result.get("errors", [])
        )

    async def link_rules_to_documents(self) -> SyncResult:
        """
        Link rules to their markdown source documents.

        Uses workspace_link_rules_to_documents MCP tool.
        """
        result = await self._call_mcp("/api/rules/link-documents", method="POST")

        if "error" in result:
            return SyncResult(success=False, errors=[result["error"]])

        return SyncResult(
            success=True,
            rules_linked=result.get("relations_created", 0),
            errors=result.get("errors", [])
        )

    async def get_pending_handoffs(self, for_agent: str = None) -> List[Dict]:
        """
        Get pending task handoffs for processing.

        Uses governance_get_pending_handoffs MCP tool.
        """
        endpoint = "/api/handoffs/pending"
        if for_agent:
            endpoint += f"?for_agent={for_agent}"

        result = await self._call_mcp(endpoint)

        if "error" in result:
            return []

        return result.get("handoffs", []) if isinstance(result, dict) else result

    async def complete_handoff(
        self,
        task_id: str,
        from_agent: str,
        to_agent: str,
        completion_notes: str = None
    ) -> bool:
        """
        Mark a handoff as completed.

        Uses governance_complete_handoff MCP tool.
        """
        result = await self._call_mcp(
            "/api/handoffs/complete",
            method="POST",
            data={
                "task_id": task_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "completion_notes": completion_notes
            }
        )

        return result.get("success", False) if isinstance(result, dict) else False

    async def sync_all(self) -> SyncResult:
        """
        Perform full synchronization:
        1. Capture tasks from files to TypeDB
        2. Link rules to documents
        3. Process pending handoffs

        Returns combined SyncResult.
        """
        combined = SyncResult(success=True)

        # 1. Capture tasks
        task_result = await self.capture_tasks()
        combined.tasks_synced = task_result.tasks_synced
        combined.errors.extend(task_result.errors)

        # 2. Link rules
        link_result = await self.link_rules_to_documents()
        combined.rules_linked = link_result.rules_linked
        combined.errors.extend(link_result.errors)

        # 3. Count pending handoffs (don't auto-process, just report)
        handoffs = await self.get_pending_handoffs()
        combined.handoffs_processed = len(handoffs)

        # Set overall success
        combined.success = len(combined.errors) == 0

        return combined

    async def run_sync_loop(self, interval: int = 300):
        """
        Run continuous sync loop.

        Args:
            interval: Seconds between sync cycles (default: 5 minutes)
        """
        print(f"[GovernanceSync] Starting sync loop (interval: {interval}s)")

        while True:
            try:
                status = await self.get_sync_status()

                if status.sync_needed:
                    print("[GovernanceSync] Sync needed, running sync_all...")
                    result = await self.sync_all()
                    print(f"[GovernanceSync] Synced: tasks={result.tasks_synced}, rules={result.rules_linked}, handoffs={result.handoffs_processed}")

                    if result.errors:
                        for error in result.errors:
                            print(f"[GovernanceSync] Error: {error}")
                else:
                    print(f"[GovernanceSync] Already synced at {status.timestamp}")

            except Exception as e:
                print(f"[GovernanceSync] Sync error: {e}")

            await asyncio.sleep(interval)


__all__ = ['GovernanceSync', 'SyncStatus', 'SyncResult']
