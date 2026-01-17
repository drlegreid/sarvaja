"""
Governance UI Views Module.

Modular view builders for each entity per RULE-012 (DSP Hygiene).
Each view module follows Single Responsibility Principle.

Usage:
    from governance_ui.views import build_rules_view, build_tasks_view

    with layout.content:
        build_rules_view(state)
"""

from .rules_view import build_rules_view
from .tasks_view import build_tasks_view
from .sessions_view import build_sessions_view
from .agents_view import build_agents_view
from .decisions_view import build_decisions_view
from .executive_view import build_executive_view
from .chat_view import build_chat_view
from .backlog_view import build_backlog_view
from .monitor_view import build_monitor_view
from .trust_view import build_trust_view
from .search_view import build_search_view
from .impact_view import build_impact_view
from .infra_view import build_infra_view
from .workflow_view import build_workflow_view
from .audit_view import build_audit_view
from .tests_view import build_tests_view
from .trace_bar_view import build_trace_bar
from .dialogs import build_all_dialogs, build_file_viewer_dialog

__all__ = [
    "build_rules_view",
    "build_tasks_view",
    "build_sessions_view",
    "build_agents_view",
    "build_decisions_view",
    "build_executive_view",
    "build_chat_view",
    "build_backlog_view",
    "build_monitor_view",
    "build_trust_view",
    "build_search_view",
    "build_impact_view",
    "build_infra_view",
    "build_workflow_view",
    "build_audit_view",
    "build_tests_view",
    "build_trace_bar",
    "build_all_dialogs",
    "build_file_viewer_dialog",
]
