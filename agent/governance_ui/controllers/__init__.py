"""
Controllers Package (GAP-FILE-005)
==================================
Trame controller registration functions for Governance Dashboard.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py (1159 lines)

Created: 2024-12-28

Module Structure:
    rules.py      - Rule CRUD + filter/sort controllers
    tasks.py      - Task CRUD controllers
    sessions.py   - Session detail controllers
    decisions.py  - Decision detail controllers
    data_loaders.py - Data loading/refresh controllers
    impact.py     - Impact analysis controllers (P9.4)
    trust.py      - Trust dashboard controllers (P9.5)
    monitor.py    - Monitoring controllers (P9.6)
    backlog.py    - Agent task backlog controllers
    chat.py       - Agent chat controllers (ORCH-006)
    search.py     - Evidence search controllers (GAP-UI-009)
"""

from .rules import register_rules_controllers
from .search import register_search_controllers
from .tasks import register_tasks_controllers
from .sessions import register_sessions_controllers
from .decisions import register_decisions_controllers
from .data_loaders import register_data_loader_controllers
from .impact import register_impact_controllers
from .trust import register_trust_controllers
from .monitor import register_monitor_controllers
from .backlog import register_backlog_controllers
from .chat import register_chat_controllers
from .tests import register_tests_controllers
from ..handlers import register_trace_bar_handlers

__all__ = [
    'register_rules_controllers',
    'register_search_controllers',
    'register_tasks_controllers',
    'register_sessions_controllers',
    'register_decisions_controllers',
    'register_data_loader_controllers',
    'register_impact_controllers',
    'register_trust_controllers',
    'register_monitor_controllers',
    'register_backlog_controllers',
    'register_chat_controllers',
    'register_tests_controllers',
]


def register_all_controllers(state, ctrl, api_base_url: str) -> dict:
    """
    Register all controllers with Trame server.

    This is the main entry point for controller registration.
    Call this from governance_dashboard.py build_ui() method.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for REST API

    Returns:
        Dict of loader functions for view change handler
    """
    # Register all controller groups
    register_rules_controllers(state, ctrl, api_base_url)
    register_search_controllers(state, ctrl, api_base_url)
    register_tasks_controllers(state, ctrl, api_base_url)
    register_sessions_controllers(state, ctrl, api_base_url)
    register_decisions_controllers(state, ctrl, api_base_url)
    register_impact_controllers(state, ctrl, api_base_url)
    register_trust_controllers(state, ctrl, api_base_url)
    register_monitor_controllers(state, ctrl, api_base_url)
    register_chat_controllers(state, ctrl, api_base_url)

    # Trace bar handlers (GAP-UI-048)
    register_trace_bar_handlers(ctrl, state)

    # Data loaders return loader functions for view change handler
    loaders = register_data_loader_controllers(state, ctrl, api_base_url)

    # Backlog needs access to load_backlog_data function
    register_backlog_controllers(
        state, ctrl, api_base_url,
        loaders['load_backlog_data']
    )

    # Tests controller (WORKFLOW-SHELL-01-v1)
    tests_loaders = register_tests_controllers(state, ctrl, api_base_url)
    loaders['load_tests_data'] = tests_loaders['load_tests_data']

    return loaders
