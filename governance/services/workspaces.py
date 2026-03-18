"""Workspace Service — Real entity CRUD for workspaces.

Completes the chain: Project → **Workspace** → Agent → Capabilities → Tasks → Sessions

A workspace is an organizational context within a project. It defines:
- Which agents operate in it
- Which workspace type governs its defaults (rules, capabilities, MCP servers)
- Where tasks and sessions are created

Backed by in-memory store + disk persistence (same pattern as agent_metrics).
Builds on workspace_registry.py for type definitions.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from governance.stores.audit import record_audit
from governance.services.workspace_registry import (
    get_workspace_type,
    list_workspace_types,
    workspace_type_to_dict,
)

logger = logging.getLogger(__name__)

_WORKSPACES_FILE = "governance/data/workspaces.json"
_workspaces_store: Dict[str, Dict[str, Any]] = {}
_loaded = False


def _load() -> None:
    """Load workspaces from disk."""
    global _loaded
    if _loaded:
        return
    _loaded = True
    if os.path.exists(_WORKSPACES_FILE):
        try:
            with open(_WORKSPACES_FILE) as f:
                data = json.load(f)
            for ws in data:
                _workspaces_store[ws["workspace_id"]] = ws
        except Exception as e:
            logger.warning(f"Failed to load workspaces: {type(e).__name__}", exc_info=True)


def _save() -> None:
    """Persist workspaces to disk."""
    try:
        os.makedirs(os.path.dirname(_WORKSPACES_FILE), exist_ok=True)
        with open(_WORKSPACES_FILE, "w") as f:
            json.dump(list(_workspaces_store.values()), f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save workspaces: {type(e).__name__}", exc_info=True)


def create_workspace(
    name: str,
    workspace_type: str,
    project_id: Optional[str] = None,
    description: Optional[str] = None,
    agent_ids: Optional[List[str]] = None,
    source: str = "service",
) -> Dict[str, Any]:
    """Create a new workspace."""
    _load()
    workspace_id = f"WS-{uuid.uuid4().hex[:8].upper()}"

    # Get defaults from workspace type registry
    wt = get_workspace_type(workspace_type)
    if not wt:
        workspace_type = "generic"
        wt = get_workspace_type("generic")

    ws = {
        "workspace_id": workspace_id,
        "name": name,
        "workspace_type": workspace_type,
        "project_id": project_id,
        "description": description or (wt.description if wt else ""),
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "agent_ids": agent_ids or [],
        "default_rules": wt.default_rules if wt else [],
        "capabilities": wt.capabilities if wt else [],
        "icon": wt.icon if wt else "mdi-folder",
        "color": wt.color if wt else "#64748b",
    }
    _workspaces_store[workspace_id] = ws
    _save()
    record_audit("CREATE", "workspace", workspace_id,
                 metadata={"name": name, "type": workspace_type, "source": source})
    return ws


def get_workspace(workspace_id: str) -> Optional[Dict[str, Any]]:
    """Get a workspace by ID."""
    _load()
    return _workspaces_store.get(workspace_id)


def list_workspaces(
    project_id: Optional[str] = None,
    workspace_type: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """List workspaces with filters and pagination."""
    _load()
    result = list(_workspaces_store.values())
    if project_id:
        result = [w for w in result if w.get("project_id") == project_id]
    if workspace_type:
        result = [w for w in result if w.get("workspace_type") == workspace_type]
    if status:
        result = [w for w in result if w.get("status") == status]
    result.sort(key=lambda w: w.get("created_at", ""), reverse=True)
    total = len(result)
    paginated = result[offset:offset + limit]
    return {
        "items": paginated,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(paginated)) < total,
    }


def update_workspace(
    workspace_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    agent_ids: Optional[List[str]] = None,
    source: str = "service",
) -> Optional[Dict[str, Any]]:
    """Update a workspace."""
    _load()
    ws = _workspaces_store.get(workspace_id)
    if not ws:
        return None
    if name is not None:
        ws["name"] = name
    if description is not None:
        ws["description"] = description
    if status is not None:
        ws["status"] = status
    if agent_ids is not None:
        ws["agent_ids"] = agent_ids
    _save()
    record_audit("UPDATE", "workspace", workspace_id, metadata={"source": source})
    return ws


def delete_workspace(workspace_id: str, source: str = "service") -> bool:
    """Delete a workspace."""
    _load()
    if workspace_id not in _workspaces_store:
        return False
    del _workspaces_store[workspace_id]
    _save()
    record_audit("DELETE", "workspace", workspace_id, metadata={"source": source})
    return True


def assign_agent_to_workspace(
    workspace_id: str,
    agent_id: str,
    source: str = "service",
) -> Optional[Dict[str, Any]]:
    """Assign an agent to a workspace."""
    _load()
    ws = _workspaces_store.get(workspace_id)
    if not ws:
        return None
    if agent_id not in ws.get("agent_ids", []):
        ws.setdefault("agent_ids", []).append(agent_id)
        _save()
        record_audit("UPDATE", "workspace", workspace_id,
                     metadata={"action": "assign_agent", "agent_id": agent_id, "source": source})
    return ws


def remove_agent_from_workspace(
    workspace_id: str,
    agent_id: str,
    source: str = "service",
) -> Optional[Dict[str, Any]]:
    """Remove an agent from a workspace."""
    _load()
    ws = _workspaces_store.get(workspace_id)
    if not ws:
        return None
    agents = ws.get("agent_ids", [])
    if agent_id in agents:
        agents.remove(agent_id)
        _save()
        record_audit("UPDATE", "workspace", workspace_id,
                     metadata={"action": "remove_agent", "agent_id": agent_id, "source": source})
    return ws


def get_workspace_types_list() -> List[Dict[str, Any]]:
    """Get all workspace types for dropdown."""
    return [workspace_type_to_dict(wt) for wt in list_workspace_types()]
