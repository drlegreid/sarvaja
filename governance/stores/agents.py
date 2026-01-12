"""
Governance Stores - Agent Configuration and Metrics.

Per RULE-032: Modularized from stores.py (503 lines).
Contains: Agent config, metrics persistence, trust score calculation.
"""

import os
import json
import math
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# =============================================================================
# AGENT CONFIGURATION AND METRICS
# =============================================================================

_AGENT_METRICS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "agent_metrics.json")

# Base agent definitions (static config - fallback if TypeDB unavailable)
# Per GAP-AGENT-004: Added capabilities field
_AGENT_BASE_CONFIG = {
    "task-orchestrator": {
        "name": "Task Orchestrator",
        "agent_type": "orchestrator",
        "base_trust": 0.95,
        "capabilities": ["task_management", "delegation", "priority_assignment"],
    },
    "rules-curator": {
        "name": "Rules Curator",
        "agent_type": "curator",
        "base_trust": 0.90,
        "capabilities": ["rule_creation", "rule_modification", "compliance_review"],
    },
    "research-agent": {
        "name": "Research Agent",
        "agent_type": "researcher",
        "base_trust": 0.85,
        "capabilities": ["web_search", "document_analysis", "knowledge_synthesis"],
    },
    "code-agent": {
        "name": "Code Agent",
        "agent_type": "coder",
        "base_trust": 0.88,
        "capabilities": ["code_generation", "refactoring", "test_writing"],
    },
    "local-assistant": {
        "name": "Local Assistant",
        "agent_type": "assistant",
        "base_trust": 0.92,
        "capabilities": ["file_operations", "command_execution", "session_management"],
    },
}


def _load_agent_metrics() -> Dict[str, Dict[str, Any]]:
    """Load persistent agent metrics from JSON file. Per P11.9."""
    metrics = {}
    if os.path.exists(_AGENT_METRICS_FILE):
        try:
            with open(_AGENT_METRICS_FILE, "r") as f:
                metrics = json.load(f)
        except Exception:
            pass
    return metrics


def _save_agent_metrics(metrics: Dict[str, Any]) -> None:
    """Save agent metrics to JSON file. Per P11.9."""
    os.makedirs(os.path.dirname(_AGENT_METRICS_FILE), exist_ok=True)
    with open(_AGENT_METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)


def _calculate_trust_score(agent_id: str, tasks_executed: int, base_trust: float) -> float:
    """
    Calculate trust score from real metrics.
    Per P11.9: GAP-AGENT-001 fix.

    Formula: base_trust * (1 + log10(tasks + 1) * 0.05)
    - New agents start at base_trust
    - Trust increases logarithmically with tasks executed
    - Max boost is ~15% after 1000 tasks
    """
    if tasks_executed == 0:
        return base_trust
    # Logarithmic growth: more tasks = higher trust, but diminishing returns
    task_boost = math.log10(tasks_executed + 1) * 0.05
    return min(1.0, base_trust * (1 + task_boost))


def _build_agents_store() -> Dict[str, Dict[str, Any]]:
    """Build agents store with persistent metrics merged with base config."""
    metrics = _load_agent_metrics()
    agents = {}

    for agent_id, config in _AGENT_BASE_CONFIG.items():
        agent_metrics = metrics.get(agent_id, {})
        tasks_executed = agent_metrics.get("tasks_executed", 0)
        last_active = agent_metrics.get("last_active", None)

        agents[agent_id] = {
            "agent_id": agent_id,
            "name": config["name"],
            "agent_type": config["agent_type"],
            "status": "ACTIVE",
            "tasks_executed": tasks_executed,
            "trust_score": _calculate_trust_score(agent_id, tasks_executed, config["base_trust"]),
            "last_active": last_active,
            # Per GAP-AGENT-004: Include capabilities
            "capabilities": config.get("capabilities", []),
        }

    return agents


# Initialize agents store with persistent metrics
_agents_store: Dict[str, Dict[str, Any]] = _build_agents_store()


def _update_agent_metrics_on_claim(agent_id: str) -> None:
    """
    Update agent metrics when a task is claimed.
    Per P11.9: Centralized agent metrics update.
    """
    if agent_id in _agents_store:
        _agents_store[agent_id]["tasks_executed"] += 1
        _agents_store[agent_id]["last_active"] = datetime.now().isoformat()

        # Recalculate trust score
        base_trust = _AGENT_BASE_CONFIG.get(agent_id, {}).get("base_trust", 0.85)
        _agents_store[agent_id]["trust_score"] = _calculate_trust_score(
            agent_id,
            _agents_store[agent_id]["tasks_executed"],
            base_trust
        )

        # Persist metrics
        metrics = _load_agent_metrics()
        metrics[agent_id] = {
            "tasks_executed": _agents_store[agent_id]["tasks_executed"],
            "last_active": _agents_store[agent_id]["last_active"]
        }
        _save_agent_metrics(metrics)


def get_available_agents_for_chat() -> List[Dict[str, Any]]:
    """Get agents available for chat."""
    return list(_agents_store.values())


def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get a specific agent by ID."""
    return _agents_store.get(agent_id)


def get_all_agents() -> List[Dict[str, Any]]:
    """Get all registered agents."""
    return list(_agents_store.values())
