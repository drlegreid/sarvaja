"""
Project Service — CRUD + hierarchy navigation.

Per GOV-PROJECT-01-v1: All work organized under projects.
Created: 2026-02-11
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# In-memory fallback store
_projects_store: Dict[str, Dict[str, Any]] = {}


def _get_client():
    """Get TypeDB client if available."""
    try:
        from governance.client import get_client
        client = get_client()
        if client and client.is_connected():
            return client
    except Exception:
        pass
    return None


def create_project(
    project_id: Optional[str] = None,
    name: str = "",
    path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create a new project."""
    if not project_id:
        slug = name.upper().replace(" ", "-")[:20]
        project_id = f"PROJ-{slug}"

    client = _get_client()
    if client:
        try:
            result = client.insert_project(
                project_id=project_id, name=name, path=path,
            )
            if result:
                return result
        except Exception as e:
            logger.warning(f"TypeDB insert project failed: {e}")

    # In-memory fallback
    project = {
        "project_id": project_id,
        "name": name,
        "path": path,
        "plan_count": 0,
        "session_count": 0,
    }
    _projects_store[project_id] = project
    return project


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Get a project by ID, enriched with session/plan counts."""
    client = _get_client()
    if client:
        try:
            result = client.get_project(project_id)
            if result:
                # Enrich with counts from linking queries
                try:
                    result["session_count"] = len(client.get_project_sessions(project_id))
                except Exception:
                    result.setdefault("session_count", 0)
                try:
                    result["plan_count"] = len(client.get_project_plans(project_id))
                except Exception:
                    result.setdefault("plan_count", 0)
                return result
        except Exception as e:
            logger.warning(f"TypeDB get project failed: {e}")

    return _projects_store.get(project_id)


def list_projects(
    limit: int = 50, offset: int = 0,
) -> Dict[str, Any]:
    """List projects with pagination."""
    client = _get_client()
    projects = []

    if client:
        try:
            projects = client.list_projects(limit=limit, offset=offset)
            # Enrich with counts
            for p in projects:
                pid = p.get("project_id", "")
                try:
                    p["session_count"] = len(client.get_project_sessions(pid))
                except Exception:
                    p.setdefault("session_count", 0)
                try:
                    p["plan_count"] = len(client.get_project_plans(pid))
                except Exception:
                    p.setdefault("plan_count", 0)
        except Exception as e:
            logger.warning(f"TypeDB list projects failed: {e}")

    if not projects:
        all_projects = sorted(_projects_store.values(), key=lambda p: p.get("project_id", ""))
        projects = all_projects[offset:offset + limit]

    total = len(projects)
    return {
        "items": projects,
        "pagination": {
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": total >= limit,
            "returned": len(projects),
        },
    }


def delete_project(project_id: str) -> bool:
    """Delete a project."""
    client = _get_client()
    if client:
        try:
            return client.delete_project(project_id)
        except Exception as e:
            logger.warning(f"TypeDB delete project failed: {e}")

    if project_id in _projects_store:
        del _projects_store[project_id]
        return True
    return False


def link_session_to_project(project_id: str, session_id: str) -> bool:
    """Link a session to a project."""
    client = _get_client()
    if client:
        try:
            return client.link_project_to_session(project_id, session_id)
        except Exception as e:
            logger.warning(f"TypeDB link session to project failed: {e}")
    return False
