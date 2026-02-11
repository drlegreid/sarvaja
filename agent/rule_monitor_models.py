"""
Rule Monitor Models & Demo Seed Data.

Per DOC-SIZE-01-v1: Extracted from rule_monitor.py (484 lines).
Dataclasses for events/alerts and demo event seeding.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class MonitorEvent:
    """A monitored governance event."""
    event_id: str
    event_type: str
    source: str
    details: Dict[str, Any]
    timestamp: str
    severity: str  # INFO, WARNING, CRITICAL


@dataclass
class Alert:
    """An active alert."""
    alert_id: str
    event_id: str
    rule_id: Optional[str]
    message: str
    severity: str
    acknowledged: bool
    timestamp: str


# Demo events for UI demonstration (GAP-UI-051).
# Uses semantic rule IDs per META-TAXON-01-v1.
DEMO_EVENTS: List[Dict[str, Any]] = [
    {
        "event_type": "rule_query",
        "source": "claude-code",
        "details": {"rule_id": "SESSION-EVID-01-v1", "query_type": "get"},
        "severity": "INFO",
    },
    {
        "event_type": "compliance_check",
        "source": "task-orchestrator",
        "details": {"rule_id": "ARCH-MCP-01-v1", "result": "PASS"},
        "severity": "INFO",
    },
    {
        "event_type": "rule_query",
        "source": "rules-curator",
        "details": {"rule_id": "SESSION-DSM-01-v1", "query_type": "dependencies"},
        "severity": "INFO",
    },
    {
        "event_type": "trust_increase",
        "source": "task-orchestrator",
        "details": {"agent_id": "code-agent", "old_trust": 0.85, "new_trust": 0.88},
        "severity": "INFO",
    },
    {
        "event_type": "rule_change",
        "source": "admin",
        "details": {"rule_id": "RECOVER-AMNES-01-v1", "change": "status update"},
        "severity": "WARNING",
    },
    {
        "event_type": "compliance_check",
        "source": "research-agent",
        "details": {"rule_id": "SAFETY-HEALTH-01-v1", "result": "PASS"},
        "severity": "INFO",
    },
    {
        "event_type": "violation",
        "source": "external-api",
        "details": {"rule_id": "ARCH-MCP-01-v1", "violation": "missing MCP healthcheck"},
        "severity": "CRITICAL",
    },
    {
        "event_type": "trust_decrease",
        "source": "governance-system",
        "details": {"agent_id": "external-api", "old_trust": 0.75, "new_trust": 0.60},
        "severity": "WARNING",
    },
]


def seed_demo_events(monitor: "RuleMonitor") -> None:
    """Seed demo events for UI demonstration (GAP-UI-051)."""
    for event in DEMO_EVENTS:
        monitor.log_event(
            event_type=event["event_type"],
            source=event["source"],
            details=event["details"],
            severity=event["severity"],
        )
