"""
DSM Tracker MCP Tools
=====================
Deep Sleep Protocol operations (RULE-012).

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: DSM entity module
"""

import json
from typing import Optional

# Import DSM tracker (with fallback)
try:
    from governance.dsm_tracker import (
        DSMTracker,
        DSPPhase,
        get_tracker,
        reset_tracker
    )
    DSM_TRACKER_AVAILABLE = True
except ImportError:
    DSM_TRACKER_AVAILABLE = False


def register_dsm_tools(mcp) -> None:
    """Register DSM-related MCP tools."""

    @mcp.tool()
    def dsm_start(batch_id: Optional[str] = None) -> str:
        """
        Start a new DSM cycle (RULE-012 Deep Sleep Protocol).

        Args:
            batch_id: Optional batch identifier (e.g., "P4.3", "RD-001")

        Returns:
            JSON object with cycle ID and current phase
        """
        if not DSM_TRACKER_AVAILABLE:
            return json.dumps({"error": "DSMTracker not available"})

        tracker = get_tracker()

        try:
            cycle = tracker.start_cycle(batch_id)
            return json.dumps({
                "cycle_id": cycle.cycle_id,
                "batch_id": cycle.batch_id,
                "current_phase": cycle.current_phase,
                "started_at": cycle.start_time,
                "message": f"DSM cycle started: {cycle.cycle_id}"
            }, indent=2)
        except ValueError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def dsm_advance() -> str:
        """
        Advance to the next DSP phase.

        Phase sequence: IDLE → AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE → DREAM → REPORT

        Returns:
            JSON object with new phase and required MCPs
        """
        if not DSM_TRACKER_AVAILABLE:
            return json.dumps({"error": "DSMTracker not available"})

        tracker = get_tracker()

        try:
            new_phase = tracker.advance_phase()
            return json.dumps({
                "new_phase": new_phase.value,
                "required_mcps": new_phase.required_mcps,
                "message": f"Advanced to phase: {new_phase.value}"
            }, indent=2)
        except ValueError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def dsm_checkpoint(
        description: str,
        metrics: Optional[str] = None,
        evidence: Optional[str] = None
    ) -> str:
        """
        Record a checkpoint in the current phase.

        Args:
            description: What was accomplished
            metrics: Optional JSON metrics (e.g., '{"tests_passed": 78}')
            evidence: Optional evidence reference (file path or URL)

        Returns:
            JSON object with checkpoint details
        """
        if not DSM_TRACKER_AVAILABLE:
            return json.dumps({"error": "DSMTracker not available"})

        tracker = get_tracker()

        # Parse optional JSON metrics
        parsed_metrics = None
        if metrics:
            try:
                parsed_metrics = json.loads(metrics)
            except json.JSONDecodeError:
                return json.dumps({"error": f"Invalid metrics JSON: {metrics}"})

        try:
            checkpoint = tracker.checkpoint(
                description=description,
                metrics=parsed_metrics,
                evidence=evidence
            )
            return json.dumps({
                "phase": checkpoint.phase,
                "description": checkpoint.description,
                "timestamp": checkpoint.timestamp,
                "metrics": checkpoint.metrics,
                "evidence": checkpoint.evidence,
                "message": "Checkpoint recorded"
            }, indent=2)
        except ValueError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def dsm_finding(
        finding_type: str,
        description: str,
        severity: str = "MEDIUM",
        related_rules: Optional[str] = None
    ) -> str:
        """
        Add a finding to the current cycle.

        Args:
            finding_type: Type of finding (gap, issue, improvement, observation)
            description: Description of the finding
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            related_rules: Comma-separated rule IDs (e.g., "RULE-001,RULE-004")

        Returns:
            JSON object with finding ID and details
        """
        if not DSM_TRACKER_AVAILABLE:
            return json.dumps({"error": "DSMTracker not available"})

        tracker = get_tracker()

        # Parse related rules
        rules = None
        if related_rules:
            rules = [r.strip() for r in related_rules.split(",")]

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
                "description": description,
                "severity": severity,
                "related_rules": rules or [],
                "message": f"Finding recorded: {finding['id']}"
            }, indent=2)
        except ValueError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def dsm_status() -> str:
        """
        Get current DSM cycle status.

        Returns:
            JSON object with current phase, checkpoints, findings, and metrics
        """
        if not DSM_TRACKER_AVAILABLE:
            return json.dumps({"error": "DSMTracker not available"})

        tracker = get_tracker()
        status = tracker.get_status()

        return json.dumps(status, indent=2)

    @mcp.tool()
    def dsm_complete() -> str:
        """
        Complete the current DSM cycle and generate evidence.

        Returns:
            JSON object with evidence path and cycle summary
        """
        if not DSM_TRACKER_AVAILABLE:
            return json.dumps({"error": "DSMTracker not available"})

        tracker = get_tracker()

        try:
            evidence_path = tracker.complete_cycle()
            return json.dumps({
                "status": "completed",
                "evidence_path": evidence_path,
                "completed_cycles": len(tracker.completed_cycles),
                "message": f"Cycle completed. Evidence: {evidence_path}"
            }, indent=2)
        except ValueError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def dsm_metrics(metrics_json: str) -> str:
        """
        Update metrics for the current cycle.

        Args:
            metrics_json: JSON object with metrics (e.g., '{"tests_passed": 78, "coverage": 85}')

        Returns:
            JSON object with updated metrics
        """
        if not DSM_TRACKER_AVAILABLE:
            return json.dumps({"error": "DSMTracker not available"})

        tracker = get_tracker()

        try:
            metrics = json.loads(metrics_json)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid metrics JSON: {metrics_json}"})

        try:
            tracker.update_metrics(metrics)
            return json.dumps({
                "metrics": tracker.current_cycle.metrics,
                "message": "Metrics updated"
            }, indent=2)
        except ValueError as e:
            return json.dumps({"error": str(e)})
