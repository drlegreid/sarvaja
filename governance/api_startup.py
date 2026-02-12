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
    loop = asyncio.get_event_loop()
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
            data["end_time"] = "orphan-cleanup-on-startup"
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
