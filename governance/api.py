"""
Governance REST API - FastAPI endpoints for Rules, Tasks, Sessions, Evidence.

Per RULE-012: DSP Semantic Code Structure - modularized via routes/.
Per RULE-019: UI/UX Design Standards.
Per GAP-FILE-002: API modularization (2357 -> ~200 lines, 92% reduction).
Per DOC-SIZE-01-v1: Startup handlers in api_startup.py.

Created: 2024-12-25
Updated: 2024-12-28 - Modularized into routes/ per RULE-012.

Route modules:
    - routes/rules.py: Rules and Decisions CRUD
    - routes/tasks.py: Tasks CRUD and execution log
    - routes/sessions.py: Sessions CRUD
    - routes/evidence.py: Evidence endpoints
    - routes/files.py: File content endpoint
    - routes/agents.py: Agents CRUD
    - routes/reports.py: Executive reports
    - routes/chat.py: Agent chat API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os
import logging

from governance.client import get_client
from governance.middleware import AccessLogMiddleware
from governance.models import (
    APIStatus,
)
from governance.routes import (
    rules_router, tasks_router, sessions_router,
    evidence_router, files_router, agents_router,
    reports_router, chat_router, metrics_router,
    projects_router, taxonomy_router,
)
from governance.routes.tests import tests_router
from governance.routes.audit import router as audit_router  # RD-DEBUG-AUDIT
from governance.routes.agents.observability import router as observability_router  # GAP-MONITOR-IPC-001
from governance.routes.proposals import router as proposals_router  # GOV-BICAM-01-v1: LangGraph workflow
from governance.routes.infra import router as infra_router  # EPIC-7.1: Container logs
from governance.routes.capabilities import router as capabilities_router  # Entity chain: Agent → Rules
from governance.routes.workspaces import router as workspaces_router  # Entity chain: Project → Workspace
from governance.routes.ingestion import router as ingestion_router  # P2-10: Event-driven ingestion
from governance.stores import (
    _tasks_store, _sessions_store, _agents_store,
    generate_chat_session_id, synthesize_execution_events,
)
# Backward-compatibility aliases for tests
_generate_chat_session_id = generate_chat_session_id
_synthesize_execution_events = synthesize_execution_events

# Re-exports from extracted startup module for backward compatibility
from governance.api_startup import (  # noqa: F401
    warmup_chromadb_embeddings as _warmup_chromadb,
    seed_data as _seed_data,
    cleanup_orphaned_chat_sessions as _cleanup_orphaned,
    discover_cc_sessions as _discover_cc_sessions,
    mcp_readiness_handler,
    _module_exists,
    _check_service_integration,
)

# Configure logging — ensure governance.* loggers propagate to container stdout
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger(__name__)
# Structured logging channels
logging.getLogger("governance.access").setLevel(logging.INFO)
logging.getLogger("governance.events").setLevel(logging.INFO)
logging.getLogger("governance.dashboard").setLevel(logging.INFO)


# =============================================================================
# API AUTHENTICATION (GAP-SEC-001)
# =============================================================================

# API Key configuration - set via environment variable
# None = no auth required (dev mode)
API_KEY = os.getenv("GOVERNANCE_API_KEY", None)
API_KEY_NAME = "X-API-Key"

# List of paths that don't require authentication
PUBLIC_PATHS = {
    "/api/health",
    "/api/docs",
    "/api/redoc",
    "/openapi.json",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API key authentication.

    Per GAP-SEC-001: Protects all API endpoints except health/docs.

    Usage:
        Set GOVERNANCE_API_KEY environment variable to enable.
        Pass key via X-API-Key header or api_key query param.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth if no API key configured (dev mode)
        if API_KEY is None:
            return await call_next(request)

        # Check API key in header or query
        api_key = request.headers.get(API_KEY_NAME) or request.query_params.get("api_key")

        if api_key != API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API Key"},
                headers={"WWW-Authenticate": "ApiKey"},
            )

        return await call_next(request)


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Sarvaja Governance API",
    description="REST API for governance rules, tasks, sessions, and evidence",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add authentication middleware (GAP-SEC-001)
app.add_middleware(AuthMiddleware)

# Structured access logging (L1)
app.add_middleware(AccessLogMiddleware)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# INCLUDE ROUTE MODULES
# =============================================================================

app.include_router(rules_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")  # SESSION-METRICS-01-v1: Session analytics
app.include_router(tests_router, prefix="/api")  # WORKFLOW-SHELL-01-v1: Self-assessment
app.include_router(audit_router, prefix="/api")  # RD-DEBUG-AUDIT: Audit trail
app.include_router(observability_router, prefix="/api/agents")  # GAP-MONITOR-IPC-001: Monitor events
app.include_router(proposals_router, prefix="/api")  # GOV-BICAM-01-v1: LangGraph proposal workflow
app.include_router(projects_router, prefix="/api")  # GOV-PROJECT-01-v1: Project hierarchy
app.include_router(taxonomy_router, prefix="/api")  # META-TAXON-01-v1: Task/rule taxonomy
app.include_router(infra_router)  # EPIC-7.1: Container logs via podman socket
app.include_router(capabilities_router, prefix="/api")  # Entity chain: Agent → Capabilities (rules)
app.include_router(workspaces_router, prefix="/api")  # Entity chain: Project → Workspace → Agent
app.include_router(ingestion_router, prefix="/api")  # P2-10: Event-driven ingestion scheduler


# =============================================================================
# STARTUP HANDLERS (delegated to api_startup.py)
# =============================================================================

@app.on_event("startup")
async def warmup_chromadb_embeddings():
    await _warmup_chromadb()


@app.on_event("startup")
async def seed_data():
    await _seed_data(_tasks_store, _sessions_store, _agents_store)


@app.on_event("startup")
async def cleanup_orphaned_chat_sessions():
    await _cleanup_orphaned(_sessions_store)


@app.on_event("startup")
async def reload_persisted_sessions():
    from governance.stores.session_persistence import load_persisted_sessions
    load_persisted_sessions(_sessions_store)


@app.on_event("startup")
async def auto_discover_cc_sessions():
    """P2-10: Start ingestion scheduler (replaces one-shot discovery)."""
    await _discover_cc_sessions()


@app.on_event("shutdown")
async def stop_ingestion_scheduler():
    """P2-10: Gracefully stop the ingestion scheduler."""
    from governance.services.ingestion_scheduler import get_scheduler
    scheduler = get_scheduler()
    await scheduler.stop()


@app.on_event("shutdown")
async def _stop_claude_watcher():
    """P2-10a: Gracefully stop the JSONL file watcher."""
    from governance.api_startup import stop_claude_watcher
    await stop_claude_watcher()


# =============================================================================
# HEALTH / STATUS
# =============================================================================

@app.get("/api/health", response_model=APIStatus)
async def health_check():
    """
    Health check endpoint.

    Per GAP-SEC-001: Returns auth_enabled status.
    Per GAP-ARCH-001/002/003: Returns TypeDB connection status.
    """
    client = get_client()
    connected = client is not None and client.is_connected()
    rules_count = 0
    decisions_count = 0

    if connected:
        try:
            rules = client.get_all_rules()
            rules_count = len(rules) if rules else 0
            decisions = client.get_all_decisions()
            decisions_count = len(decisions) if decisions else 0
        except Exception as e:
            logger.debug(f"Failed to query health counts: {e}")

    return APIStatus(
        status="ok" if connected else "degraded",
        typedb_connected=connected,
        rules_count=rules_count,
        decisions_count=decisions_count,
        auth_enabled=API_KEY is not None
    )


@app.get("/api/mcp/readiness")
async def mcp_readiness():
    """MCP usage enforcement audit & readiness check."""
    return mcp_readiness_handler()


# =============================================================================
# MAIN
# =============================================================================

def create_api_app() -> FastAPI:
    """Factory function to create API app."""
    return app


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8082"))
    uvicorn.run(app, host="0.0.0.0", port=port)
