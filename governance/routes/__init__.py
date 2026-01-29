"""
Governance API Routes Module.

Per RULE-012: DSP Semantic Code Structure - modular route files.
Per GAP-FILE-002: API route modularization.

Each route module follows Single Responsibility Principle:
- rules.py: Rules and Decisions CRUD
- tasks.py: Tasks CRUD and execution log
- sessions.py: Sessions CRUD
- evidence.py: Evidence endpoints
- files.py: File content endpoint
- agents.py: Agents CRUD
- reports.py: Executive reports
- chat.py: Agent chat API

Usage:
    from governance.routes import (
        rules_router, tasks_router, sessions_router,
        evidence_router, files_router, agents_router,
        reports_router, chat_router
    )

    app.include_router(rules_router, prefix="/api")
"""

from .rules import router as rules_router
from .tasks import router as tasks_router
from .sessions import router as sessions_router
from .evidence import router as evidence_router
from .files import router as files_router
from .agents import router as agents_router
from .reports import router as reports_router
from .chat import router as chat_router
from .metrics import router as metrics_router

__all__ = [
    "rules_router",
    "tasks_router",
    "sessions_router",
    "evidence_router",
    "files_router",
    "agents_router",
    "reports_router",
    "chat_router",
    "metrics_router",
]
