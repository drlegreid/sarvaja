"""
Workflow Compliance Service - Backward Compatibility Wrapper.

Per DOC-SIZE-01-v1: Refactored from 653 lines to package structure.
Per UI-AUDIT-009: Workflow compliance validation system.

This file maintains backward compatibility for imports.
All functionality moved to governance/workflow_compliance/ package.

Original: 653 lines (2026-01-20)
Refactored: Package structure (2026-01-20)
"""

# Re-export everything from the package for backward compatibility
from governance.workflow_compliance import (
    ComplianceCheck,
    ComplianceReport,
    run_compliance_checks,
    format_compliance_for_ui,
)

__all__ = [
    "ComplianceCheck",
    "ComplianceReport",
    "run_compliance_checks",
    "format_compliance_for_ui",
]
