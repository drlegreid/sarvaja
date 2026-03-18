"""
Dashboard Initial Data Loader.

Per DOC-SIZE-01-v1: Extracted from governance_dashboard.py (679 lines).
Handles REST API loading at dashboard startup with MCP fallback.
"""

import logging
import threading
from pathlib import Path
from typing import Any

from agent.governance_ui.utils import (
    format_timestamps_in_list,
    compute_session_metrics,
    compute_session_duration,
    compute_timeline_data,
)

logger = logging.getLogger(__name__)


def load_initial_data(
    state: Any,
    api_base_url: str,
    get_rules,
    get_decisions,
    get_sessions,
    get_tasks,
) -> None:
    """Load initial data from REST API with MCP fallback.

    Populates state with rules, decisions, sessions, agents, and tasks.
    Uses REST API first (includes document_path), falls back to MCP functions.
    """
    import httpx
    page_size = 20

    try:
        with httpx.Client(timeout=10.0) as client:
            _load_rules(state, client, api_base_url, get_rules)
            _load_decisions(state, client, api_base_url, get_decisions)
            _load_sessions(state, client, api_base_url, get_sessions, page_size)
            _load_agents(state, client, api_base_url)
            _load_tasks(state, client, api_base_url, get_tasks, page_size)
            _load_projects(state, client, api_base_url)
            _load_workspaces(state, client, api_base_url)
            _load_tests(state, client, api_base_url)
    except Exception as e:
        # BUG-LOG-002: Log fallback instead of silently swallowing
        # BUG-474-DDL-1: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"REST API loading failed, falling back to MCP: {type(e).__name__}", exc_info=True)
        state.rules = get_rules()
        state.decisions = get_decisions()
        state.sessions = get_sessions(limit=100)
        state.tasks = get_tasks()


def _load_rules(state, client, api_base_url, get_rules) -> None:
    """Load rules from REST API."""
    resp = client.get(f"{api_base_url}/api/rules")
    if resp.status_code == 200:
        data = resp.json()
        state.rules = data.get("items", data) if isinstance(data, dict) else data
    else:
        state.rules = get_rules()


def _load_decisions(state, client, api_base_url, get_decisions) -> None:
    """Load decisions from REST API."""
    resp = client.get(f"{api_base_url}/api/decisions")
    if resp.status_code == 200:
        data = resp.json()
        state.decisions = data.get("items", data) if isinstance(data, dict) else data
    else:
        state.decisions = get_decisions()


def _load_sessions(state, client, api_base_url, get_sessions, page_size) -> None:
    """Load sessions with pagination and compute metrics."""
    resp = client.get(
        f"{api_base_url}/api/sessions",
        params={"limit": page_size, "offset": 0},
    )
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
            state.sessions_pagination = data.get("pagination", {})
        else:
            items = data[:page_size] if len(data) > page_size else data

        metrics = compute_session_metrics(items)
        state.sessions_metrics_duration = metrics["duration"]
        state.sessions_metrics_avg_tasks = metrics["avg_tasks"]

        for item in items:
            item["duration"] = compute_session_duration(
                item.get("start_time", ""), item.get("end_time", ""),
            )
            # BUG-SESSION-END-001: Show meaningful text for missing end_time
            if not item.get("end_time"):
                status = (item.get("status") or "").upper()
                if status in ("COMPLETED", "CLOSED"):
                    item["end_time"] = "(completed)"
                elif status == "ACTIVE":
                    item["end_time"] = "ongoing"
            # Derive source_type for Source column (SESSION-CC-01-v1)
            if not item.get("source_type"):
                sid = item.get("session_id", "")
                if item.get("cc_session_uuid") or "-CC-" in sid:
                    item["source_type"] = "CC"
                elif "-CHAT-" in sid or "-MCP-AUTO-" in sid:
                    item["source_type"] = "Chat"
                else:
                    item["source_type"] = "API"

        tl_vals, tl_labels = compute_timeline_data(items)
        state.sessions_timeline_data = tl_vals
        state.sessions_timeline_labels = tl_labels

        agents = sorted(set(
            s.get("agent_id") for s in items if s.get("agent_id")
        ))
        state.sessions_agent_options = agents
        state.sessions = format_timestamps_in_list(
            items, ["start_time", "end_time"],
        )
    else:
        state.sessions = get_sessions(limit=100)


