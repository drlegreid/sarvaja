"""Capability Service — Rule→Agent binding CRUD.

The critical missing link in the entity chain:
Project → Workspace → Agent → **Capabilities** → Tasks → Sessions

A capability binds a rule to an agent, optionally within a category (coding,
testing, governance, research). This determines which rules constrain which
agents and enables compliance validation.

Dual-store: in-memory primary with TypeDB persistence (best-effort).
Per P2-12: TypeDB persistence via agent-capability relation.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from governance.stores.audit import record_audit
from governance.stores.config import get_typedb_client

logger = logging.getLogger(__name__)


def _monitor(action: str, entity_id: str, source: str = "service", **extra):
    """Log capability monitoring event for MCP compliance. Per P3-14."""
    try:
        from governance.mcp_tools.common import log_monitor_event
        log_monitor_event(
            event_type="capability_event",
            source=source,
            details={"entity_id": entity_id, "action": action, **extra},
            severity="INFO",
        )
    except Exception as e:
        logger.warning(f"Monitor event failed for capability {entity_id}: {type(e).__name__}", exc_info=True)


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


def _persist_to_typedb(agent_id: str, rule_id: str, category: str, status: str) -> None:
    """Best-effort persist capability to TypeDB."""
    try:
        client = get_typedb_client()
        if client:
            client.create_capability(agent_id, rule_id, category, status)
    except Exception as e:
        # P3-14: Add exc_info for stack trace consistency
        logger.warning(f"TypeDB persist failed for {agent_id}→{rule_id}: {type(e).__name__}", exc_info=True)


def _delete_from_typedb(agent_id: str, rule_id: str) -> None:
    """Best-effort delete capability from TypeDB."""
    try:
        client = get_typedb_client()
        if client:
            client.delete_capability(agent_id, rule_id)
    except Exception as e:
        # P3-14: Add exc_info for stack trace consistency
        logger.warning(f"TypeDB delete failed for {agent_id}→{rule_id}: {type(e).__name__}", exc_info=True)


def _update_status_in_typedb(agent_id: str, rule_id: str, status: str) -> None:
    """Best-effort update capability status in TypeDB."""
    try:
        client = get_typedb_client()
        if client:
            client.update_capability_status(agent_id, rule_id, status)
    except Exception as e:
        # P3-14: Add exc_info for stack trace consistency
        logger.warning(f"TypeDB status update failed for {agent_id}→{rule_id}: {type(e).__name__}", exc_info=True)


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


def sync_to_typedb() -> Dict[str, int]:
    """Sync all in-memory capabilities to TypeDB. Called on startup."""
    _seed_defaults()
    synced = 0
    failed = 0
    client = get_typedb_client()
    if not client:
        return {"synced": 0, "failed": 0, "skipped": len(_capabilities_store)}
    for entry in _capabilities_store.values():
        try:
            ok = client.create_capability(
                entry["agent_id"], entry["rule_id"],
                entry["category"], entry["status"],
            )
            if ok:
                synced += 1
            else:
                failed += 1
        except Exception:
            failed += 1
    logger.info(f"Capability sync: {synced} synced, {failed} failed")
    return {"synced": synced, "failed": failed, "skipped": 0}


def load_from_typedb() -> int:
    """Load capabilities from TypeDB into memory (startup merge)."""
    client = get_typedb_client()
    if not client:
        return 0
    try:
        typedb_caps = client.get_all_capabilities()
        loaded = 0
        for cap in typedb_caps:
            k = _key(cap["agent_id"], cap["rule_id"])
            if k not in _capabilities_store:
                _capabilities_store[k] = {
                    **cap,
                    "created_at": datetime.now().isoformat(),
                }
                loaded += 1
        if loaded:
            logger.info(f"Loaded {loaded} capabilities from TypeDB")
        return loaded
    except Exception as e:
        # P3-14: Sanitize message + add exc_info for consistency
        logger.warning(f"Failed to load capabilities from TypeDB: {type(e).__name__}", exc_info=True)
        return 0


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
    _persist_to_typedb(agent_id, rule_id, category, "active")
    record_audit("CREATE", "capability", k,
                 metadata={"agent_id": agent_id, "rule_id": rule_id, "source": source})
    logger.info(f"Bound rule {rule_id} to agent {agent_id} (category={category})")
    _monitor("bind", k, source=source, agent_id=agent_id, rule_id=rule_id)
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
    _delete_from_typedb(agent_id, rule_id)
    record_audit("DELETE", "capability", k,
                 metadata={"agent_id": agent_id, "rule_id": rule_id, "source": source})
    _monitor("unbind", k, source=source, agent_id=agent_id, rule_id=rule_id)
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
    _update_status_in_typedb(agent_id, rule_id, status)
    record_audit("UPDATE", "capability", k,
                 old_value=old_status, new_value=status,
                 metadata={"source": source})
    _monitor("status_change", k, source=source, old_status=old_status, new_status=status)
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
