"""
Real-Time Monitoring Functions (GAP-FILE-006)
==============================================
Real-time monitoring for P9.6.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py
Per GAP-MONITOR-IPC-001: Audit file bridge for cross-process events

Created: 2024-12-28
Updated: 2026-01-20 - Added audit file writer for IPC
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Audit file directory (relative to workspace root)
_AUDIT_LOG_DIR: Optional[Path] = None


def _get_audit_log_dir() -> Path:
    """Get or initialize the audit log directory."""
    global _AUDIT_LOG_DIR
    if _AUDIT_LOG_DIR is None:
        # Find workspace root (contains CLAUDE.md or TODO.md)
        current = Path(__file__).resolve()
        for _ in range(10):
            current = current.parent
            if (current / "CLAUDE.md").exists() or (current / "TODO.md").exists():
                _AUDIT_LOG_DIR = current / "logs" / "monitor"
                break
        if _AUDIT_LOG_DIR is None:
            _AUDIT_LOG_DIR = Path("/tmp/logs/monitor")
        _AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _AUDIT_LOG_DIR


def _write_audit_event(event: Dict[str, Any]) -> None:
    """
    Write event to audit file (JSONL format).

    Per GAP-MONITOR-IPC-001: Enables cross-process event sharing.
    """
    try:
        log_dir = _get_audit_log_dir()
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"{today}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        pass  # Don't fail monitoring if audit write fails

# Singleton monitor instance
_monitor_instance = None


def get_rule_monitor():
    """
    Get or create singleton RuleMonitor instance.

    Returns:
        RuleMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        from agent.rule_monitor import create_rule_monitor
        _monitor_instance = create_rule_monitor()
    return _monitor_instance


def get_monitor_feed(limit: int = 50, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get monitoring event feed.

    Per GAP-MONITOR-IPC-001: Merges events from in-memory monitor and audit files.
    This enables cross-process event visibility in the Dashboard.

    Args:
        limit: Maximum events to return
        event_type: Optional filter by event type

    Returns:
        List of events (newest first)
    """
    # Get in-memory events
    monitor = get_rule_monitor()
    memory_events = monitor.get_feed(limit=limit, event_type=event_type)

    # Get audit file events (cross-process events from MCP tools)
    try:
        audit_events = read_audit_events(days=1, limit=limit, event_type=event_type)
    except Exception:
        audit_events = []

    # Merge and deduplicate by event_id
    seen_ids = set()
    merged = []

    for event in memory_events:
        event_id = event.get("id") or event.get("event_id")
        if event_id and event_id not in seen_ids:
            seen_ids.add(event_id)
            merged.append(event)

    for event in audit_events:
        event_id = event.get("event_id")
        if event_id and event_id not in seen_ids:
            seen_ids.add(event_id)
            # Normalize audit event format to match monitor format
            merged.append({
                "id": event_id,
                "type": event.get("event_type"),
                "source": event.get("source"),
                "details": event.get("details", {}),
                "severity": event.get("severity", "INFO"),
                "timestamp": event.get("timestamp"),
            })
        elif not event_id:
            # Include events without IDs (older format)
            merged.append({
                "type": event.get("event_type"),
                "source": event.get("source"),
                "details": event.get("details", {}),
                "severity": event.get("severity", "INFO"),
                "timestamp": event.get("timestamp"),
            })

    # Sort by timestamp descending
    merged.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return merged[:limit]


def get_monitor_alerts(acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
    """
    Get active monitoring alerts.

    Args:
        acknowledged: Optional filter by acknowledged status

    Returns:
        List of alerts
    """
    monitor = get_rule_monitor()
    return monitor.get_alerts(acknowledged=acknowledged)


def get_monitor_stats() -> Dict[str, Any]:
    """
    Get monitoring statistics.

    Returns:
        Stats dict with event counts, alerts, etc.
    """
    monitor = get_rule_monitor()
    return monitor.get_statistics()


def log_monitor_event(
    event_type: str,
    source: str,
    details: Dict[str, Any],
    severity: str = "INFO"
) -> Dict[str, Any]:
    """
    Log a governance event.

    Per GAP-MONITOR-IPC-001: Events written to both in-memory monitor
    and audit file for cross-process sharing.

    Args:
        event_type: Type of event (rule_query, violation, rule_change, etc.)
        source: Event source (agent ID, user, etc.)
        details: Event details
        severity: Event severity (INFO, WARNING, CRITICAL)

    Returns:
        Event record
    """
    monitor = get_rule_monitor()
    event = monitor.log_event(event_type, source, details, severity)

    # Write to audit file for cross-process access (GAP-MONITOR-IPC-001)
    _write_audit_event({
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "source": source,
        "details": details,
        "severity": severity,
        "event_id": event.get("id") if isinstance(event, dict) else None,
    })

    return event


def acknowledge_monitor_alert(alert_id: str) -> Dict[str, Any]:
    """
    Acknowledge an alert.

    Args:
        alert_id: Alert ID to acknowledge

    Returns:
        Result dict
    """
    monitor = get_rule_monitor()
    return monitor.acknowledge_alert(alert_id)


def get_top_monitored_rules(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most frequently accessed rules.

    Args:
        limit: Number of rules to return

    Returns:
        List of rules with access counts
    """
    monitor = get_rule_monitor()
    return monitor.get_top_rules(limit=limit)


def get_hourly_monitor_stats() -> Dict[str, Any]:
    """
    Get hourly monitoring statistics.

    Returns:
        Hourly stats dict
    """
    monitor = get_rule_monitor()
    return monitor.get_hourly_stats()


def read_audit_events(
    days: int = 1,
    limit: int = 100,
    event_type: Optional[str] = None,
    severity: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Read events from audit files.

    Per GAP-MONITOR-IPC-001: Cross-process event reading.

    Args:
        days: Number of days to read (default 1)
        limit: Max events to return
        event_type: Optional filter by event type
        severity: Optional filter by severity

    Returns:
        List of events (newest first)
    """
    events = []
    log_dir = _get_audit_log_dir()

    # Read files for requested days
    for day_offset in range(days):
        date = datetime.now()
        if day_offset > 0:
            from datetime import timedelta
            date = date - timedelta(days=day_offset)
        log_file = log_dir / f"{date.strftime('%Y-%m-%d')}.jsonl"

        if not log_file.exists():
            continue

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        # Apply filters
                        if event_type and event.get("event_type") != event_type:
                            continue
                        if severity and event.get("severity") != severity:
                            continue
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            continue

    # Sort by timestamp descending and limit
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return events[:limit]
