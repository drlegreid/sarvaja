"""
Test Audit Trail System

Provides Given/When/Then structured audit trails for test execution.
Writes evidence to evidence/ directory with datetime organization.

Per EPIC-006: Test certification with audit trails.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TestStep:
    """A single Given/When/Then step in a test."""
    phase: str  # GIVEN, WHEN, THEN
    description: str
    technical_details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestAuditRecord:
    """Complete audit record for a single test."""
    test_id: str
    test_name: str
    module: str
    category: str  # unit, integration, e2e
    business_intent: str

    # Given/When/Then steps
    given: List[TestStep] = field(default_factory=list)
    when: List[TestStep] = field(default_factory=list)
    then: List[TestStep] = field(default_factory=list)

    # Results
    status: str = "pending"  # pending, passed, failed, skipped, error
    result_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: float = 0.0

    # Timestamps
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def add_given(self, description: str, **details):
        """Add a GIVEN precondition step."""
        self.given.append(TestStep("GIVEN", description, details or None))
        return self

    def add_when(self, description: str, **details):
        """Add a WHEN action step."""
        self.when.append(TestStep("WHEN", description, details or None))
        return self

    def add_then(self, description: str, **details):
        """Add a THEN assertion step."""
        self.then.append(TestStep("THEN", description, details or None))
        return self

    def mark_passed(self, duration_ms: float = 0.0, **details):
        """Mark test as passed."""
        self.status = "passed"
        self.duration_ms = duration_ms
        self.completed_at = datetime.now().isoformat()
        self.result_details = details or None
        return self

    def mark_failed(self, error: str, duration_ms: float = 0.0, **details):
        """Mark test as failed."""
        self.status = "failed"
        self.error_message = error
        self.duration_ms = duration_ms
        self.completed_at = datetime.now().isoformat()
        self.result_details = details or None
        return self

    def mark_skipped(self, reason: str):
        """Mark test as skipped."""
        self.status = "skipped"
        self.error_message = reason
        self.completed_at = datetime.now().isoformat()
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert nested dataclasses
        data["given"] = [asdict(s) for s in self.given]
        data["when"] = [asdict(s) for s in self.when]
        data["then"] = [asdict(s) for s in self.then]
        return data


class AuditTrailWriter:
    """
    Writes test audit trails to evidence directory.

    Directory structure:
        evidence/tests/claude/YYYY-MM-DD_HHMMSS/   # Claude hooks tests
        ├── summary.json           # Overall run summary
        ├── unit/                  # Unit test results
        │   └── test_xxx.json
        ├── integration/           # Integration test results
        │   └── test_xxx.json
        └── e2e/                   # E2E test results
            └── test_xxx.json

        evidence/tests/platform/YYYY-MM-DD_HHMMSS/ # Platform agent tests (future)
    """

    def __init__(self, evidence_root: Optional[Path] = None):
        """Initialize audit trail writer."""
        if evidence_root is None:
            # Default: project_root/evidence/tests/claude (hooks tests separate from platform tests)
            self.evidence_root = Path(__file__).parent.parent.parent.parent / "evidence" / "tests" / "claude"
        else:
            self.evidence_root = Path(evidence_root)

        # Create run directory with timestamp
        self.run_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.run_dir = self.evidence_root / self.run_timestamp

        # Track all records
        self.records: List[TestAuditRecord] = []
        self.run_started = datetime.now().isoformat()

        # Summary counters
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = 0

    def create_record(
        self,
        test_id: str,
        test_name: str,
        module: str,
        category: str,
        business_intent: str
    ) -> TestAuditRecord:
        """Create a new test audit record."""
        record = TestAuditRecord(
            test_id=test_id,
            test_name=test_name,
            module=module,
            category=category,
            business_intent=business_intent
        )
        self.records.append(record)
        return record

    def write_record(self, record: TestAuditRecord) -> Path:
        """Write a single test record to its category directory."""
        # Create category directory
        category_dir = self.run_dir / record.category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Write record
        filename = f"{record.test_id.replace('::', '_').replace('/', '_')}.json"
        filepath = category_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)

        # Update counters
        if record.status == "passed":
            self.passed += 1
        elif record.status == "failed":
            self.failed += 1
        elif record.status == "skipped":
            self.skipped += 1
        elif record.status == "error":
            self.errors += 1

        return filepath

    def write_summary(self) -> Path:
        """Write run summary to summary.json."""
        self.run_dir.mkdir(parents=True, exist_ok=True)

        summary = {
            "run_id": self.run_timestamp,
            "started_at": self.run_started,
            "completed_at": datetime.now().isoformat(),
            "total_tests": len(self.records),
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "success_rate": f"{(self.passed / max(len(self.records), 1)) * 100:.1f}%",
            "tests": [
                {
                    "test_id": r.test_id,
                    "name": r.test_name,
                    "category": r.category,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "intent": r.business_intent
                }
                for r in self.records
            ]
        }

        filepath = self.run_dir / "summary.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return filepath

    def get_run_path(self) -> Path:
        """Get the path to the current run directory."""
        return self.run_dir

    def print_summary(self):
        """Print a concise summary to console."""
        total = len(self.records)
        print(f"\n{'=' * 60}")
        print(f"TEST RUN SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total: {total} | Passed: {self.passed} | Failed: {self.failed} | Skipped: {self.skipped}")
        print(f"Success Rate: {(self.passed / max(total, 1)) * 100:.1f}%")
        print(f"Audit Trail: {self.run_dir}")
        print(f"{'=' * 60}")

        if self.failed > 0:
            print("\nFailed Tests:")
            for r in self.records:
                if r.status == "failed":
                    print(f"  - {r.test_name}: {r.error_message[:80] if r.error_message else 'Unknown'}")


# Singleton instance for pytest integration
_audit_writer: Optional[AuditTrailWriter] = None


def get_audit_writer() -> AuditTrailWriter:
    """Get or create the global audit writer instance."""
    global _audit_writer
    if _audit_writer is None:
        _audit_writer = AuditTrailWriter()
    return _audit_writer


def reset_audit_writer():
    """Reset the global audit writer (for new test runs)."""
    global _audit_writer
    _audit_writer = None
