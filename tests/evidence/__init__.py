"""
Test Evidence Module - BDD-Enhanced Evidence Collection.

Per GAP-TEST-EVIDENCE-001: File-based test evidence with BDD structure.
Per RD-TESTING-STRATEGY TEST-002: Evidence collection at trace level.

This module provides:
- BDDEvidenceCollector: Captures Given/When/Then structured evidence
- RuleLinker: Links tests to governance rules/gaps
- TraceCapture: HTTP/MCP trace collection with correlation IDs
- Evidence file generation in evidence/tests/ directory

Created: 2026-01-21
"""

from tests.evidence.collector import (
    BDDEvidenceCollector,
    BDDStep,
    StepType,
    EvidenceRecord,
)
from tests.evidence.rule_linker import RuleLinker
from tests.evidence.trace_capture import (
    TraceCapture,
    TraceRecord,
    RequestsTraceAdapter,
    link_traces_to_evidence,
)
from tests.evidence.trace_minimizer import (
    TraceMinimizer,
    MinimizedTrace,
    MinimizedFrame,
    ErrorCategory,
    minimize_for_llm,
    estimate_compression,
)
from tests.evidence.certification_report import (
    CertificationReportGenerator,
    CertificationReport,
    TestResult,
    generate_certification,
)

__all__ = [
    "BDDEvidenceCollector",
    "BDDStep",
    "StepType",
    "EvidenceRecord",
    "RuleLinker",
    "TraceCapture",
    "TraceRecord",
    "RequestsTraceAdapter",
    "link_traces_to_evidence",
    "TraceMinimizer",
    "MinimizedTrace",
    "MinimizedFrame",
    "ErrorCategory",
    "minimize_for_llm",
    "estimate_compression",
    "CertificationReportGenerator",
    "CertificationReport",
    "TestResult",
    "generate_certification",
]
