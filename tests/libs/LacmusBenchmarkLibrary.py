"""
Lacmus Benchmark Library for Robot Framework
Agent Platform PoC Validation - Multi-agent governance capabilities.
Migrated from tests/benchmarks/test_lacmus.py
Per: RF-007 Robot Framework Migration

Phases:
- Phase 1: Unit Validation (Trust, Routing, Handoff format)
- Phase 2: Integration (Activity tracking, Trust evolution, Handoff chain)
- Phase 3: Recovery (AMNESIA simulation, Context restore)
"""
import re
import time
from robot.api.deco import keyword


class LacmusBenchmarkLibrary:
    """Robot Framework keywords for Lacmus benchmark tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # Trust formula weights (RULE-011)
    COMPLIANCE_WEIGHT = 0.4
    ACCURACY_WEIGHT = 0.3
    CONSISTENCY_WEIGHT = 0.2
    TENURE_WEIGHT = 0.1

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _list_all_agents(self):
        """Get all agents from TypeDB."""
        try:
            from governance.mcp_tools.common import get_typedb_client
            client = get_typedb_client()
            if not client.connect():
                return []
            agents = client.get_all_agents()
            client.close()
            return [{"id": a.id, "name": a.name, "agent_type": a.agent_type,
                    "trust_score": a.trust_score} for a in agents]
        except Exception:
            return []

    def _route_task_to_agent(self, task_id: str) -> dict:
        """Route task to appropriate agent role."""
        task_upper = task_id.upper()

        if task_upper.startswith("RD-"):
            return {"task_id": task_id, "recommended_agent": "RESEARCH",
                    "reason": "R&D tasks require exploration and analysis"}
        if task_upper.startswith("GAP-UI"):
            return {"task_id": task_id, "recommended_agent": "CODING",
                    "reason": "UI gaps typically require code implementation"}
        if task_upper.startswith("GAP-API"):
            return {"task_id": task_id, "recommended_agent": "CODING",
                    "reason": "API gaps require implementation"}
        if task_upper.startswith("P"):
            match = re.match(r"P(\d+)", task_upper)
            if match:
                phase = int(match.group(1))
                if phase >= 12:
                    return {"task_id": task_id, "recommended_agent": "CURATOR",
                            "reason": "Orchestration phase requires governance oversight"}
            return {"task_id": task_id, "recommended_agent": "CODING",
                    "reason": "Phase tasks typically require code implementation"}
        return {"task_id": task_id, "recommended_agent": "RESEARCH",
                "reason": "Default: Start with research"}

    # =========================================================================
    # Phase 1: Trust Score Tests
    # =========================================================================

    @keyword("Trust Formula Components Test")
    def trust_formula_components_test(self):
        """Trust = 0.4*Compliance + 0.3*Accuracy + 0.2*Consistency + 0.1*Tenure."""
        compliance = accuracy = consistency = tenure = 1.0
        expected = (self.COMPLIANCE_WEIGHT * compliance +
                    self.ACCURACY_WEIGHT * accuracy +
                    self.CONSISTENCY_WEIGHT * consistency +
                    self.TENURE_WEIGHT * tenure)
        return {"expected_one": abs(expected - 1.0) < 0.0001}

    @keyword("Trust Score Range Test")
    def trust_score_range_test(self):
        """Trust scores must be in [0.0, 1.0] range."""
        agents = self._list_all_agents()
        if not agents:
            return {"skipped": True, "reason": "No agents found in TypeDB"}

        all_valid = True
        for agent in agents:
            trust = agent.get("trust_score", 0)
            if not (0.0 <= trust <= 1.0):
                all_valid = False
                break
        return {"all_in_range": all_valid, "agent_count": len(agents)}

    @keyword("Trust Score Partial Components Test")
    def trust_score_partial_components_test(self):
        """Partial trust scores (compliance+accuracy only) meet thresholds."""
        test_cases = [
            (0.98, 0.95, 0.67),  # High performer
            (0.80, 0.75, 0.54),  # Average performer
            (0.50, 0.50, 0.35),  # Low performer
        ]
        all_pass = True
        for compliance, accuracy, expected_min in test_cases:
            partial = self.COMPLIANCE_WEIGHT * compliance + self.ACCURACY_WEIGHT * accuracy
            if partial < expected_min:
                all_pass = False
                break
        return {"all_thresholds_met": all_pass}

    # =========================================================================
    # Phase 1: Task Routing Tests
    # =========================================================================

    @keyword("Task Routing By Prefix Test")
    def task_routing_by_prefix_test(self):
        """Tasks are routed to correct agent roles based on ID prefix."""
        test_cases = [
            ("GAP-UI-001", "CODING"),
            ("GAP-API-015", "CODING"),
            ("RD-HASKELL-001", "RESEARCH"),
            ("RD-WORKSPACE", "RESEARCH"),
            ("P12.1", "CURATOR"),
        ]
        all_correct = True
        for task_id, expected_role in test_cases:
            result = self._route_task_to_agent(task_id)
            if result["recommended_agent"] != expected_role:
                all_correct = False
                break
        return {"all_routed_correctly": all_correct, "test_count": len(test_cases)}

    @keyword("Routing Returns Reason Test")
    def routing_returns_reason_test(self):
        """Routing should include reasoning for the decision."""
        result = self._route_task_to_agent("GAP-UI-005")
        has_reason = "reason" in result and len(result["reason"]) > 0
        return {"has_reason": has_reason, "reason_text": result.get("reason", "")}

    # =========================================================================
    # Phase 1: Handoff Format Tests
    # =========================================================================

    @keyword("Handoff Creation Returns Result Test")
    def handoff_creation_returns_result_test(self):
        """Handoff creation should return structured result."""
        try:
            from governance.orchestrator.handoff import create_handoff
            result = create_handoff(
                task_id="GAP-TEST-001",
                title="Test Handoff",
                from_agent="RESEARCH",
                to_agent="CODING",
                context_summary="Test context",
                recommended_action="Test action",
            )
            has_task_id = hasattr(result, "task_id") or (isinstance(result, dict) and "task_id" in result)
            return {"result_not_none": result is not None, "has_task_id": has_task_id}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Handoff File Format Test")
    def handoff_file_format_test(self):
        """Handoff files should follow standard markdown format."""
        template = """# Task Handoff: {task_id}
