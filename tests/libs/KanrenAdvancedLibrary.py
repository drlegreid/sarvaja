"""
Robot Framework Library for Kanren Advanced Tests.

Per KAN-002: Kanren Constraint Engine - Advanced Module.
Split from KanrenConstraintsLibrary.py per DOC-SIZE-01-v1.

Covers: Rule Conflict Detection, KAN-004 TypeDB Loader, KAN-005 Performance Benchmark.
"""
from robot.api.deco import keyword


class KanrenAdvancedLibrary:
    """Library for testing Kanren advanced features."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Rule Conflict Detection Tests
    # =========================================================================

    @keyword("Conflicting Priorities Detected")
    def conflicting_priorities_detected(self):
        """Detects priority conflicts in same category."""
        try:
            from governance.kanren_constraints import conflicting_priorities, RuleContext
            rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
            rule2 = RuleContext("RULE-002", "MEDIUM", "ACTIVE", "governance")
            return {"has_conflict": conflicting_priorities(rule1, rule2) is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("No Conflict Different Category")
    def no_conflict_different_category(self):
        """No conflict for different categories."""
        try:
            from governance.kanren_constraints import conflicting_priorities, RuleContext
            rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
            rule2 = RuleContext("RULE-002", "MEDIUM", "ACTIVE", "technical")
            return {"no_conflict": conflicting_priorities(rule1, rule2) is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("No Conflict Same Priority")
    def no_conflict_same_priority(self):
        """No conflict for same priority."""
        try:
            from governance.kanren_constraints import conflicting_priorities, RuleContext
            rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
            rule2 = RuleContext("RULE-002", "CRITICAL", "ACTIVE", "governance")
            return {"no_conflict": conflicting_priorities(rule1, rule2) is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Find All Conflicts")
    def find_all_conflicts(self):
        """Finds all conflicts in rule set."""
        try:
            from governance.kanren_constraints import find_rule_conflicts, RuleContext
            rules = [
                RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance"),
                RuleContext("RULE-002", "HIGH", "ACTIVE", "governance"),
                RuleContext("RULE-003", "MEDIUM", "ACTIVE", "governance"),
                RuleContext("RULE-004", "HIGH", "ACTIVE", "technical"),
            ]
            conflicts = find_rule_conflicts(rules)
            return {"conflict_count": len(conflicts) == 3}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # KAN-004: TypeDB -> Kanren Loader Tests
    # =========================================================================

    @keyword("Loader Imports")
    def loader_imports(self):
        """Loader module can be imported."""
        try:
            from governance.kanren import (
                RuleConstraint,
                TypeDBKanrenBridge,
                load_rules_from_typedb,
                populate_kanren_facts,
                query_critical_rules,
            )
            return {
                "rule_constraint": RuleConstraint is not None,
                "bridge": TypeDBKanrenBridge is not None,
                "load_func": load_rules_from_typedb is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Constraint From Dict")
    def rule_constraint_from_dict(self):
        """RuleConstraint creates from TypeDB query result."""
        try:
            from governance.kanren import RuleConstraint
            data = {
                "id": "RULE-011",
                "semantic_id": "GOV-BICAM-01-v1",
                "name": "Multi-Agent Governance Protocol",
                "category": "governance",
                "priority": "CRITICAL",
                "directive": "Bicameral model",
                "rule_type": "FOUNDATIONAL",
            }
            constraint = RuleConstraint.from_dict(data)
            return {
                "rule_id": constraint.rule_id == "RULE-011",
                "semantic_id": constraint.semantic_id == "GOV-BICAM-01-v1",
                "priority": constraint.priority == "CRITICAL",
                "rule_type": constraint.rule_type == "FOUNDATIONAL"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Load Rules From JSON")
    def load_rules_from_json(self):
        """load_rules_from_typedb parses JSON correctly."""
        try:
            from governance.kanren import load_rules_from_typedb
            json_result = '''[
                {"id": "RULE-001", "priority": "CRITICAL", "category": "governance", "rule_type": "FOUNDATIONAL"},
                {"id": "RULE-002", "priority": "HIGH", "category": "testing", "rule_type": "OPERATIONAL"}
            ]'''
            rules = load_rules_from_typedb(json_result)
            return {
                "count": len(rules) == 2,
                "first_id": rules[0].rule_id == "RULE-001",
                "first_priority": rules[0].priority == "CRITICAL",
                "second_id": rules[1].rule_id == "RULE-002",
                "second_priority": rules[1].priority == "HIGH"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Load Rules Empty Input")
    def load_rules_empty_input(self):
        """load_rules_from_typedb handles empty input."""
        try:
            from governance.kanren import load_rules_from_typedb
            return {
                "none_empty": load_rules_from_typedb(None) == [],
                "str_empty": load_rules_from_typedb("") == [],
                "invalid_empty": load_rules_from_typedb("invalid json") == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Populate Kanren Facts")
    def populate_kanren_facts(self):
        """populate_kanren_facts creates Kanren relations."""
        try:
            from governance.kanren import load_rules_from_typedb, populate_kanren_facts
            json_result = '''[
                {"id": "TEST-RULE-001", "priority": "CRITICAL", "category": "governance", "rule_type": "FOUNDATIONAL"},
                {"id": "TEST-RULE-002", "priority": "HIGH", "category": "testing", "rule_type": "OPERATIONAL"},
                {"id": "TEST-RULE-003", "priority": "CRITICAL", "category": "autonomy", "rule_type": "TECHNICAL"}
            ]'''
            rules = load_rules_from_typedb(json_result)
            counts = populate_kanren_facts(rules)
            return {
                "priority_count": counts["priority"] == 3,
                "critical_count": counts["critical"] == 2,
                "rule_type_count": counts["rule_type"] == 3,
                "category_count": counts["category"] == 3
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("TypeDB Kanren Bridge Lifecycle")
    def typedb_kanren_bridge_lifecycle(self):
        """TypeDBKanrenBridge manages load/validate lifecycle."""
        try:
            from governance.kanren import TypeDBKanrenBridge
            bridge = TypeDBKanrenBridge()

            not_loaded = bridge.is_loaded() is False
            result = bridge.validate_rule("RULE-001")
            validation_fails = result["compliant"] is False and "Rules not loaded" in result["violations"][0]

            json_result = '''[
                {"id": "RULE-001", "priority": "HIGH", "category": "governance", "rule_type": "FOUNDATIONAL"}
            ]'''
            counts = bridge.load_from_mcp(json_result)

            return {
                "initially_not_loaded": not_loaded,
                "validation_fails_unloaded": validation_fails,
                "loaded_after": bridge.is_loaded() is True,
                "priority_count": counts["priority"] == 1,
                "rules_count": len(bridge.get_rules()) == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Rule Compliance Expert")
    def validate_rule_compliance_expert(self):
        """Expert agent can comply with any rule."""
        try:
            from governance.kanren import TypeDBKanrenBridge
            bridge = TypeDBKanrenBridge()
            json_result = '''[
                {"id": "RULE-CRITICAL", "priority": "CRITICAL", "rule_type": "FOUNDATIONAL"}
            ]'''
            bridge.load_from_mcp(json_result)
            result = bridge.validate_rule(
                "RULE-CRITICAL",
                has_evidence=True,
                agent_trust=0.95
            )
            return {
                "compliant": result["compliant"] is True,
                "trust_level": result["trust_level"] == "expert"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Rule Compliance Low Trust")
    def validate_rule_compliance_low_trust(self):
        """Low trust agent cannot comply with CRITICAL rules."""
        try:
            from governance.kanren import TypeDBKanrenBridge
            bridge = TypeDBKanrenBridge()
            json_result = '''[
                {"id": "RULE-CRITICAL", "priority": "CRITICAL", "rule_type": "FOUNDATIONAL"}
            ]'''
            bridge.load_from_mcp(json_result)
            result = bridge.validate_rule(
                "RULE-CRITICAL",
                has_evidence=True,
                agent_trust=0.3
            )
            return {
                "not_compliant": result["compliant"] is False,
                "has_violation": "Trust level 'restricted' cannot execute CRITICAL priority" in result["violations"]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Rule Missing Evidence")
    def validate_rule_missing_evidence(self):
        """Missing evidence causes compliance failure for CRITICAL rules."""
        try:
            from governance.kanren import TypeDBKanrenBridge
            bridge = TypeDBKanrenBridge()
            json_result = '''[
                {"id": "RULE-CRITICAL", "priority": "CRITICAL", "rule_type": "FOUNDATIONAL"}
            ]'''
            bridge.load_from_mcp(json_result)
            result = bridge.validate_rule(
                "RULE-CRITICAL",
                has_evidence=False,
                agent_trust=0.95
            )
            return {
                "not_compliant": result["compliant"] is False,
                "has_evidence_violation": any("requires evidence" in v for v in result["violations"])
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Rules By Category")
    def get_rules_by_category(self):
        """Bridge filters rules by category."""
        try:
            from governance.kanren import TypeDBKanrenBridge
            bridge = TypeDBKanrenBridge()
            json_result = '''[
                {"id": "RULE-001", "priority": "CRITICAL", "category": "governance"},
                {"id": "RULE-002", "priority": "HIGH", "category": "testing"},
                {"id": "RULE-003", "priority": "HIGH", "category": "governance"}
            ]'''
            bridge.load_from_mcp(json_result)
            gov_rules = bridge.get_rules_by_category("governance")
            test_rules = bridge.get_rules_by_category("testing")
            return {
                "gov_count": len(gov_rules) == 2,
                "test_count": len(test_rules) == 1,
                "all_gov": all(r.category == "governance" for r in gov_rules)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # KAN-005: Performance Benchmark Tests
    # =========================================================================

    @keyword("Benchmark Imports")
    def benchmark_imports(self):
        """Benchmark module can be imported."""
        try:
            from governance.kanren import (
                BenchmarkResult,
                run_all_benchmarks,
                compare_kanren_vs_direct,
            )
            return {
                "result": BenchmarkResult is not None,
                "run_func": run_all_benchmarks is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Benchmark Result Dataclass")
    def benchmark_result_dataclass(self):
        """BenchmarkResult has correct fields."""
        try:
            from governance.kanren import BenchmarkResult
            result = BenchmarkResult(
                name="test_bench",
                iterations=100,
                total_ms=10.0,
                avg_ms=0.1,
                min_ms=0.05,
                max_ms=0.2,
                target_ms=1.0,
                passed=True
            )
            return {
                "name_correct": result.name == "test_bench",
                "avg_correct": result.avg_ms == 0.1,
                "passed": result.passed is True,
                "has_pass": "PASS" in result.summary()
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Run All Benchmarks Returns Results")
    def run_all_benchmarks_returns_results(self):
        """run_all_benchmarks returns list of results."""
        try:
            from governance.kanren import run_all_benchmarks
            results = run_all_benchmarks()
            return {
                "is_list": isinstance(results, list),
                "has_benchmarks": len(results) >= 7
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("All Benchmarks Pass")
    def all_benchmarks_pass(self):
        """All benchmarks should pass their targets."""
        try:
            from governance.kanren import run_all_benchmarks
            results = run_all_benchmarks()
            failed = [r for r in results if not r.passed]
            return {
                "all_passed": len(failed) == 0,
                "failed_names": [r.name for r in failed] if failed else []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Kanren Under 100ms Target")
    def kanren_under_100ms_target(self):
        """Total Kanren validation time is under 100ms."""
        try:
            from governance.kanren import compare_kanren_vs_direct
            comparison = compare_kanren_vs_direct()
            total_ms = comparison["summary"]["total_kanren_avg_ms"]
            return {
                "under_target": total_ms < 100.0,
                "actual_ms": total_ms
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Compare Returns Overhead")
    def compare_returns_overhead(self):
        """compare_kanren_vs_direct returns overhead metrics."""
        try:
            from governance.kanren import compare_kanren_vs_direct
            comparison = compare_kanren_vs_direct()
            return {
                "has_trust_level": "trust_level" in comparison,
                "has_kanren_ms": "kanren_ms" in comparison["trust_level"],
                "has_direct_ms": "direct_ms" in comparison["trust_level"],
                "has_overhead": "overhead_pct" in comparison["trust_level"]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Benchmark Summary Pass")
    def benchmark_summary_pass(self):
        """Benchmark summary should show all passed."""
        try:
            from governance.kanren import compare_kanren_vs_direct
            comparison = compare_kanren_vs_direct()
            return {"all_passed": comparison["summary"]["all_kanren_passed"] is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
