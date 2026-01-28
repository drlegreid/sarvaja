"""
BDD Evidence Collector - Structured Test Evidence with Given/When/Then.

Per GAP-TEST-EVIDENCE-001: File-based test evidence with BDD structure.
Per RD-TESTING-STRATEGY TEST-002: Full trace collection.

Created: 2026-01-21
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class StepType(str, Enum):
    """BDD step types."""
    GIVEN = "given"
    WHEN = "when"
    THEN = "then"
    AND = "and"
    BUT = "but"


@dataclass
class BDDStep:
    """A single BDD step in a test scenario."""
    step_type: StepType
    description: str
    data: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
    passed: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        result = {
            "type": self.step_type.value,
            "description": self.description,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
        }
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class EvidenceRecord:
    """Complete evidence for a single test. Renamed to avoid pytest collection."""
    test_id: str
    name: str
    category: str  # unit, integration, e2e
    status: str  # passed, failed, skipped
    duration_ms: float
    intent: str  # High-level test purpose
    steps: List[BDDStep] = field(default_factory=list)
    linked_rules: List[str] = field(default_factory=list)
    linked_gaps: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence to dictionary for JSON serialization."""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "intent": self.intent,
            "bdd_steps": [step.to_dict() for step in self.steps],
            "linked_rules": self.linked_rules,
            "linked_gaps": self.linked_gaps,
            "session_id": self.session_id,
            "error_message": self.error_message,
            "traceback": self.traceback[:2000] if self.traceback else None,
        }


class BDDEvidenceCollector:
    """
    Collects BDD-structured test evidence.

    Usage:
        collector = BDDEvidenceCollector(base_dir="evidence/tests")
        collector.start_run()

        # For each test:
        collector.start_test("test_user_login", "unit", "User login validates credentials")
        collector.given("a registered user exists", {"email": "test@example.com"})
        collector.when("the user submits valid credentials")
        collector.then("the user is logged in")
        collector.end_test("passed", duration_ms=150.0)

        collector.end_run()  # Writes summary.json
    """

    def __init__(
        self,
        base_dir: str = "evidence/tests",
        session_id: Optional[str] = None
    ):
        """Initialize collector.

        Args:
            base_dir: Base directory for evidence files
            session_id: Optional governance session ID for linking
        """
        self.base_dir = Path(base_dir)
        self.session_id = session_id
        self.run_id: Optional[str] = None
        self.run_dir: Optional[Path] = None
        self.current_test: Optional[EvidenceRecord] = None
        self.tests: List[EvidenceRecord] = []
        self.start_time: Optional[datetime] = None

    def start_run(self, run_id: Optional[str] = None) -> str:
        """Start a new test run.

        Args:
            run_id: Optional run identifier (auto-generated if not provided)

        Returns:
            Run ID
        """
        self.run_id = run_id or datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.run_dir = self.base_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.tests = []
        self.start_time = datetime.now()

        # Create subdirectories for test levels
        for level in ["unit", "integration", "e2e"]:
            (self.run_dir / level).mkdir(exist_ok=True)

        return self.run_id

    def start_test(
        self,
        test_id: str,
        category: str,
        intent: str,
        rules: Optional[List[str]] = None,
        gaps: Optional[List[str]] = None
    ) -> None:
        """Start recording evidence for a test.

        Args:
            test_id: Unique test identifier (e.g., pytest nodeid)
            category: Test category (unit, integration, e2e)
            intent: High-level purpose of the test
            rules: List of rule IDs this test validates
            gaps: List of gap IDs this test addresses
        """
        name = test_id.split("::")[-1] if "::" in test_id else test_id
        self.current_test = EvidenceRecord(
            test_id=test_id,
            name=name,
            category=category,
            status="running",
            duration_ms=0.0,
            intent=intent,
            linked_rules=rules or [],
            linked_gaps=gaps or [],
            session_id=self.session_id,
        )

    def given(
        self,
        description: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a GIVEN step (precondition)."""
        self._add_step(StepType.GIVEN, description, data)

    def when(
        self,
        description: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a WHEN step (action)."""
        self._add_step(StepType.WHEN, description, data)

    def then(
        self,
        description: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a THEN step (assertion)."""
        self._add_step(StepType.THEN, description, data)

    def and_step(
        self,
        description: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an AND step (continuation)."""
        self._add_step(StepType.AND, description, data)

    def but_step(
        self,
        description: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a BUT step (exception to previous)."""
        self._add_step(StepType.BUT, description, data)

    def _add_step(
        self,
        step_type: StepType,
        description: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a step to the current test."""
        if not self.current_test:
            return
        step = BDDStep(step_type=step_type, description=description, data=data)
        self.current_test.steps.append(step)

    def mark_step_failed(self, error: str) -> None:
        """Mark the last step as failed."""
        if self.current_test and self.current_test.steps:
            self.current_test.steps[-1].passed = False
            self.current_test.steps[-1].error = error

    def end_test(
        self,
        status: str,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
        traceback: Optional[str] = None
    ) -> Optional[EvidenceRecord]:
        """End the current test and save evidence.

        Args:
            status: Test outcome (passed, failed, skipped)
            duration_ms: Test duration in milliseconds
            error: Error message if failed
            traceback: Stack trace if failed

        Returns:
            The completed EvidenceRecord or None
        """
        if not self.current_test or not self.run_dir:
            return None

        self.current_test.status = status
        self.current_test.duration_ms = duration_ms
        self.current_test.error_message = error
        self.current_test.traceback = traceback

        # Save individual test evidence
        self._save_test_evidence(self.current_test)
        self.tests.append(self.current_test)

        evidence = self.current_test
        self.current_test = None
        return evidence

    def _save_test_evidence(self, evidence: EvidenceRecord) -> Path:
        """Save individual test evidence to file."""
        if not self.run_dir:
            raise RuntimeError("No active run - call start_run() first")

        # Determine target directory
        category_dir = self.run_dir / evidence.category
        category_dir.mkdir(exist_ok=True)

        # Generate safe filename from test_id
        safe_name = evidence.test_id.replace("::", "_").replace("/", "_")
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        filepath = category_dir / f"{safe_name}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(evidence.to_dict(), f, indent=2)

        return filepath

    def end_run(self) -> Dict[str, Any]:
        """End the test run and generate summary.

        Returns:
            Summary dictionary with run statistics
        """
        if not self.run_dir or not self.start_time:
            return {}

        # Calculate statistics
        passed = sum(1 for t in self.tests if t.status == "passed")
        failed = sum(1 for t in self.tests if t.status == "failed")
        skipped = sum(1 for t in self.tests if t.status == "skipped")
        total = len(self.tests)
        success_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0%"

        # Collect all linked rules/gaps
        all_rules = set()
        all_gaps = set()
        for test in self.tests:
            all_rules.update(test.linked_rules)
            all_gaps.update(test.linked_gaps)

        summary = {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "started_at": self.start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": success_rate,
            "linked_rules": sorted(all_rules),
            "linked_gaps": sorted(all_gaps),
            "tests": [t.to_dict() for t in self.tests],
        }

        # Save summary
        summary_path = self.run_dir / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def get_run_dir(self) -> Optional[Path]:
        """Get the current run directory."""
        return self.run_dir
