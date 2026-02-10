"""
SFDC LangGraph State Schema
============================
State types and constants for Salesforce Development Lifecycle workflow.

Per UI-TRAME-01-v1: Cross-workspace pattern reuse (from DSP LangGraph)

Graph structure:
    START → discover → [develop | skip_to_report | abort]
                          ↓
    develop → test → review → deploy → validate
       ↑                                  ↓
       └── loop_to_develop ─────── [failed, retries < MAX]
                                          ↓
                     [failed, no retries] → rollback → report → complete → END
                                              ↓
                                          monitor → report → complete → END

Created: 2026-02-09
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any


class PhaseResult(TypedDict):
    """Result from a single SFDC phase execution."""
    phase: str
    status: Literal["success", "failed", "skipped"]
    findings: int
    metrics: Dict[str, Any]
    error: Optional[str]
    duration_ms: int


class MetadataComponent(TypedDict):
    """A Salesforce metadata component."""
    name: str
    type: str  # ApexClass, LightningComponentBundle, Flow, etc.
    status: Literal["created", "modified", "deleted"]
    api_version: Optional[str]


class SFDCState(TypedDict):
    """State that flows through the SFDC workflow.

    Mirrors DSPState pattern for consistency.
    """

    # Cycle identity
    cycle_id: str
    org_alias: str
    target_org: Optional[str]

    # Progress tracking
    current_phase: str
    phases_completed: List[str]
    phase_results: List[PhaseResult]

    # Discovery data
    metadata_components: List[MetadataComponent]
    change_set: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]

    # Development data
    apex_classes: List[str]
    lwc_components: List[str]
    flows: List[str]
    custom_objects: List[str]

    # Test data
    test_results: Dict[str, Any]
    code_coverage: float
    coverage_met: bool

    # Review data
    review_findings: List[Dict[str, Any]]
    security_scan_passed: bool

    # Deployment data
    deployment_id: Optional[str]
    deployment_status: Optional[str]
    deployment_errors: List[str]

    # Validation data
    post_deploy_checks: Dict[str, Any]
    validation_passed: bool

    # Monitoring data
    monitoring_alerts: List[Dict[str, Any]]

    # Decision routing
    has_breaking_changes: bool
    should_skip_monitor: bool

    # Loop control
    retry_count: int

    # Execution mode
    dry_run: bool
    sandbox_only: bool

    # Status
    status: Literal["pending", "running", "success", "failed", "aborted", "rolled_back"]
    error_message: Optional[str]
    abort_reason: Optional[str]
    rollback_reason: Optional[str]

    # Timestamps
    started_at: Optional[str]
    completed_at: Optional[str]


# =============================================================================
# CONSTANTS
# =============================================================================

# Coverage thresholds
MIN_CODE_COVERAGE = 75.0  # Salesforce minimum: 75%
RECOMMENDED_COVERAGE = 85.0

# Cycle limits
MAX_DEPLOY_RETRIES = 3
MAX_CYCLE_HOURS = 8  # SFDC deploys shouldn't take 8+ hours

# Component thresholds
MAX_COMPONENTS_PER_DEPLOY = 500  # Large deployments are risky
BREAKING_CHANGE_THRESHOLD = 10  # Skip if too many breaking changes


def create_initial_state(
    org_alias: str = "default",
    target_org: Optional[str] = None,
    dry_run: bool = False,
    sandbox_only: bool = True,
) -> SFDCState:
    """Create initial SFDC cycle state.

    Args:
        org_alias: Source Salesforce org alias
        target_org: Target org for deployment (None = same as source)
        dry_run: If True, simulate without actual deployment
        sandbox_only: If True, only deploy to sandbox orgs

    Returns:
        Initial SFDCState for workflow execution
    """
    from datetime import datetime

    cycle_id = f"SFDC-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"

    return {
        # Identity
        "cycle_id": cycle_id,
        "org_alias": org_alias,
        "target_org": target_org or org_alias,

        # Progress
        "current_phase": "idle",
        "phases_completed": [],
        "phase_results": [],

        # Discovery
        "metadata_components": [],
        "change_set": [],
        "dependencies": [],

        # Development
        "apex_classes": [],
        "lwc_components": [],
        "flows": [],
        "custom_objects": [],

        # Testing
        "test_results": {},
        "code_coverage": 0.0,
        "coverage_met": False,

        # Review
        "review_findings": [],
        "security_scan_passed": False,

        # Deployment
        "deployment_id": None,
        "deployment_status": None,
        "deployment_errors": [],

        # Validation
        "post_deploy_checks": {},
        "validation_passed": False,

        # Monitoring
        "monitoring_alerts": [],

        # Decision routing
        "has_breaking_changes": False,
        "should_skip_monitor": False,

        # Loop control
        "retry_count": 0,

        # Execution
        "dry_run": dry_run,
        "sandbox_only": sandbox_only,

        # Status
        "status": "pending",
        "error_message": None,
        "abort_reason": None,
        "rollback_reason": None,

        # Timestamps
        "started_at": None,
        "completed_at": None,
    }
