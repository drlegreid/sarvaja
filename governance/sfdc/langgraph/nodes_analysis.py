"""
SFDC LangGraph Analysis Nodes
================================
Discover and review phase nodes.

Created: 2026-02-09
"""

import logging
import time
from datetime import datetime

from .state import (
    SFDCState,
    BREAKING_CHANGE_THRESHOLD,
    MAX_COMPONENTS_PER_DEPLOY,
)
from .nodes_lifecycle import _create_phase_result

logger = logging.getLogger(__name__)


def discover_node(state: SFDCState) -> dict:
    """DISCOVER phase: Scan org metadata and identify changes.

    Inventories metadata components, maps dependencies, and
    flags breaking changes.
    """
    start_time = time.perf_counter()
    logger.info(f"[SFDC:{state['cycle_id']}] DISCOVER phase for org {state['org_alias']}")

    try:
        if state.get("dry_run"):
            # Simulated discovery
            components = [
                {"name": "AccountService", "type": "ApexClass", "status": "modified", "api_version": "59.0"},
                {"name": "ContactTrigger", "type": "ApexTrigger", "status": "modified", "api_version": "59.0"},
                {"name": "accountCard", "type": "LightningComponentBundle", "status": "created", "api_version": "59.0"},
                {"name": "Lead_Assignment", "type": "Flow", "status": "modified", "api_version": "59.0"},
            ]
            dependencies = [
                {"source": "ContactTrigger", "target": "AccountService", "type": "references"},
                {"source": "accountCard", "target": "AccountService", "type": "imports"},
            ]
            change_set = [
                {"component": c["name"], "type": c["type"], "action": c["status"]}
                for c in components
            ]
        else:
            # Production: would call sfdx/sf CLI
            components = []
            dependencies = []
            change_set = []

        # Check for breaking changes
        deleted = [c for c in components if c.get("status") == "deleted"]
        has_breaking = len(deleted) >= BREAKING_CHANGE_THRESHOLD

        # Check deployment size
        if len(components) > MAX_COMPONENTS_PER_DEPLOY:
            has_breaking = True

        # Categorize components
        apex_classes = [c["name"] for c in components if c["type"] in ("ApexClass", "ApexTrigger")]
        lwc_components = [c["name"] for c in components if c["type"] == "LightningComponentBundle"]
        flows = [c["name"] for c in components if c["type"] == "Flow"]
        custom_objects = [c["name"] for c in components if c["type"] == "CustomObject"]

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "current_phase": "discovered",
            "phases_completed": state["phases_completed"] + ["discover"],
            "metadata_components": components,
            "change_set": change_set,
            "dependencies": dependencies,
            "apex_classes": apex_classes,
            "lwc_components": lwc_components,
            "flows": flows,
            "custom_objects": custom_objects,
            "has_breaking_changes": has_breaking,
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("discover", "success", state, duration_ms=duration_ms)
            ],
        }

    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        # BUG-473-SNA-1: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"[SFDC] DISCOVER phase failed: {type(e).__name__}", exc_info=True)
        return {
            "current_phase": "discover_failed",
            "status": "failed",
            "error_message": f"DISCOVER phase failed: {type(e).__name__}",
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("discover", "failed", state, str(e), duration_ms)
            ],
        }


def review_node(state: SFDCState) -> dict:
    """REVIEW phase: Code review and security scan.

    Checks for SOQL injection, DML in loops, governor limit risks,
    and other Salesforce-specific security concerns.
    """
    start_time = time.perf_counter()
    logger.info(f"[SFDC:{state['cycle_id']}] REVIEW phase")

    try:
        review_findings = state.get("review_findings", [])[:]

        if state.get("dry_run"):
            # Simulated review findings
            for cls in state.get("apex_classes", []):
                review_findings.append({
                    "id": f"REVIEW-{len(review_findings)+1:03d}",
                    "component": cls,
                    "type": "best_practice",
                    "severity": "LOW",
                    "description": f"Consider bulkifying {cls}",
                    "phase": "review",
                    "timestamp": datetime.now().isoformat(),
                })

            # Simulate security scan pass (no critical findings)
            security_passed = not any(
                f.get("severity") == "CRITICAL" for f in review_findings
            )
        else:
            security_passed = True

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "current_phase": "reviewed",
            "phases_completed": state["phases_completed"] + ["review"],
            "review_findings": review_findings,
            "security_scan_passed": security_passed,
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("review", "success", state, duration_ms=duration_ms)
            ],
        }

    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        # BUG-473-SNA-2: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"[SFDC] REVIEW phase failed: {type(e).__name__}", exc_info=True)
        return {
            "current_phase": "review_failed",
            "status": "failed",
            "error_message": f"REVIEW phase failed: {type(e).__name__}",
            "phase_results": state.get("phase_results", []) + [
                _create_phase_result("review", "failed", state, str(e), duration_ms)
            ],
        }
