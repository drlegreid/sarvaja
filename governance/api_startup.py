"""
API Startup Handlers
====================
FastAPI on_event("startup") handlers for data seeding and cleanup.

Per DOC-SIZE-01-v1: Extracted from api.py.
"""

import logging

logger = logging.getLogger(__name__)


async def warmup_chromadb_embeddings():
    """Pre-download ChromaDB ONNX embedding model on startup.

    The chromadb client downloads all-MiniLM-L6-v2 (79MB) on first use.
    By triggering it at startup, we avoid blocking the first heuristic/search call.
    Logs progress to console so operators see readiness state.
    """
    import asyncio
    import concurrent.futures

    def _warmup():
        try:
            import chromadb
            logger.info("ChromaDB embeddings: checking ONNX model cache...")
            # Creating a client with default embedding triggers the download
            client = chromadb.Client()
            # A trivial add triggers the model load (download if missing)
            col = client.get_or_create_collection("sarvaja-warmup-probe")
            col.add(documents=["startup probe"], ids=["probe-1"])
            col.delete(ids=["probe-1"])
            client.delete_collection("sarvaja-warmup-probe")
            logger.info("ChromaDB embeddings: ONNX model ready")
        except Exception as e:
            logger.warning("ChromaDB embeddings: not ready (%s) - first search may be slow", str(e)[:80])

    # Run in thread pool to not block startup
    # BUG-225-STARTUP-001: Use get_running_loop() (get_event_loop deprecated in 3.10+)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(concurrent.futures.ThreadPoolExecutor(max_workers=1), _warmup)


async def seed_data(_tasks_store, _sessions_store, _agents_store):
    """
    Seed in-memory stores with initial data.

    Per GAP-UI-008: Tasks view shows empty table.
    Per P10.1-P10.3: TypeDB-first seeding with in-memory cache.

    Note: Seed data moved to governance/seed_data.py for maintainability.
    """
    from governance.seed_data import seed_tasks_and_sessions
    seed_tasks_and_sessions(_tasks_store, _sessions_store, _agents_store)


async def cleanup_orphaned_chat_sessions(_sessions_store):
    """End stale ACTIVE chat sessions from prior container runs.

    Per GAP-GOVSESS-CAPTURE-001: _chat_gov_sessions is in-memory only,
    so a container restart loses collector refs. This ends any CHAT-*
    sessions that are still ACTIVE in TypeDB or _sessions_store.
    """
    ended = 0

    # Clean _sessions_store (for sessions created this container run)
    for sid, data in list(_sessions_store.items()):
        if data.get("status") == "ACTIVE" and "CHAT-" in sid:
            data["status"] = "COMPLETED"
            # BUG-213-ORPHAN-ENDTIME-001: Use ISO timestamp, not string literal
            from datetime import datetime as _dt
            data["end_time"] = _dt.now().isoformat()
            ended += 1

    # Clean TypeDB: end any ACTIVE CHAT-* sessions from prior runs
    try:
        from governance.services.sessions import list_sessions, end_session
        result = list_sessions(status=None, limit=200)
        for s in result.get("items", []):
            sid = s.get("session_id", "")
            if s.get("status") == "ACTIVE" and "CHAT-" in sid:
                try:
                    end_session(sid, source="orphan-cleanup")
                    ended += 1
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"TypeDB orphan cleanup skipped: {e}")

    if ended:
        logger.info(f"Startup: ended {ended} orphaned CHAT sessions")


