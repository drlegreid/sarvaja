"""
Robot Framework Library for SessionCollector - Log Generation Tests.

Per P4.2: Session Collector.
Split from SessionCollectorLibrary.py per DOC-SIZE-01-v1.

Covers: Session log generation, markdown output, sections.
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class SessionCollectorLogLibrary:
    """Library for testing SessionCollector log generation."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Session Log Generation Tests
    # =========================================================================

    @keyword("Generate Session Log Creates File")
    def generate_session_log_creates_file(self):
        """generate_session_log creates markdown file."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_prompt("Test prompt")
                log_path = collector.generate_session_log(Path(tmpdir))

                return {
                    "file_exists": Path(log_path).exists(),
                    "is_markdown": log_path.endswith(".md")
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Header")
    def generate_session_log_contains_header(self):
        """Generated log contains session header."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("MY-TOPIC", evidence_dir=tmpdir)
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path) as f:
                    content = f.read()

                return {
                    "has_topic": "MY-TOPIC" in content,
                    "has_session_id": "Session ID:" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Decisions")
    def generate_session_log_contains_decisions(self):
        """Generated log contains decisions section."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_decision(
                    decision_id="DECISION-001",
                    name="Test Decision",
                    context="Testing",
                    rationale="For testing"
                )
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_decisions_section": "## Decisions" in content,
                    "has_decision_id": "DECISION-001" in content,
                    "has_decision_name": "Test Decision" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Thoughts")
    def generate_session_log_contains_thoughts(self):
        """Generated log contains Key Thoughts section."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_thought(
                    thought="This is a key reasoning step",
                    thought_type="hypothesis",
                    confidence=0.85
                )
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_thoughts_section": "## Key Thoughts" in content,
                    "has_hypothesis": "Hypothesis" in content,
                    "has_reasoning": "key reasoning step" in content,
                    "has_confidence": "Confidence: 85" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Tool Calls")
    def generate_session_log_contains_tool_calls(self):
        """Generated log contains Tool Calls section."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_tool_call(
                    tool_name="governance_get_rule",
                    arguments={"rule_id": "RULE-001"},
                    result="Rule returned successfully",
                    duration_ms=150,
                    success=True
                )
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_tool_calls_section": "## Tool Calls" in content,
                    "has_tool_name": "governance_get_rule" in content,
                    "has_duration": "150ms" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Session Log Contains Initial Prompt")
    def generate_session_log_contains_initial_prompt(self):
        """Generated log contains initial prompt per SESSION-PROMPT-01-v1."""
        try:
            from governance.session_collector import SessionCollector

            with tempfile.TemporaryDirectory() as tmpdir:
                collector = SessionCollector("TEST", evidence_dir=tmpdir)
                collector.capture_intent(
                    goal="Fix the bug",
                    source="User request",
                    initial_prompt="Please fix the login bug that crashes on mobile"
                )
                log_path = collector.generate_session_log(Path(tmpdir))

                with open(log_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_intent_section": "## Session Intent" in content,
                    "has_initial_prompt": "### Initial Prompt" in content,
                    "has_prompt_content": "login bug that crashes on mobile" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
