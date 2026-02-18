"""
DSM Tracker Exports (GAP-FILE-007)
==================================
DSM backward compatibility exports for test imports.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-007: Extracted from mcp_server.py

Created: 2024-12-28
"""

import json
import logging

logger = logging.getLogger(__name__)

# Try to import DSM tracker
try:
    from governance.dsm_tracker import get_tracker
    _DSM_AVAILABLE = True
except ImportError:
    _DSM_AVAILABLE = False


def dsm_start(batch_id=None):
    """Start DSM cycle (backward compat export)."""
    if not _DSM_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})
    tracker = get_tracker()
    try:
        cycle = tracker.start_cycle(batch_id)
        return json.dumps({
            "cycle_id": cycle.cycle_id,
            "batch_id": cycle.batch_id,
            "current_phase": cycle.current_phase,
            "message": f"DSM cycle started: {cycle.cycle_id}"
        }, indent=2)
    except ValueError as e:
        logger.warning(f"dsm_start failed: {type(e).__name__}", exc_info=True)
        return json.dumps({"error": type(e).__name__})  # BUG-476-CDS-1


def dsm_advance():
    """Advance DSM phase (backward compat export)."""
    if not _DSM_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})
    tracker = get_tracker()
    try:
        new_phase = tracker.advance_phase()
        return json.dumps({
            "new_phase": new_phase.value,
            "message": f"Advanced to phase: {new_phase.value}",
            "required_mcps": new_phase.required_mcps
        }, indent=2)
    except ValueError as e:
        logger.warning(f"dsm_advance failed: {type(e).__name__}", exc_info=True)
        return json.dumps({"error": type(e).__name__})  # BUG-476-CDS-2


def dsm_checkpoint(description, metrics=None, evidence=None):
    """Record DSM checkpoint (backward compat export)."""
    if not _DSM_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})
    tracker = get_tracker()
    parsed_metrics = None
    if metrics:
        try:
            parsed_metrics = json.loads(metrics) if isinstance(metrics, str) else metrics
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid metrics JSON: {metrics}"})
    try:
        checkpoint = tracker.checkpoint(description=description, metrics=parsed_metrics, evidence=evidence)
        return json.dumps({
            "phase": checkpoint.phase,
            "description": checkpoint.description,
            "timestamp": checkpoint.timestamp,
            "message": "Checkpoint recorded"
        }, indent=2)
    except ValueError as e:
        logger.warning(f"dsm_checkpoint failed: {type(e).__name__}", exc_info=True)
        return json.dumps({"error": type(e).__name__})  # BUG-476-CDS-3


def dsm_status():
    """Get DSM status (backward compat export)."""
    if not _DSM_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})
    tracker = get_tracker()
    return json.dumps(tracker.get_status(), indent=2)


def dsm_complete():
    """Complete DSM cycle (backward compat export)."""
    if not _DSM_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})
    tracker = get_tracker()
    try:
        evidence_path = tracker.complete_cycle()
        return json.dumps({
            "status": "completed",
            "evidence_path": evidence_path,
            "message": f"Cycle completed. Evidence: {evidence_path}"
        }, indent=2)
    except ValueError as e:
        logger.warning(f"dsm_complete failed: {type(e).__name__}", exc_info=True)
        return json.dumps({"error": type(e).__name__})  # BUG-476-CDS-4


def dsm_finding(finding_type, description, severity="MEDIUM", related_rules=None):
    """Add DSM finding (backward compat export)."""
    if not _DSM_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})
    tracker = get_tracker()
    rules = None
    if related_rules:
        rules = [r.strip() for r in related_rules.split(",")] if isinstance(related_rules, str) else related_rules
    try:
        finding = tracker.add_finding(
            finding_type=finding_type,
            description=description,
            severity=severity,
            related_rules=rules
        )
        return json.dumps({
            "finding_id": finding["id"],
            "finding_type": finding_type,
            "severity": severity,
            "related_rules": finding["related_rules"],
            "message": f"Finding recorded: {finding['id']}"
        }, indent=2)
    except ValueError as e:
        logger.warning(f"dsm_finding failed: {type(e).__name__}", exc_info=True)
        return json.dumps({"error": type(e).__name__})  # BUG-476-CDS-5


def dsm_metrics(metrics_json):
    """Update DSM metrics (backward compat export)."""
    if not _DSM_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})
    tracker = get_tracker()
    try:
        metrics = json.loads(metrics_json) if isinstance(metrics_json, str) else metrics_json
    except json.JSONDecodeError:
        return json.dumps({"error": f"Invalid metrics JSON: {metrics_json}"})
    try:
        tracker.update_metrics(metrics)
        return json.dumps({
            "metrics": tracker.current_cycle.metrics if tracker.current_cycle else {},
            "message": "Metrics updated"
        }, indent=2)
    except ValueError as e:
        logger.warning(f"dsm_metrics failed: {type(e).__name__}", exc_info=True)
        return json.dumps({"error": type(e).__name__})  # BUG-476-CDS-6
