"""
Task CRUD Exports (GAP-FILE-007)
================================
Task backward compatibility exports for test imports.

Per RULE-012: DSP Semantic Code Structure
Per P10.4: MCP Tools for CRUD
Per GAP-FILE-007: Extracted from mcp_server.py

Created: 2024-12-28
"""

import json
from dataclasses import asdict
from datetime import datetime

from governance.mcp_tools.common import get_typedb_client


def _json_serializer(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Handle TypeDB Datetime objects (duck typing for isoformat)
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    # Handle TypeDB 3.x native datetime representation
    if type(obj).__name__ == 'Datetime':
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def governance_create_task(task_id, name, description="", status="pending",
                           priority="MEDIUM", phase="P10"):
    """Create task (backward compat export)."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})
        # Map description → body (client uses 'body' parameter)
        body = f"[Priority: {priority}] {description}" if description else f"[Priority: {priority}]"
        success = client.insert_task(
            task_id=task_id,
            name=name,
            status=status,
            phase=phase,
            body=body
        )
        if success:
            return json.dumps({
                "task_id": task_id,
                "name": name,
                "status": status,
                "phase": phase,
                "priority": priority,
                "message": f"Task {task_id} created successfully"
            }, indent=2)
        return json.dumps({"error": f"Failed to create task {task_id}"})
    finally:
        client.close()


def governance_get_task(task_id):
    """Get task (backward compat export)."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})
        task = client.get_task(task_id)
        if task:
            return json.dumps(asdict(task), indent=2, default=_json_serializer)
        return json.dumps({"error": f"Task {task_id} not found"})
    finally:
        client.close()


def governance_update_task(task_id, status=None, name=None, phase=None):
    """Update task (backward compat export)."""
    if not any([status, name, phase]):
        return json.dumps({"error": "No update fields provided"})
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})
        success = client.update_task(task_id=task_id, status=status, name=name, phase=phase)
        if success:
            task = client.get_task(task_id)
            if task:
                result = asdict(task)
                result["message"] = f"Task {task_id} updated successfully"
                return json.dumps(result, indent=2, default=_json_serializer)
            return json.dumps({"task_id": task_id, "message": f"Task {task_id} updated"}, indent=2)
        return json.dumps({"error": f"Failed to update task {task_id}"})
    finally:
        client.close()


def governance_delete_task(task_id):
    """Delete task (backward compat export)."""
    client = get_typedb_client()
    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})
        success = client.delete_task(task_id)
        if success:
            return json.dumps({
                "task_id": task_id,
                "deleted": True,
                "message": f"Task {task_id} deleted successfully"
            }, indent=2)
        return json.dumps({"error": f"Failed to delete task {task_id}"})
    finally:
        client.close()
