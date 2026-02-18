"""
DSP LangGraph Analysis Nodes
==============================
Audit, hypothesize, and measure phase nodes.

Per WORKFLOW-DSP-01-v1: DSP Workflow Stability Requirements
Per DOC-SIZE-01-v1: Modularized from nodes.py (572 lines)

Created: 2026-02-08
"""

import logging
import time
from datetime import datetime

from .state import (
    DSPState,
    MIN_HYPOTHESIS_CHARS,
    CRITICAL_SEVERITY_THRESHOLD,
)
from .nodes_lifecycle import _create_phase_result

logger = logging.getLogger(__name__)


def audit_node(state: DSPState) -> dict:
    """AUDIT phase: Inventory gaps, orphans, and loops.

    Per RULE-012: Uses claude-mem + governance MCPs.
    """
    start_time = time.perf_counter()
    logger.info(f"[DSP:{state['cycle_id']}] AUDIT phase")

    gaps = []
    orphans = []
    findings = state.get("findings", [])[:]
    checkpoints = state.get("checkpoints", [])[:]

    try:
        # Query for gaps (would use MCP in production)
        if state.get("dry_run"):
            gaps = ["GAP-TEST-001", "GAP-TEST-002"]
            orphans = ["ORPHAN-TASK-001"]
        else:
            # Production: Call governance MCP to get gaps
            from governance.mcp_tools.gaps import _get_gap_summary
            gap_data = _get_gap_summary()
            gaps = [g.get("gap_id") for g in gap_data.get("gaps", [])]

        # Check for critical severity
        critical_count = len([g for g in gaps if "CRITICAL" in str(g).upper()])
        has_critical = critical_count >= CRITICAL_SEVERITY_THRESHOLD

        # Record checkpoint
        checkpoints.append({
            "phase": "audit",
            "timestamp": datetime.now().isoformat(),
            "description": f"Audited {len(gaps)} gaps, {len(orphans)} orphans",
            "metrics": {"gaps": len(gaps), "orphans": len(orphans), "critical": critical_count},
        })

        # Record findings
        for gap_id in gaps[:5]:  # Top 5 gaps as findings
            findings.append({
                "id": f"FINDING-AUDIT-{len(findings)+1:03d}",
                "type": "gap",
                "description": f"Gap discovered: {gap_id}",
                "severity": "MEDIUM",
                "phase": "audit",
                "timestamp": datetime.now().isoformat(),
            })

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "current_phase": "audited",
            "phases_completed": state["phases_completed"] + ["audit"],
            "audit_gaps": gaps,
            "audit_orphans": orphans,
            "has_critical_gaps": has_critical,
            "findings": findings,
            "checkpoints": checkpoints,
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("audit", "success", {"checkpoints": checkpoints, "findings": findings}, duration_ms=duration_ms)
            ],
        }

    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        # BUG-410-NOD-001: Don't leak exception text into state/API; add exc_info
        # BUG-473-DNA-1: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"[DSP] AUDIT phase failed: {type(e).__name__}", exc_info=True)
        return {
            "current_phase": "audit_failed",
            "status": "failed",
            "error_message": f"AUDIT phase failed: {type(e).__name__}",
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("audit", "failed", state, type(e).__name__, duration_ms)
            ],
        }


def hypothesize_node(state: DSPState) -> dict:
    """HYPOTHESIZE phase: Form improvement theories.

    Per RULE-012: Uses sequential-thinking MCP.
    """
    start_time = time.perf_counter()
    logger.info(f"[DSP:{state['cycle_id']}] HYPOTHESIZE phase")

    hypotheses = []
    checkpoints = state.get("checkpoints", [])[:]

    try:
        # Generate hypotheses based on audit findings
        for gap in state.get("audit_gaps", [])[:3]:
            hypothesis = f"Addressing {gap} will improve system integrity"
            if len(hypothesis) >= MIN_HYPOTHESIS_CHARS:
                hypotheses.append(hypothesis)

        if not hypotheses:
            hypotheses.append("No actionable gaps found - system is healthy")

        # Record checkpoint
        checkpoints.append({
            "phase": "hypothesize",
            "timestamp": datetime.now().isoformat(),
            "description": f"Generated {len(hypotheses)} improvement hypotheses",
            "metrics": {"hypotheses": len(hypotheses)},
        })

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "current_phase": "hypothesized",
            "phases_completed": state["phases_completed"] + ["hypothesize"],
            "hypotheses": hypotheses,
            "checkpoints": checkpoints,
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("hypothesize", "success", {"checkpoints": checkpoints}, duration_ms=duration_ms)
            ],
        }

    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        # BUG-410-NOD-002: Don't leak exception text into state/API; add exc_info
        # BUG-473-DNA-2: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"[DSP] HYPOTHESIZE phase failed: {type(e).__name__}", exc_info=True)
        return {
            "current_phase": "hypothesize_failed",
            "status": "failed",
            "error_message": f"HYPOTHESIZE phase failed: {type(e).__name__}",
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("hypothesize", "failed", state, type(e).__name__, duration_ms)
            ],
        }


def measure_node(state: DSPState) -> dict:
    """MEASURE phase: Quantify current state.

    Per RULE-012: Uses powershell + llm-sandbox MCPs.
    """
    start_time = time.perf_counter()
    logger.info(f"[DSP:{state['cycle_id']}] MEASURE phase")

    measurements = {}
    checkpoints = state.get("checkpoints", [])[:]

    try:
        # Collect baseline measurements
        measurements = {
            "gaps_count": len(state.get("audit_gaps", [])),
            "orphans_count": len(state.get("audit_orphans", [])),
            "hypotheses_count": len(state.get("hypotheses", [])),
            "timestamp": datetime.now().isoformat(),
        }

        # Record checkpoint
        checkpoints.append({
            "phase": "measure",
            "timestamp": datetime.now().isoformat(),
            "description": f"Collected {len(measurements)} baseline measurements",
            "metrics": measurements,
        })

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "current_phase": "measured",
            "phases_completed": state["phases_completed"] + ["measure"],
            "measurements": measurements,
            "checkpoints": checkpoints,
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("measure", "success", {"checkpoints": checkpoints}, duration_ms=duration_ms)
            ],
        }

    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        # BUG-410-NOD-003: Don't leak exception text into state/API; add exc_info
        # BUG-473-DNA-3: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"[DSP] MEASURE phase failed: {type(e).__name__}", exc_info=True)
        return {
            "current_phase": "measure_failed",
            "status": "failed",
            "error_message": f"MEASURE phase failed: {type(e).__name__}",
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("measure", "failed", state, type(e).__name__, duration_ms)
            ],
        }
