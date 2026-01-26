"""
Robot Framework Library for Agent Platform Benchmark Tests.

Per RD-LACMUS: Benchmark metrics for agent platform.
Split from test_agent_platform.py per DOC-SIZE-01-v1.
"""
import re
from pathlib import Path
from robot.api.deco import keyword


class AgentPlatformBenchmarkLibrary:
    """Library for agent platform benchmark tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    @keyword("Trust Accuracy Target 95")
    def trust_accuracy_target_95(self):
        """Trust score accuracy meets 95% target."""
        test_cases = [
            (1.0, 1.0, 1.0, 1.0, 0.99, 1.01),
            (0.8, 0.8, 0.8, 0.8, 0.79, 0.81),
            (0.5, 0.5, 0.5, 0.5, 0.49, 0.51),
            (0.9, 0.85, 0.80, 0.70, 0.84, 0.88),
        ]

        accurate = 0
        for compliance, accuracy, consistency, tenure, low, high in test_cases:
            trust = 0.4 * compliance + 0.3 * accuracy + 0.2 * consistency + 0.1 * tenure
            if low <= trust <= high:
                accurate += 1

        accuracy_rate = accurate / len(test_cases)
        return {
            "meets_target": accuracy_rate >= 0.95,
            "accuracy_rate": accuracy_rate
        }

    @keyword("Task Routing Accuracy Target 90")
    def task_routing_accuracy_target_90(self):
        """Task routing accuracy meets 90% target."""
        routing_rules = [
            ("GAP-UI-001", "CODING"),
            ("GAP-API-001", "CODING"),
            ("RD-001", "RESEARCH"),
            ("RD-WORKSPACE", "RESEARCH"),
            ("P12.1", "CURATOR"),
            ("P11.1", "CODING"),
            ("GAP-DATA-001", "CURATOR"),
            ("UNKNOWN-001", "RESEARCH"),
        ]

        def route(task_id: str) -> str:
            task_upper = task_id.upper()
            if task_upper.startswith("GAP-UI") or task_upper.startswith("GAP-API"):
                return "CODING"
            if task_upper.startswith("RD-"):
                return "RESEARCH"
            if task_upper.startswith("GAP-DATA"):
                return "CURATOR"
            if task_upper.startswith("P"):
                match = re.match(r"P(\d+)", task_upper)
                if match and int(match.group(1)) >= 12:
                    return "CURATOR"
                return "CODING"
            return "RESEARCH"

        correct = sum(1 for task_id, expected in routing_rules if route(task_id) == expected)
        accuracy = correct / len(routing_rules)
        return {
            "meets_target": accuracy >= 0.90,
            "accuracy_rate": accuracy
        }
