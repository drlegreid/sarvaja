"""
Executive View Subpackage.

Per RULE-032: File size limit - modularized executive view components.
Per GAP-UI-046: Reports are per-session with evidence summary.

Module structure:
- header.py: Header with session selector (~50 lines)
- metrics.py: Metrics summary cards (~50 lines)
- sections.py: Report sections (~55 lines)
- status.py: Status banner and evidence section (~130 lines)
- content.py: Main content area (~55 lines)
"""

from .header import build_session_selector, build_executive_header
from .metrics import build_metrics_summary
from .sections import build_report_sections
from .status import build_status_banner, build_session_evidence_section
from .content import build_executive_content

__all__ = [
    "build_session_selector",
    "build_executive_header",
    "build_metrics_summary",
    "build_report_sections",
    "build_status_banner",
    "build_session_evidence_section",
    "build_executive_content",
]