def _load_agents(state, client, api_base_url) -> None:
    """Load agents from REST API."""
    resp = client.get(f"{api_base_url}/api/agents")
    if resp.status_code == 200:
        data = resp.json()
        state.agents = data.get("items", data) if isinstance(data, dict) else data
    else:
        state.agents = []


def _auto_ingest_cc_sessions(cc_proj: dict) -> None:
    """Auto-ingest CC sessions for a discovered project (idempotent).

    Per ASSESS-PLATFORM-GAPS-2026-02-15 Fix F: Bridges CC discovery → governance
    sessions so they appear on dashboard without manual backfill.
    """
    try:
        from governance.services.cc_session_ingestion import ingest_all
        cc_dir = cc_proj.get("cc_directory")
        if not cc_dir:
            return
        results = ingest_all(
            directory=Path(cc_dir),
            project_slug=cc_proj.get("project_id", "").replace("PROJ-", "").lower(),
            project_id=cc_proj.get("project_id"),
            dry_run=False,
        )
        if results:
            logger.info(f"Auto-ingested {len(results)} CC sessions for {cc_proj['project_id']}")
    except Exception as e:
        # BUG-477-DDL-1: Sanitize debug/info logger
        logger.debug(f"Auto-ingest sessions failed for {cc_proj.get('project_id', '?')}: {type(e).__name__}")


def _load_projects(state, client, api_base_url) -> None:
    """Load projects from REST API + auto-discover CC projects.

    Per ASSESS-PLATFORM-GAPS-2026-02-15 Fix D: Scans CC directories and
    auto-creates missing projects so they appear in the UI without manual backfill.
    """
    try:
        resp = client.get(f"{api_base_url}/api/projects", params={"limit": 50})
        if resp.status_code == 200:
            data = resp.json()
            existing = data.get("items", data) if isinstance(data, dict) else data
        else:
            existing = []
    except Exception as e:
        # BUG-477-DDL-2: Sanitize debug/info logger
        logger.debug(f"Failed to load projects from API: {type(e).__name__}")
        existing = []

    # Auto-discover CC projects and create missing ones
    try:
        from governance.services.cc_session_scanner import (
            discover_cc_projects,
            discover_filesystem_projects,
        )
        from governance.services.workspace_registry import detect_project_type
        cc_projects = discover_cc_projects()
        existing_ids = {p.get("project_id") for p in existing}

        for cc_proj in cc_projects:
            if cc_proj["project_id"] not in existing_ids:
                try:
                    # Auto-detect project type from filesystem
                    proj_type = detect_project_type(cc_proj.get("path", ""))
                    create_resp = client.post(
                        f"{api_base_url}/api/projects",
                        json={
                            "project_id": cc_proj["project_id"],
                            "name": cc_proj["name"],
                            "path": cc_proj["path"],
                            "project_type": proj_type,
                        },
                    )
                    if create_resp.status_code in (200, 201):
                        created = create_resp.json()
                        created["session_count"] = cc_proj["session_count"]
                        existing.append(created)
                        existing_ids.add(cc_proj["project_id"])
                        logger.info(f"Auto-created project: {cc_proj['project_id']} (type={proj_type})")
                except Exception as e:
                    # BUG-477-DDL-3: Sanitize debug/info logger
                    logger.debug(f"Auto-create project failed for {cc_proj['project_id']}: {type(e).__name__}")

            # Auto-ingest CC sessions in background (P3 fix: non-blocking startup)
            thread = threading.Thread(
                target=_auto_ingest_cc_sessions,
                args=(cc_proj,),
                daemon=True,
            )
            thread.start()
    except Exception as e:
        # BUG-477-DDL-4: Sanitize debug/info logger
        logger.debug(f"CC project discovery failed: {type(e).__name__}")

    # Filesystem-based discovery for projects without CC directories (P2 fix)
    try:
        from governance.services.cc_session_scanner import discover_filesystem_projects
        existing_paths = {p.get("path", "") for p in existing}
        existing_ids = {p.get("project_id") for p in existing}

        # Scan parent directories of known projects for siblings
        scan_dirs = set()
        for proj in existing:
            proj_path = proj.get("path", "")
            if proj_path:
                parent = str(Path(proj_path).parent)
                scan_dirs.add(parent)
                # Also scan sibling directories (e.g., ~/Documents/Vibe/)
                grandparent = str(Path(proj_path).parent.parent)
                scan_dirs.add(grandparent)

        fs_projects = discover_filesystem_projects(
            scan_dirs=list(scan_dirs),
            existing_paths=existing_paths,
            existing_ids=existing_ids,
        )

        for fs_proj in fs_projects:
            try:
                create_resp = client.post(
                    f"{api_base_url}/api/projects",
                    json={
                        "project_id": fs_proj["project_id"],
                        "name": fs_proj["name"],
                        "path": fs_proj["path"],
                        "project_type": fs_proj.get("project_type", "generic"),
                    },
                )
                if create_resp.status_code in (200, 201):
                    created = create_resp.json()
                    existing.append(created)
                    logger.info(f"Auto-created FS project: {fs_proj['project_id']} (type={fs_proj.get('project_type')})")
                else:
                    existing.append(fs_proj)
            except Exception as e:
                # BUG-477-DDL-5: Sanitize debug/info logger
                logger.debug(f"Auto-create FS project failed for {fs_proj['project_id']}: {type(e).__name__}")
                existing.append(fs_proj)
    except Exception as e:
        # BUG-477-DDL-6: Sanitize debug/info logger
        logger.debug(f"Filesystem project discovery failed: {type(e).__name__}")

    state.projects = existing


