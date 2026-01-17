"""
Tasks Workflow Helpers.

Per DOC-SIZE-01-v1: Extracted from workflow.py (414→~280 lines)
Per WORKFLOW-SEQ-01-v1: Verification hierarchy (L1→L2→L3)
Per GAP-UI-046: Resolution (IMPLEMENTED→VALIDATED→CERTIFIED)

Created: 2026-01-17 (GAP-FILE-029)
"""

from typing import Optional, Literal, Tuple
import logging

from governance.task_lifecycle import (
    TaskResolution,
    get_resolution_for_close,
    validate_resolution_transition,
)
from governance.stores import record_audit

logger = logging.getLogger(__name__)

# Verification level descriptions per WORKFLOW-SEQ-01-v1
VERIFICATION_DESCRIPTIONS = {
    "L1": "Technical fix verified",
    "L2": "E2E functionality verified",
    "L3": "Full user flow verified",
}


def enrich_evidence_with_verification(
    evidence: Optional[str],
    verification_level: Optional[Literal["L1", "L2", "L3"]],
    is_promotion: bool = False
) -> str:
    """
    Enrich evidence with verification level metadata.

    Args:
        evidence: Original evidence text
        verification_level: L1, L2, or L3 per WORKFLOW-SEQ-01-v1
        is_promotion: True if this is a resolution promotion (uses different prefix)

    Returns:
        Enriched evidence string with verification metadata prepended
    """
    enriched = evidence or ""

    if verification_level:
        prefix = "Promotion" if is_promotion else "Verification"
        description = VERIFICATION_DESCRIPTIONS.get(verification_level, "")
        verification_info = f"[{prefix}: {verification_level}] {description}"
        enriched = f"{verification_info} {enriched}".strip()

    return enriched


def determine_resolution(
    current_resolution: TaskResolution,
    has_evidence: bool,
    has_tests: bool,
    has_user_feedback: bool,
    verification_level: Optional[Literal["L1", "L2", "L3"]] = None
) -> TaskResolution:
    """
    Determine task resolution based on evidence quality.

    Per GAP-UI-046:
    - IMPLEMENTED: Evidence provided but no tests
    - VALIDATED: Tests pass (has_tests=True or verification_level=L2/L3)
    - CERTIFIED: User feedback received (has_user_feedback=True or verification_level=L3)
    """
    # L2/L3 verification implies tests pass
    effective_has_tests = has_tests or verification_level in ("L2", "L3")
    # L3 verification implies user acceptance
    effective_has_feedback = has_user_feedback or verification_level == "L3"

    return get_resolution_for_close(
        current_resolution=current_resolution,
        has_evidence=has_evidence,
        has_tests=effective_has_tests,
        has_user_feedback=effective_has_feedback
    )


def validate_promotion(
    current_resolution: TaskResolution,
    target_resolution: TaskResolution
) -> Tuple[bool, Optional[str]]:
    """
    Validate resolution promotion transition.

    Valid transitions:
    - IMPLEMENTED → VALIDATED
    - IMPLEMENTED → CERTIFIED
    - VALIDATED → CERTIFIED
    """
    if validate_resolution_transition(current_resolution, target_resolution):
        return True, None

    return False, f"Cannot promote from {current_resolution.value} to {target_resolution.value}"


def combine_evidence(existing: Optional[str], new: str) -> str:
    """Combine existing evidence with new evidence using markdown separator."""
    if existing:
        return f"{existing}\n---\n{new}"
    return new


def try_link_task_to_session(
    client,
    task_id: str,
    session_id: Optional[str],
    context: str = "completion"
) -> bool:
    """
    Link a task to a session for traceability.

    Per EPIC-DR-006: Establishes session→task traceability.
    """
    if not session_id:
        return False

    try:
        client.link_task_to_session(task_id, session_id)
        logger.info(f"Linked task {task_id} to session {session_id} ({context})")
        return True
    except Exception as link_err:
        logger.warning(f"Failed to link task {task_id} to session {session_id}: {link_err}")
        return False


def record_completion_audit(
    task_id: str,
    agent_id: Optional[str],
    old_status: str,
    new_status: str,
    resolution: str,
    verification_level: Optional[str],
    session_id: Optional[str]
) -> None:
    """
    Record task completion in audit trail.

    Per RD-DEBUG-AUDIT: All task state changes logged with correlation_id.
    """
    record_audit(
        action_type="COMPLETE",
        entity_type="task",
        entity_id=task_id,
        actor_id=agent_id or "unknown",
        old_value=old_status,
        new_value=new_status,
        applied_rules=["WORKFLOW-SEQ-01-v1"],
        metadata={
            "resolution": resolution,
            "verification_level": verification_level,
            "session_id": session_id
        }
    )


def update_agent_metrics_on_claim_fallback(
    agent_id: str,
    agents_store: dict,
    agent_base_config: dict,
    calculate_trust_score_fn,
    load_metrics_fn,
    save_metrics_fn
) -> None:
    """
    Update agent metrics when task is claimed (in-memory fallback).

    Per TODO-6: Agent Task Backlog UI - track agent metrics.
    """
    from datetime import datetime

    if agent_id not in agents_store:
        return

    agents_store[agent_id]["tasks_executed"] += 1
    agents_store[agent_id]["last_active"] = datetime.now().isoformat()

    base_trust = agent_base_config.get(agent_id, {}).get("base_trust", 0.85)
    agents_store[agent_id]["trust_score"] = calculate_trust_score_fn(
        agent_id, agents_store[agent_id]["tasks_executed"], base_trust
    )

    metrics = load_metrics_fn()
    metrics[agent_id] = {
        "tasks_executed": agents_store[agent_id]["tasks_executed"],
        "last_active": agents_store[agent_id]["last_active"]
    }
    save_metrics_fn(metrics)