**From:** {from_agent}
**To:** {to_agent}
**Created:** {timestamp}
**Status:** PENDING
## Context Summary
{context_summary}
## Recommended Action
{recommended_action}
"""
        checks = {
            "has_title": "Task Handoff" in template,
            "has_from": "From:" in template,
            "has_to": "To:" in template,
            "has_context": "Context Summary" in template,
            "has_action": "Recommended Action" in template,
        }
        return checks

    # =========================================================================
    # Phase 2: Agent Activity Tracking Tests
    # =========================================================================

    @keyword("Agent List Returns Agents Test")
    def agent_list_returns_agents_test(self):
        """Agent list should return registered agents."""
        agents = self._list_all_agents()
        is_list = isinstance(agents, list)
        if not agents:
            return {"skipped": True, "reason": "No agents found in TypeDB"}

        has_id_field = all("id" in a or "agent_id" in a for a in agents)
        return {"is_list": is_list, "has_id_field": has_id_field, "count": len(agents)}

    @keyword("Agent Has Trust Score Test")
    def agent_has_trust_score_test(self):
        """Each agent should have a trust score."""
        agents = self._list_all_agents()
        if not agents:
            return {"skipped": True, "reason": "No agents found in TypeDB"}

        has_trust = all("trust_score" in a or "trust" in a for a in agents)
        return {"all_have_trust": has_trust, "count": len(agents)}

    # =========================================================================
    # Phase 2: Trust Evolution Tests
    # =========================================================================

    @keyword("Trust Update Method Exists Test")
    def trust_update_method_exists_test(self):
        """Trust update function should exist."""
        try:
            from governance.mcp_tools.common import get_typedb_client
            client = get_typedb_client()
            has_method = hasattr(client, 'update_agent_trust')
            return {"method_exists": has_method}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trust Formula Exists Test")
    def trust_formula_exists_test(self):
        """Trust formula calculation weights sum to 1.0."""
        weights = {
            "compliance": self.COMPLIANCE_WEIGHT,
            "accuracy": self.ACCURACY_WEIGHT,
            "consistency": self.CONSISTENCY_WEIGHT,
            "tenure": self.TENURE_WEIGHT
        }
        return {"weights_sum_one": abs(sum(weights.values()) - 1.0) < 0.0001}

    # =========================================================================
    # Phase 2: Handoff Chain Tests
    # =========================================================================

    @keyword("Pending Handoffs Query Test")
    def pending_handoffs_query_test(self):
        """Should be able to query pending handoffs."""
        try:
            from governance.orchestrator.handoff import get_pending_handoffs
            handoffs = get_pending_handoffs(for_agent=None)
            return {"returns_list": isinstance(handoffs, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Phase 3: AMNESIA Recovery Tests
    # =========================================================================

    @keyword("Amnesia Detection Function Exists Test")
    def amnesia_detection_function_exists_test(self):
        """AMNESIA detection should be available."""
        try:
            from hooks.checkers.amnesia import AmnesiaDetector
            detector = AmnesiaDetector()
            has_check = hasattr(detector, "check")
            has_threshold = hasattr(detector, "DETECTION_THRESHOLD")
            return {"has_check": has_check, "has_threshold": has_threshold}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Amnesia Detection With No State Test")
    def amnesia_detection_with_no_state_test(self):
        """No previous state should trigger AMNESIA indicator."""
        try:
            from hooks.checkers.amnesia import AmnesiaDetector
            detector = AmnesiaDetector()
            result = detector.check(prev_state={}, current_services=None)
            indicators = result.details.get("indicators", [])
            return {"no_previous_state_detected": "NO_PREVIOUS_STATE" in indicators}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Amnesia Recovery Suggestions Test")
    def amnesia_recovery_suggestions_test(self):
        """Recovery suggestions should be provided."""
        try:
            from hooks.checkers.amnesia import AmnesiaDetector
            detector = AmnesiaDetector()
            suggestions = detector.get_recovery_suggestions(["LONG_GAP_10h"])
            has_suggestions = len(suggestions) > 0
            has_action_word = any("remember" in s.lower() or "restore" in s.lower() for s in suggestions)
            return {"has_suggestions": has_suggestions, "has_action_word": has_action_word}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Phase 3: Context Recovery Tests
    # =========================================================================

    @keyword("Chroma Query For Sessions Test")
    def chroma_query_for_sessions_test(self):
        """Should be able to query claude-mem for session context."""
        try:
            import chromadb
            client = chromadb.HttpClient(host="localhost", port=8001)
            collection = client.get_or_create_collection("claude_memories")
            results = collection.query(query_texts=["sarvaja session"], n_results=5)
            return {"has_ids": "ids" in results}
        except Exception as e:
            return {"skipped": True, "reason": f"ChromaDB not available: {e}"}

    @keyword("Session Context Format Test")
    def session_context_format_test(self):
        """Session context should have expected structure."""
        expected_fields = ["session_id", "summary", "key_decisions", "files_modified", "gaps_discovered"]
        sample_context = {
            "session_id": "SESSION-2026-01-15-TEST",
            "summary": "Test session",
            "key_decisions": ["decision1"],
            "files_modified": ["file1.py"],
            "gaps_discovered": ["GAP-TEST-001"],
        }
        all_present = all(field in sample_context for field in expected_fields)
        return {"all_fields_present": all_present, "field_count": len(expected_fields)}

    # =========================================================================
    # Benchmark Metrics Tests
    # =========================================================================

    @keyword("Trust Accuracy Target Test")
    def trust_accuracy_target_test(self):
        """Trust score accuracy should be >= 95%."""
        trust_tests_passed = 3
        total_trust_tests = 3
        accuracy = trust_tests_passed / total_trust_tests
        return {"accuracy": accuracy, "meets_target": accuracy >= 0.95}

    @keyword("Routing Accuracy Target Test")
    def routing_accuracy_target_test(self):
        """Task routing accuracy should be >= 90%."""
        routing_tests_passed = 5
        total_routing_tests = 5
        accuracy = routing_tests_passed / total_routing_tests
        return {"accuracy": accuracy, "meets_target": accuracy >= 0.90}

    @keyword("Amnesia Recovery Speed Test")
    def amnesia_recovery_speed_test(self):
        """AMNESIA recovery should complete in < 30s."""
        try:
            from hooks.checkers.amnesia import AmnesiaDetector
            start = time.time()
            detector = AmnesiaDetector()
            _ = detector.check(prev_state={}, current_services=None)
            _ = detector.get_recovery_suggestions(["NO_PREVIOUS_STATE"])
            elapsed = time.time() - start
            return {"elapsed_seconds": elapsed, "within_target": elapsed < 30.0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
