"""Capability Service — Rule→Agent binding CRUD.

The critical missing link in the entity chain:
Project → Workspace → Agent → **Capabilities** → Tasks → Sessions

A capability binds a rule to an agent, optionally within a category (coding,
testing, governance, research). This determines which rules constrain which
agents and enables compliance validation.

In-memory store with TypeDB persistence (same dual-store pattern as agents).
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from governance.stores.audit import record_audit

logger = logging.getLogger(__name__)

# In-memory store: key = "agent_id::rule_id"
_capabilities_store: Dict[str, Dict[str, Any]] = {}

# Seed data: default rule→agent bindings from workspace_registry patterns
_DEFAULT_BINDINGS = {
    "code-agent": {
        "rules": ["TEST-GUARD-01", "TEST-COMP-02", "DOC-SIZE-01", "TEST-FIX-01"],
        "category": "coding",
    },
    "research-agent": {
        "rules": ["SESSION-EVID-01", "GOV-RULE-01", "DOC-LINK-01"],
        "category": "research",
    },
    "curator-agent": {
        "rules": ["GOV-RULE-01", "GOV-BICAM-01", "DOC-LINK-01"],
        "category": "governance",
    },
    "security-agent": {
        "rules": ["SAFETY-HEALTH-01", "SAFETY-DESTR-01"],
        "category": "security",
    },
    "sync-agent": {
        "rules": ["CONTAINER-DEV-01", "ARCH-INFRA-01"],
        "category": "infrastructure",
    },
}


def _key(agent_id: str, rule_id: str) -> str:
    return f"{agent_id}::{rule_id}"


def _seed_defaults() -> None:
    """Seed default bindings if store is empty."""
    if _capabilities_store:
        return
    for agent_id, config in _DEFAULT_BINDINGS.items():
        for rule_id in config["rules"]:
            k = _key(agent_id, rule_id)
            _capabilities_store[k] = {
                "agent_id": agent_id,
                "rule_id": rule_id,
                "category": config["category"],
                "status": "active",
                "created_at": datetime.now().isoformat(),
            }


def bind_rule_to_agent(
    agent_id: str,
    rule_id: str,
    category: str = "general",
    source: str = "service",
) -> Dict[str, Any]:
    """Bind a rule to an agent (create a capability)."""
    _seed_defaults()
    k = _key(agent_id, rule_id)
    if k in _capabilities_store:
        return _capabilities_store[k]

    entry = {
        "agent_id": agent_id,
        "rule_id": rule_id,
        "category": category,
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }
    _capabilities_store[k] = entry
    record_audit("CREATE", "capability", k,
                 metadata={"agent_id": agent_id, "rule_id": rule_id, "source": source})
    logger.info(f"Bound rule {rule_id} to agent {agent_id} (category={category})")
    return entry


def unbind_rule_from_agent(
    agent_id: str,
    rule_id: str,
    source: str = "service",
) -> bool:
    """Remove a rule→agent binding."""
    _seed_defaults()
    k = _key(agent_id, rule_id)
    if k not in _capabilities_store:
        return False
    del _capabilities_store[k]
    record_audit("DELETE", "capability", k,
                 metadata={"agent_id": agent_id, "rule_id": rule_id, "source": source})
    return True


def get_capabilities_for_agent(agent_id: str) -> List[Dict[str, Any]]:
    """Get all rule bindings for an agent."""
    _seed_defaults()
    return [
        v for v in _capabilities_store.values()
        if v["agent_id"] == agent_id
    ]


def get_agents_for_rule(rule_id: str) -> List[Dict[str, Any]]:
    """Get all agents bound to a rule."""
    _seed_defaults()
    return [
        v for v in _capabilities_store.values()
        if v["rule_id"] == rule_id
    ]


def list_capabilities(
    agent_id: Optional[str] = None,
    rule_id: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List all capabilities with optional filters."""
    _seed_defaults()
    result = list(_capabilities_store.values())
    if agent_id:
        result = [c for c in result if c["agent_id"] == agent_id]
    if rule_id:
        result = [c for c in result if c["rule_id"] == rule_id]
    if category:
        result = [c for c in result if c["category"] == category]
    if status:
        result = [c for c in result if c["status"] == status]
    return result


def update_capability_status(
    agent_id: str,
    rule_id: str,
    status: str,
    source: str = "service",
) -> Optional[Dict[str, Any]]:
    """Update status of a capability (active/suspended)."""
    _seed_defaults()
    k = _key(agent_id, rule_id)
    if k not in _capabilities_store:
        return None
    old_status = _capabilities_store[k]["status"]
    _capabilities_store[k]["status"] = status
    record_audit("UPDATE", "capability", k,
                 old_value=old_status, new_value=status,
                 metadata={"source": source})
    return _capabilities_store[k]


def get_capability_summary() -> Dict[str, Any]:
    """Get summary stats for capabilities dashboard."""
    _seed_defaults()
    caps = list(_capabilities_store.values())
    agents = set(c["agent_id"] for c in caps)
    rules = set(c["rule_id"] for c in caps)
    categories = {}
    for c in caps:
        cat = c["category"]
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "total_bindings": len(caps),
        "agents_with_rules": len(agents),
        "rules_applied": len(rules),
        "by_category": categories,
        "active": sum(1 for c in caps if c["status"] == "active"),
        "suspended": sum(1 for c in caps if c["status"] == "suspended"),
    }
