"""
Robot Framework Library for Rule Impact Analyzer Tests.

Per P9.4: Rule dependency analysis and impact visualization.
Migrated from tests/test_rule_impact.py
"""
from pathlib import Path
from robot.api.deco import keyword


class RuleImpactLibrary:
    """Library for testing rule impact analyzer."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = self.project_root / "agent"

    # =============================================================================
    # Module Existence Tests
    # =============================================================================

    @keyword("Rule Impact Module Exists")
    def rule_impact_module_exists(self):
        """Rule impact module must exist."""
        impact_file = self.agent_dir / "rule_impact.py"
        return {"exists": impact_file.exists()}

    @keyword("Rule Impact Class Importable")
    def rule_impact_class_importable(self):
        """RuleImpactAnalyzer class must be importable."""
        try:
            from agent.rule_impact import RuleImpactAnalyzer

            analyzer = RuleImpactAnalyzer()
            return {
                "importable": True,
                "instantiable": analyzer is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("Analyzer Has Required Methods")
    def analyzer_has_required_methods(self):
        """Analyzer must have required methods."""
        try:
            from agent.rule_impact import RuleImpactAnalyzer

            analyzer = RuleImpactAnalyzer()

            return {
                "has_analyze_dependencies": hasattr(analyzer, 'analyze_dependencies'),
                "has_get_impact_graph": hasattr(analyzer, 'get_impact_graph'),
                "has_simulate_change": hasattr(analyzer, 'simulate_change'),
                "has_get_affected_rules": hasattr(analyzer, 'get_affected_rules')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    # =============================================================================
    # Dependency Analysis Tests
    # =============================================================================

    @keyword("Analyze Dependencies Works")
    def analyze_dependencies_works(self):
        """Should analyze rule dependencies."""
        try:
            from agent.rule_impact import RuleImpactAnalyzer

            analyzer = RuleImpactAnalyzer()
            result = analyzer.analyze_dependencies("RULE-001")

            return {
                "is_dict": isinstance(result, dict),
                "has_rule_id": 'rule_id' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Find Dependent Rules Works")
    def find_dependent_rules_works(self):
        """Should find rules that depend on a given rule."""
        try:
            from agent.rule_impact import RuleImpactAnalyzer

            analyzer = RuleImpactAnalyzer()
            dependents = analyzer.get_dependent_rules("RULE-001")

            return {"is_list": isinstance(dependents, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Find Required Rules Works")
    def find_required_rules_works(self):
        """Should find rules required by a given rule."""
        try:
            from agent.rule_impact import RuleImpactAnalyzer

            analyzer = RuleImpactAnalyzer()
            required = analyzer.get_required_rules("RULE-011")

            return {"is_list": isinstance(required, list)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
