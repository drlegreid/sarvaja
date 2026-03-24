"""Report models. Per RULE-029."""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class ExecutiveReportSection(BaseModel):
    """Single section of executive report."""
    title: str
    content: str
    metrics: Optional[Dict[str, Any]] = None
    status: Optional[str] = None  # success, warning, error, info

class ExecutiveSummarySession(BaseModel):
    """Session summary for executive report."""
    session_id: str
    date: str
    tasks_completed: int
    decisions_made: int
    rules_applied: List[str]
    key_outcomes: List[str]

class ExecutiveReportResponse(BaseModel):
    """Executive report per RULE-029. 7 sections: Highlights, Compliance, Risk, Alignment, Resources, Recommendations, Objectives."""
    report_id: str
    generated_at: str
    session_id: Optional[str] = None
    period: str  # e.g., "2024-12-27", "2024-12-25 to 2024-12-27"
    sections: List[ExecutiveReportSection]
    overall_status: str  # healthy, warning, critical
    metrics_summary: Dict[str, Any]
