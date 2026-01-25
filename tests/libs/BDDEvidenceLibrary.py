"""
RF-004: Robot Framework Library for BDD Evidence Collector.

Wraps tests/evidence/collector.py for Robot Framework tests.
Per GAP-TEST-EVIDENCE-001: File-based test evidence with BDD structure.
"""

import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class BDDEvidenceLibrary:
    """Robot Framework library for BDD Evidence Collector functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._tmpdir = None
        self._collector = None
        self._linker = None

    def create_temp_directory(self) -> str:
        """Create a temporary directory for testing."""
        self._tmpdir = tempfile.mkdtemp()
        return self._tmpdir

    def cleanup_temp_directory(self):
        """Clean up temporary directory."""
        import shutil
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None

    # BDDStep tests
    def create_bdd_step(
        self,
        step_type: str,
        description: str,
        passed: bool = True,
        data: Dict = None,
        duration_ms: float = None,
        error: str = None
    ) -> Dict[str, Any]:
        """Create a BDDStep and return as dict."""
        from tests.evidence.collector import BDDStep, StepType

        type_map = {
            "given": StepType.GIVEN,
            "when": StepType.WHEN,
            "then": StepType.THEN,
            "and": StepType.AND,
        }

        kwargs = {
            "step_type": type_map[step_type.lower()],
            "description": description,
            "passed": passed
        }
        if data:
            kwargs["data"] = data
        if duration_ms is not None:
            kwargs["duration_ms"] = float(duration_ms)
        if error:
            kwargs["error"] = error

        step = BDDStep(**kwargs)
        return step.to_dict()

    # EvidenceRecord tests
    def create_evidence_record(
        self,
        test_id: str,
        name: str,
        category: str,
        status: str,
        duration_ms: float = 0.0,
        intent: str = None,
        linked_rules: List[str] = None,
        linked_gaps: List[str] = None
    ) -> Dict[str, Any]:
        """Create an EvidenceRecord and return as dict."""
        from tests.evidence.collector import EvidenceRecord

        kwargs = {
            "test_id": test_id,
            "name": name,
            "category": category,
            "status": status,
            "duration_ms": float(duration_ms),
        }
        if intent:
            kwargs["intent"] = intent
        if linked_rules:
            kwargs["linked_rules"] = linked_rules
        if linked_gaps:
            kwargs["linked_gaps"] = linked_gaps

        evidence = EvidenceRecord(**kwargs)
        return evidence.to_dict()

    # BDDEvidenceCollector tests
    def create_collector(self, base_dir: str = None, session_id: str = None) -> bool:
        """Create a BDDEvidenceCollector instance."""
        from tests.evidence.collector import BDDEvidenceCollector

        kwargs = {}
        if base_dir:
            kwargs["base_dir"] = base_dir
        elif self._tmpdir:
            kwargs["base_dir"] = self._tmpdir
        if session_id:
            kwargs["session_id"] = session_id

        self._collector = BDDEvidenceCollector(**kwargs)
        return self._collector is not None

    def get_collector_session_id(self) -> Optional[str]:
        """Get collector's session ID."""
        return self._collector.session_id if self._collector else None

    def start_run(self, run_id: str = None) -> str:
        """Start a test run."""
        return self._collector.start_run(run_id)

    def run_directory_exists(self) -> bool:
        """Check if run directory was created."""
        return self._collector.run_dir is not None and self._collector.run_dir.exists()

    def start_test(self, test_id: str, category: str, intent: str, rules: List[str] = None, gaps: List[str] = None):
        """Start recording a test."""
        kwargs = {"rules": rules or [], "gaps": gaps or []}
        self._collector.start_test(test_id, category, intent, **kwargs)

    def record_given(self, description: str, data: Dict = None):
        """Record a GIVEN step."""
        self._collector.given(description, data)

    def record_when(self, description: str, data: Dict = None):
        """Record a WHEN step."""
        self._collector.when(description, data)

    def record_then(self, description: str, data: Dict = None):
        """Record a THEN step."""
        self._collector.then(description, data)

    def end_test(self, status: str, duration_ms: float = None, error: str = None) -> Dict[str, Any]:
        """End test and return evidence as dict."""
        kwargs = {}
        if duration_ms is not None:
            kwargs["duration_ms"] = float(duration_ms)
        if error:
            kwargs["error"] = error

        evidence = self._collector.end_test(status, **kwargs)
        return evidence.to_dict() if evidence else {}

    def end_run(self) -> Dict[str, Any]:
        """End run and return summary."""
        return self._collector.end_run()

    def get_evidence_file_count(self, category: str) -> int:
        """Get count of evidence files in category directory."""
        if not self._collector or not self._collector.run_dir:
            return 0
        category_dir = self._collector.run_dir / category
        if not category_dir.exists():
            return 0
        return len(list(category_dir.glob("*.json")))

    # RuleLinker tests
    def create_rule_linker(self) -> bool:
        """Create a RuleLinker instance."""
        from tests.evidence.rule_linker import RuleLinker
        self._linker = RuleLinker()
        return self._linker is not None

    def extract_references(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract rule and gap references from text."""
        rules, gaps = self._linker.extract_references(text)
        return list(rules), list(gaps)

    def register_test(
        self,
        test_id: str,
        docstring: str = None,
        rules: List[str] = None,
        gaps: List[str] = None
    ) -> Tuple[List[str], List[str]]:
        """Register a test with the linker."""
        kwargs = {}
        if docstring:
            kwargs["docstring"] = docstring
        if rules:
            kwargs["rules"] = rules
        if gaps:
            kwargs["gaps"] = gaps

        rules_out, gaps_out = self._linker.register_test(test_id, **kwargs)
        return list(rules_out), list(gaps_out)

    def get_tests_for_rule(self, rule_id: str) -> List[str]:
        """Get tests that validate a rule."""
        return list(self._linker.get_tests_for_rule(rule_id))

    def get_coverage_summary(self) -> Dict[str, Any]:
        """Get coverage summary from linker."""
        return self._linker.get_coverage_summary()