async def discover_cc_sessions():
    """Auto-discover and ingest CC sessions on API startup.

    Per GAP-SESSION-CC-AUTO-DISCOVERY: Scans ~/.claude/projects/ for JSONL
    files, creates missing project entities, and ingests CC sessions so they
    appear in the API without waiting for the dashboard to load.

    Runs ingestion in a background thread to avoid blocking startup.
    """
    import asyncio
    import concurrent.futures
    import threading

    def _discover_and_ingest():
        try:
            from governance.services.cc_session_scanner import (
                discover_cc_projects,
                discover_filesystem_projects,
            )
            from governance.services.cc_session_ingestion import ingest_all
            from governance.services.projects import create_project, get_project
            from governance.services.workspace_registry import detect_project_type
            from pathlib import Path

            cc_projects = discover_cc_projects()
            if not cc_projects:
                logger.info("CC auto-discovery: no CC projects found")
                return

            created_projects = 0
            ingested_sessions = 0

            for cc_proj in cc_projects:
                pid = cc_proj["project_id"]

                # Create project if missing
                existing = get_project(pid)
                if not existing:
                    proj_path = cc_proj.get("path", "")
                    proj_type = "generic"
                    try:
                        proj_type = detect_project_type(proj_path)
                    except Exception:
                        pass
                    create_project(
                        project_id=pid,
                        name=cc_proj["name"],
                        path=proj_path,
                        project_type=proj_type,
                    )
                    created_projects += 1

                # Ingest sessions
                cc_dir = cc_proj.get("cc_directory")
                if cc_dir:
                    slug = pid.replace("PROJ-", "").lower()
                    results = ingest_all(
                        directory=Path(cc_dir),
                        project_slug=slug,
                        project_id=pid,
                        dry_run=False,
                    )
                    ingested_sessions += len(results)

            # Also discover filesystem projects (game projects etc.)
            try:
                existing_paths = {cc_proj.get("path", "") for cc_proj in cc_projects}
                existing_ids = {cc_proj["project_id"] for cc_proj in cc_projects}
                scan_dirs = set()
                for cc_proj in cc_projects:
                    p = cc_proj.get("path", "")
                    if p:
                        scan_dirs.add(str(Path(p).parent))

                fs_projects = discover_filesystem_projects(
                    scan_dirs=list(scan_dirs),
                    existing_paths=existing_paths,
                    existing_ids=existing_ids,
                )
                for fs_proj in fs_projects:
                    existing = get_project(fs_proj["project_id"])
                    if not existing:
                        create_project(
                            project_id=fs_proj["project_id"],
                            name=fs_proj["name"],
                            path=fs_proj["path"],
                            project_type=fs_proj.get("project_type", "generic"),
                        )
                        created_projects += 1
            except Exception as e:
                logger.debug(f"FS project discovery failed: {e}")

            if created_projects or ingested_sessions:
                logger.info(
                    f"CC auto-discovery: {created_projects} projects created, "
                    f"{ingested_sessions} sessions ingested"
                )
            else:
                logger.info("CC auto-discovery: all sessions already ingested")
        except Exception as e:
            # BUG-474-AST-1: Sanitize logger message + add exc_info for stack trace preservation
            logger.warning(f"CC auto-discovery failed: {type(e).__name__}", exc_info=True)

    # Run in thread pool to not block API startup
    # BUG-225-STARTUP-001: Use get_running_loop() (get_event_loop deprecated in 3.10+)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        concurrent.futures.ThreadPoolExecutor(max_workers=1),
        _discover_and_ingest,
    )


def mcp_readiness_handler(api_base_url_unused=None):
    """MCP usage enforcement audit & readiness check.

    Reports which MCP servers are configured, their backend dependencies,
    and whether the service layer is properly integrated.
    """
    from agent.governance_ui.controllers.infra import (
        MCP_SERVER_META, SERVICE_CONFIG, check_port, is_in_container,
    )

    # Check backend service health (container-aware per GAP-MCP-READINESS-001)
    backends = {}
    in_container = is_in_container()
    for svc_name, (container_host, container_port, host_port) in SERVICE_CONFIG.items():
        if in_container:
            backends[svc_name] = check_port(container_host, container_port)
        else:
            backends[svc_name] = check_port("localhost", host_port)

    # Check each MCP server readiness
    servers = {}
    all_ready = True
    for name, meta in MCP_SERVER_META.items():
        deps = meta.get("depends_on", [])
        deps_ok = all(backends.get(d, False) for d in deps)
        ready = not deps or deps_ok
        servers[name] = {
            "tools": meta.get("tools", 0),
            "depends_on": deps,
            "deps_ok": deps_ok,
            "ready": ready,
            "desc": meta.get("desc", ""),
        }
        if not ready:
            all_ready = False

    # Check service layer integration
    service_audit = {
        "tasks": _check_service_integration("governance.services.tasks"),
        "sessions": _check_service_integration("governance.services.sessions"),
        "rules": _check_service_integration("governance.services.rules"),
        "agents": _check_service_integration("governance.services.agents"),
    }

    return {
        "status": "READY" if all_ready else "PARTIAL",
        "backends": backends,
        "mcp_servers": servers,
        "service_layer": service_audit,
        "total_tools": sum(s["tools"] for s in servers.values()),
        "ready_count": sum(1 for s in servers.values() if s["ready"]),
        "total_count": len(servers),
    }


def _module_exists(module_name: str) -> bool:
    """Check if a Python module exists."""
    import importlib
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def _check_service_integration(module_name: str) -> str:
    """Check if a service layer module is integrated."""
    if _module_exists(module_name):
        return "SERVICE_LAYER"
    return "DIRECT_TYPEDB"
