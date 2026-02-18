"""
Reports Routes.

Per SESSION-DSM-01-v1: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per REPORT-EXEC-01-v1: Executive Reporting Pattern.

Created: 2024-12-28
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import logging

from governance.models import ExecutiveReportSection, ExecutiveReportResponse
from governance.stores import (
    get_typedb_client,
    _tasks_store, _sessions_store, _agents_store
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Reports"])


# =============================================================================
# REPORT GENERATION HELPERS
# =============================================================================

def _generate_recommendations(pending_tasks: int, avg_trust: float, active_rules: int) -> str:
    """Generate recommendations based on current state."""
    recs = []

    if pending_tasks > 10:
        recs.append("Consider prioritizing backlog reduction - high pending task count")
    if avg_trust < 0.7:
        recs.append("Monitor agent trust scores - below optimal threshold")
    if active_rules < 20:
        recs.append("Review governance rules - some may need activation")

    if not recs:
        recs.append("System operating within normal parameters")
        recs.append("Continue regular DSP cycles per SESSION-DSM-01-v1")

    return ". ".join(recs) + "."


def _generate_objectives(pending_tasks: int, completed_tasks: int) -> str:
    """Generate next session objectives."""
    objs = []

    if pending_tasks > 0:
        objs.append(f"Complete top {min(pending_tasks, 3)} priority tasks from backlog")
    objs.append("Run DSP cycle for system health validation")
    objs.append("Update session evidence per SESSION-EVID-01-v1")

    if completed_tasks > 5:
        objs.append("Archive completed tasks to TASKS-COMPLETED.md")

    return ". ".join(objs) + "."


def _generate_executive_report(
    session_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> ExecutiveReportResponse:
    """
    Generate executive report per REPORT-EXEC-01-v1 template.

    Aggregates data from sessions, rules, tasks, and agents.
    """
    report_id = f"EXEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    now = datetime.now()
    client = get_typedb_client()

    # Determine period
    if session_id:
        period = session_id
    elif start_date and end_date:
        period = f"{start_date} to {end_date}"
    else:
        period = now.strftime("%Y-%m-%d")

    # Gather metrics
    total_tasks = len(_tasks_store)
    completed_tasks = sum(1 for t in _tasks_store.values() if t.get("status") in ["DONE", "completed"])
    pending_tasks = sum(1 for t in _tasks_store.values() if t.get("status") in ["TODO", "pending"])

    total_sessions = len(_sessions_store)
    active_sessions = sum(1 for s in _sessions_store.values() if s.get("status") == "ACTIVE")

    total_agents = len(_agents_store)
    active_agents = sum(1 for a in _agents_store.values() if a.get("status") == "ACTIVE")
    avg_trust = sum(a.get("trust_score", 0.8) for a in _agents_store.values()) / max(total_agents, 1)

    # Try to get rules count from TypeDB
    rules_count = 0
    active_rules = 0
    if client:
        try:
            rules = client.get_all_rules()
            if rules:
                rules_count = len(rules)
                active_rules = sum(1 for r in rules if r.status == "ACTIVE")
        except Exception as e:
            logger.debug(f"Failed to query rules for report: {e}")

    # Calculate overall status
    if avg_trust >= 0.8 and completed_tasks > pending_tasks:
        overall_status = "healthy"
    elif avg_trust >= 0.6 or completed_tasks >= pending_tasks:
        overall_status = "warning"
    else:
        overall_status = "critical"

    # Build sections per RULE-029 template
    sections = [
        # 1. Executive Summary (Highlights)
        ExecutiveReportSection(
            title="Executive Summary",
            content=f"Session period: {period}. {completed_tasks} tasks completed, {pending_tasks} pending. "
                    f"{active_agents} agents active with average trust score of {avg_trust:.2f}.",
            metrics={
                "tasks_completed": completed_tasks,
                "tasks_pending": pending_tasks,
                "agents_active": active_agents,
                "avg_trust_score": round(avg_trust, 2),
            },
            status=overall_status
        ),
        # 2. Compliance Status
        ExecutiveReportSection(
            title="Compliance Status",
            content=f"{active_rules} of {rules_count} governance rules are ACTIVE. "
                    f"All agents operating within trust thresholds per GOV-BICAM-01-v1.",
            metrics={
                "active_rules": active_rules,
                "total_rules": rules_count,
                "compliance_rate": round(active_rules / max(rules_count, 1) * 100, 1),
            },
            status="success" if active_rules > 0 else "warning"
        ),
        # 3. Risk Assessment
        ExecutiveReportSection(
            title="Risk Assessment",
            content="No critical risks identified. " if overall_status != "critical" else
                    "Elevated risk: Trust scores below threshold or high pending task count.",
            metrics={
                "risk_level": overall_status.upper(),
                "pending_critical_tasks": sum(1 for t in _tasks_store.values()
                                              if t.get("status") in ["TODO", "pending"]),
            },
            status=overall_status
        ),
        # 4. Strategic Alignment
        ExecutiveReportSection(
            title="Strategic Alignment",
            content=f"TypeDB-First strategy (DECISION-003) in effect. "
                    f"{total_sessions} sessions documented with evidence trails per SESSION-EVID-01-v1.",
            metrics={
                "sessions_documented": total_sessions,
                "active_sessions": active_sessions,
                "typedb_connected": client is not None and client.is_connected() if client else False,
            },
            status="success"
        ),
        # 5. Resource Utilization
        ExecutiveReportSection(
            title="Resource Utilization",
            content=f"{total_agents} agents registered, {active_agents} currently active. "
                    f"Total tasks executed: {sum(a.get('tasks_executed', 0) for a in _agents_store.values())}.",
            metrics={
                "total_agents": total_agents,
                "active_agents": active_agents,
                "total_tasks_executed": sum(a.get("tasks_executed", 0) for a in _agents_store.values()),
            },
            status="success" if active_agents > 0 else "warning"
        ),
        # 6. Recommendations
        ExecutiveReportSection(
            title="Recommendations",
            content=_generate_recommendations(pending_tasks, avg_trust, active_rules),
            metrics=None,
            status="info" if pending_tasks < 10 else "warning"
        ),
        # 7. Next Session Objectives
        ExecutiveReportSection(
            title="Next Session Objectives",
            content=_generate_objectives(pending_tasks, completed_tasks),
            metrics={
                "priority_tasks": min(pending_tasks, 5),
            },
            status="info"
        ),
    ]

    # Calculate compliance rate for metrics_summary
    compliance_rate = round(active_rules / max(rules_count, 1) * 100, 1)

    return ExecutiveReportResponse(
        report_id=report_id,
        generated_at=now.isoformat(),
        session_id=session_id,
        period=period,
        sections=sections,
        overall_status=overall_status,
        metrics_summary={
            "tasks_total": total_tasks,
            "tasks_completed": completed_tasks,
            "tasks_pending": pending_tasks,
            "sessions_total": total_sessions,
            # GAP-UI-029 fix: Use field names expected by executive_view.py
            "total_agents": total_agents,
            "total_rules": rules_count,
            "active_rules": active_rules,
            "compliance_rate": compliance_rate,
            "avg_trust_score": round(avg_trust, 2),
        }
    )


# =============================================================================
# REPORTS ENDPOINTS
# =============================================================================

@router.get("/reports/executive", response_model=ExecutiveReportResponse)
async def get_executive_report(
    session_id: Optional[str] = Query(None, description="Specific session to report on"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Generate executive report per REPORT-EXEC-01-v1.

    Per GAP-UI-044: Executive Reporting UI.

    Parameters:
    - session_id: Optional specific session to report on
    - start_date: Optional start date for period
    - end_date: Optional end date for period

    Returns 7-section executive report with metrics.
    """
    return _generate_executive_report(session_id, start_date, end_date)


@router.get("/reports/executive/sessions/{session_id}", response_model=ExecutiveReportResponse)
async def get_session_executive_report(session_id: str):
    """
    Generate executive report for a specific session.

    Per GAP-UI-044: Executive Reporting UI.
    """
    if session_id not in _sessions_store:
        client = get_typedb_client()
        if client:
            try:
                session = client.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            except Exception as e:
                # BUG-475-RPT-1: Sanitize HTTPException detail — prevent exception detail leakage to API clients
                logger.warning(f"Session lookup failed for {session_id}: {type(e).__name__}", exc_info=True)
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        else:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return _generate_executive_report(session_id=session_id)