def _load_workspaces(state, client, api_base_url) -> None:
    """Load workspaces and workspace types from REST API."""
    try:
        resp = client.get(f"{api_base_url}/api/workspaces", params={"limit": 200})
        if resp.status_code == 200:
            state.workspaces = resp.json()
        else:
            state.workspaces = []
    except Exception as e:
        logger.debug(f"Failed to load workspaces: {type(e).__name__}")
        state.workspaces = []

    try:
        types_resp = client.get(f"{api_base_url}/api/workspaces/types")
        if types_resp.status_code == 200:
            types_data = types_resp.json()
            state.workspace_types = types_data
            state.workspace_type_options = [
                t.get("type_id", t.get("name", ""))
                for t in types_data
            ]
    except Exception as e:
        logger.debug(f"Failed to load workspace types: {type(e).__name__}")


def _load_tests(state, client, api_base_url) -> None:
    """Load recent test runs and CVP status on startup."""
    try:
        resp = client.get(f"{api_base_url}/api/tests/results", params={"limit": 10})
        if resp.status_code == 200:
            data = resp.json()
            state.tests_recent_runs = data.get("runs", [])
        else:
            state.tests_recent_runs = []

        # Also load CVP pipeline status
        cvp_resp = client.get(f"{api_base_url}/api/tests/cvp/status")
        if cvp_resp.status_code == 200:
            state.tests_cvp_status = cvp_resp.json()
    except Exception as e:
        # BUG-477-DDL-7: Sanitize debug/info logger
        logger.debug(f"Failed to load test results: {type(e).__name__}")
        state.tests_recent_runs = []


def _load_tasks(state, client, api_base_url, get_tasks, page_size) -> None:
    """Load tasks with pagination."""
    resp = client.get(
        f"{api_base_url}/api/tasks",
        params={"limit": page_size, "offset": 0},
    )
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict) and "items" in data:
            state.tasks = data["items"]
            state.tasks_pagination = data.get("pagination", {})
        else:
            state.tasks = data[:page_size] if len(data) > page_size else data
            state.tasks_pagination = {
                "total": len(data), "offset": 0, "limit": page_size,
                "has_more": len(data) > page_size,
                "returned": min(len(data), page_size),
            }
        # BUG-UI-TASKS-003: Format timestamps on initial load
        state.tasks = format_timestamps_in_list(
            state.tasks, ["created_at", "completed_at", "claimed_at"]
        )
        # BUG-UI-TASKS-004: Enrich doc_count for Docs column
        from agent.governance_ui.controllers.tasks import _enrich_doc_count
        state.tasks = _enrich_doc_count(state.tasks)
    else:
        state.tasks = get_tasks()
