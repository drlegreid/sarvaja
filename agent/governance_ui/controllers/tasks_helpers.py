"""
Task Controller Helpers
=======================
Shared enrichment and filter functions for task data.

Per DOC-SIZE-01-v1: Extracted from tasks.py.
"""

import httpx


def _enrich_doc_count(tasks):
    """Add doc_count field to each task for the Docs column."""
    for t in tasks:
        docs = t.get("linked_documents") or []
        t["doc_count"] = len(docs)
    return tasks


def _enrich_first_session(tasks):
    """Add first_session field to each task for the Session column. Phase 9d."""
    for t in tasks:
        sessions = t.get("linked_sessions") or []
        t["first_session"] = sessions[0] if sessions else ""
    return tasks


def _fetch_workspace_project_map(api_base_url):
    """Fetch workspace_id → project_id map from API. FIX-HIER-001."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{api_base_url}/api/workspaces")
            if resp.status_code == 200:
                return {
                    ws["workspace_id"]: ws.get("project_id", "")
                    for ws in resp.json()
                }
    except Exception:
        pass
    return {}


def _enrich_project_name(tasks, ws_project_map):
    """Add project_name field from workspace→project_id mapping. FIX-HIER-001."""
    for t in tasks:
        ws_id = t.get("workspace_id")
        t["project_name"] = ws_project_map.get(ws_id, "") if ws_id else ""
    return tasks


# Phase 4: Test task prefix patterns
_TEST_PREFIXES = ("CRUD-", "INTTEST-", "TEST-")


def _filter_test_tasks(tasks):
    """FIX-FILT-001: Remove test tasks from display list.

    Filters out tasks where task_type='test' or task_id starts
    with test prefixes (CRUD-*, INTTEST-*, TEST-*).
    """
    return [
        t for t in tasks
        if t.get("task_type") != "test"
        and not any(
            (t.get("task_id") or "").startswith(pfx)
            for pfx in _TEST_PREFIXES
        )
    ]
