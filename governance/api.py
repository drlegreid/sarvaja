"""
Governance REST API - FastAPI endpoints for Rules, Tasks, Sessions, Evidence.

Per RULE-012: DSP Semantic Code Structure - modularized via routes/.
Per RULE-019: UI/UX Design Standards.
Per GAP-FILE-002: API modularization (2357 -> ~200 lines, 92% reduction).

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
from governance.models import (
    APIStatus,
    # Backward-compatibility re-exports for tests
    ChatMessageRequest, ChatMessageResponse, ChatSessionResponse,
    ExecutiveReportSection, ExecutiveReportResponse,
)
from governance.routes import (
    rules_router, tasks_router, sessions_router,
    evidence_router, files_router, agents_router,
    reports_router, chat_router
)
from governance.routes.tests import tests_router
from governance.routes.audit import router as audit_router  # RD-DEBUG-AUDIT
from governance.routes.chat import _process_chat_command  # Backward-compat re-export
from governance.stores import (
    _tasks_store, _sessions_store, _agents_store,
    generate_chat_session_id, synthesize_execution_events,
)
# Backward-compatibility aliases for tests
_generate_chat_session_id = generate_chat_session_id
_synthesize_execution_events = synthesize_execution_events

# Models re-exports for backward compatibility
from governance.models import (
    TaskExecutionEvent, TaskExecutionResponse, FileContentResponse,
)

# Configure logging
logger = logging.getLogger(__name__)


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
    title="Sim.ai Governance API",
    description="REST API for governance rules, tasks, sessions, and evidence",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add authentication middleware (GAP-SEC-001)
app.add_middleware(AuthMiddleware)

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
app.include_router(tests_router, prefix="/api")  # WORKFLOW-SHELL-01-v1: Self-assessment
app.include_router(audit_router, prefix="/api")  # RD-DEBUG-AUDIT: Audit trail


# =============================================================================
# STARTUP: Seed data for Tasks and Sessions (per GAP-UI-008)
# =============================================================================

@app.on_event("startup")
async def seed_data():
    """
    Seed in-memory stores with initial data.

    Per GAP-UI-008: Tasks view shows empty table.
    Per P10.1-P10.3: TypeDB-first seeding with in-memory cache.

    Note: Seed data moved to governance/seed_data.py for maintainability.
    """
    from governance.seed_data import seed_tasks_and_sessions
    seed_tasks_and_sessions(_tasks_store, _sessions_store, _agents_store)


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
        except Exception:
            pass

    return APIStatus(
        status="ok" if connected else "degraded",
        typedb_connected=connected,
        rules_count=rules_count,
        decisions_count=decisions_count,
        auth_enabled=API_KEY is not None
    )


# =============================================================================
# MAIN
# =============================================================================

def create_api_app() -> FastAPI:
    """Factory function to create API app."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
