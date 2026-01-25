"""
RF-004: Robot Framework Library for Trace Minimizer.

Wraps tests/evidence/trace_minimizer.py for Robot Framework tests.
Per RD-TESTING-STRATEGY TEST-003: Debug workflow trace minimization.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Sample tracebacks for testing
SAMPLE_ASSERTION_ERROR = """
def test_rule_creation():
>       assert rule.status == 'ACTIVE'
E       AssertionError: assert 'INACTIVE' == 'ACTIVE'
E         + where 'INACTIVE' = <Rule RULE-001>.status

tests/test_rules.py:42: AssertionError
"""

SAMPLE_ATTRIBUTE_ERROR = """
Traceback (most recent call last):
  File "tests/test_agents.py", line 25, in test_agent_trust
    score = agent.get_trust_score()
  File "/home/user/project/governance/agents.py", line 100, in get_trust_score
    return self.trust_manager.calculate()
AttributeError: 'NoneType' object has no attribute 'calculate'
"""

SAMPLE_LONG_TRACEBACK = """
Traceback (most recent call last):
  File "/home/user/.venv/lib/python3.13/site-packages/_pytest/runner.py", line 341, in from_call
    result = func()
  File "/home/user/.venv/lib/python3.13/site-packages/_pytest/runner.py", line 262, in <lambda>
    lambda: ihook(item=item, **kwds), when=when, reraise=reraise
  File "/home/user/.venv/lib/python3.13/site-packages/pluggy/_hooks.py", line 513, in __call__
    return self._hookexec(self.name, self._hookimpls, kwargs, firstresult)
  File "/home/user/project/tests/test_rules.py", line 42, in test_rule_creation
    assert rule.status == 'ACTIVE'
  File "/home/user/project/governance/models.py", line 50, in status
    return self._get_status()
AssertionError: Expected ACTIVE but got INACTIVE
"""


class TraceMinimzerLibrary:
    """Robot Framework library for Trace Minimizer functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._minimizer = None

    def create_trace_minimizer(self) -> bool:
        """Create a TraceMinimizer instance."""
        from tests.evidence.trace_minimizer import TraceMinimizer
        self._minimizer = TraceMinimizer()
        return self._minimizer is not None

    def get_sample_assertion_error(self) -> str:
        """Get sample assertion error traceback."""
        return SAMPLE_ASSERTION_ERROR

    def get_sample_attribute_error(self) -> str:
        """Get sample attribute error traceback."""
        return SAMPLE_ATTRIBUTE_ERROR

    def get_sample_long_traceback(self) -> str:
        """Get sample long traceback."""
        return SAMPLE_LONG_TRACEBACK

    def classify_error(self, traceback: str) -> Dict[str, str]:
        """Classify an error from traceback.

        Returns dict with error_type and category (both strings).
        """
        error_type, category = self._minimizer.classify_error(traceback)
        # category is already a string from ErrorCategory constants
        return {"error_type": error_type, "category": category}

    def extract_error_message(self, traceback: str) -> str:
        """Extract error message from traceback."""
        return self._minimizer.extract_message(traceback)

    def parse_and_filter_frames(self, traceback: str) -> Dict[str, Any]:
        """Parse traceback and filter frames.

        First parses traceback to frames, then filters them.
        """
        frames = self._minimizer.parse_traceback(traceback)
        filtered = self._minimizer.filter_frames(frames)
        return {
            "count": len(filtered),
            "frames": [
                {"file": f.file, "line": f.line, "function": f.function, "is_user_code": f.is_user_code}
                for f in filtered
            ]
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return self._minimizer.estimate_tokens(text)

    def minimize_traceback(self, traceback: str, test_id: str = "test") -> Dict[str, Any]:
        """Minimize a traceback for LLM consumption.

        Returns dict with error info and compression stats.
        """
        result = self._minimizer.minimize_traceback(traceback, test_id=test_id)
        return {
            "error_type": result.error_type,
            "category": result.error_category,
            "message": result.error_message,
            "frame_count": len(result.stack_frames),
            "original_tokens": result.original_tokens,
            "minimized_tokens": result.minimized_tokens,
            "source_file": result.source_file,
            "source_line": result.source_line,
        }

    def minimize_for_llm(self, traceback: str, test_id: str = None) -> str:
        """Minimize trace for LLM with optional test ID."""
        from tests.evidence.trace_minimizer import minimize_for_llm
        return minimize_for_llm(traceback, test_id=test_id)

    def estimate_compression(self, original: str, minimized: str) -> Dict[str, Any]:
        """Estimate compression ratio between original and minimized text."""
        from tests.evidence.trace_minimizer import estimate_compression
        return estimate_compression(original, minimized)

    def frames_exclude_pytest_internals(self, traceback: str) -> bool:
        """Check if filtered frames exclude pytest internals."""
        frames = self._minimizer.parse_traceback(traceback)
        filtered = self._minimizer.filter_frames(frames)
        for f in filtered:
            if "_pytest" in f.file or "pluggy" in f.file:
                return False
        return True

    def frames_include_project_code(self, traceback: str) -> bool:
        """Check if filtered frames include project code."""
        frames = self._minimizer.parse_traceback(traceback)
        filtered = self._minimizer.filter_frames(frames)
        for f in filtered:
            if "tests/" in f.file or "governance/" in f.file:
                return True
        return False
