"""
Core Data Access Functions (GAP-FILE-006)
==========================================
MCP tool registry and core data access functions.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py

Created: 2024-12-28
"""

import json
from typing import Dict, List, Any, Callable

# Import MCP tools
from governance.compat import (
    governance_list_sessions,
    governance_get_session,
    governance_list_decisions,
    governance_get_decision,
    governance_list_tasks,
    governance_get_task_deps,
    governance_evidence_search,
    governance_query_rules,
)


# =============================================================================
# MCP TOOL REGISTRY (Immutable)
# =============================================================================

MCP_TOOLS: Dict[str, Callable] = {
    'governance_list_sessions': governance_list_sessions,
    'governance_get_session': governance_get_session,
    'governance_list_decisions': governance_list_decisions,
    'governance_get_decision': governance_get_decision,
    'governance_list_tasks': governance_list_tasks,
    'governance_get_task_deps': governance_get_task_deps,
    'governance_evidence_search': governance_evidence_search,
    'governance_query_rules': governance_query_rules,
}


# =============================================================================
# PURE FUNCTIONS (No side effects)
# =============================================================================

def call_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Call an MCP tool and parse JSON response.

    Pure function: same input -> same output, no side effects.

    Args:
        tool_name: Name of MCP tool
        **kwargs: Tool arguments

    Returns:
        Parsed JSON dict or error dict
    """
    tool_func = MCP_TOOLS.get(tool_name)
    if not tool_func:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        result = tool_func(**kwargs)
        return json.loads(result)
    except Exception as e:
        return {"error": str(e)}


def get_rules() -> List[Dict[str, Any]]:
    """
    Get all governance rules.

    Returns:
        List of rule dicts with rule_id, title, status, category
    """
    result = call_mcp_tool('governance_query_rules')

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('rules', []) if isinstance(result, dict) else []


def get_rules_by_category() -> Dict[str, List[Dict]]:
    """
    Group rules by category.

    Pure function: computes grouping from rules list.

    Returns:
        Dict of category -> rules list
    """
    rules = get_rules()
    grouped: Dict[str, List[Dict]] = {}

    for rule in rules:
        category = rule.get('category', 'unknown')
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(rule)

    return grouped


def get_decisions() -> List[Dict[str, Any]]:
    """
    Get all strategic decisions.

    Returns:
        List of decision dicts
    """
    result = call_mcp_tool('governance_list_decisions')

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('decisions', []) if isinstance(result, dict) else []


def get_sessions(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent sessions.

    Args:
        limit: Max number of sessions

    Returns:
        List of session dicts
    """
    result = call_mcp_tool('governance_list_sessions', limit=limit)

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('sessions', []) if isinstance(result, dict) else []


def get_tasks() -> List[Dict[str, Any]]:
    """
    Get R&D tasks.

    Returns:
        List of task dicts
    """
    result = call_mcp_tool('governance_list_tasks')

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('tasks', []) if isinstance(result, dict) else []


def search_evidence(query: str) -> List[Dict[str, Any]]:
    """
    Search evidence documents.

    Args:
        query: Search query

    Returns:
        List of matching evidence
    """
    result = call_mcp_tool('governance_evidence_search', query=query)

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('results', []) if isinstance(result, dict) else []
