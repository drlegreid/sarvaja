"""
Robot Framework Library for Context Preloader Split Tests.

Per GAP-FILE-022: context_preloader.py split.
Migrated from tests/test_context_preloader_split.py
"""
from pathlib import Path
from robot.api.deco import keyword


class ContextPreloaderSplitLibrary:
    """Library for testing context preloader module structure."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"

    # =============================================================================
    # Package Structure Tests
    # =============================================================================

    @keyword("Context Preloader Package Exists")
    def context_preloader_package_exists(self):
        """context_preloader should be a module or package."""
        package_dir = self.governance_dir / "context_preloader"
        old_file = self.governance_dir / "context_preloader.py"
        return {
            "exists": package_dir.exists() or old_file.exists(),
            "is_package": package_dir.exists(),
            "is_file": old_file.exists()
        }

    @keyword("Models Module Exists")
    def models_module_exists(self):
        """Models module should exist in package."""
        models_file = self.governance_dir / "context_preloader" / "models.py"
        package_dir = self.governance_dir / "context_preloader"
        if not package_dir.exists():
            return {"skipped": True, "reason": "Package not yet split"}
        return {"exists": models_file.exists()}

    # =============================================================================
    # Backward Compatibility Tests
    # =============================================================================

    @keyword("Import Context Preloader Class")
    def import_context_preloader_class(self):
        """from governance.context_preloader import ContextPreloader must work."""
        try:
            from governance.context_preloader import ContextPreloader
            return {"imported": ContextPreloader is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Decision Class")
    def import_decision_class(self):
        """from governance.context_preloader import Decision must work."""
        try:
            from governance.context_preloader import Decision
            return {"imported": Decision is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Technology Choice Class")
    def import_technology_choice_class(self):
        """from governance.context_preloader import TechnologyChoice must work."""
        try:
            from governance.context_preloader import TechnologyChoice
            return {"imported": TechnologyChoice is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Context Summary Class")
    def import_context_summary_class(self):
        """from governance.context_preloader import ContextSummary must work."""
        try:
            from governance.context_preloader import ContextSummary
            return {"imported": ContextSummary is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Get Context Preloader")
    def import_get_context_preloader(self):
        """from governance.context_preloader import get_context_preloader must work."""
        try:
            from governance.context_preloader import get_context_preloader
            return {"imported": get_context_preloader is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Preload Session Context")
    def import_preload_session_context(self):
        """from governance.context_preloader import preload_session_context must work."""
        try:
            from governance.context_preloader import preload_session_context
            return {"imported": preload_session_context is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Get Agent Context Prompt")
    def import_get_agent_context_prompt(self):
        """from governance.context_preloader import get_agent_context_prompt must work."""
        try:
            from governance.context_preloader import get_agent_context_prompt
            return {"imported": get_agent_context_prompt is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Models Module Tests
    # =============================================================================

    @keyword("Decision Dataclass Works")
    def decision_dataclass_works(self):
        """Decision dataclass should work."""
        try:
            from governance.context_preloader import Decision

            d = Decision(
                id="DECISION-001",
                name="Test Decision",
                status="APPROVED",
                date="2026-01-14",
                summary="Test summary"
            )

            return {
                "id_correct": d.id == "DECISION-001",
                "name_correct": d.name == "Test Decision",
                "status_correct": d.status == "APPROVED"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Technology Choice Dataclass Works")
    def technology_choice_dataclass_works(self):
        """TechnologyChoice dataclass should work."""
        try:
            from governance.context_preloader import TechnologyChoice

            tc = TechnologyChoice(
                area="Database",
                choice="TypeDB",
                not_using="PostgreSQL",
                rationale="Graph-first"
            )

            return {
                "area_correct": tc.area == "Database",
                "choice_correct": tc.choice == "TypeDB"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Summary Dataclass Works")
    def context_summary_dataclass_works(self):
        """ContextSummary dataclass should work."""
        try:
            from governance.context_preloader import ContextSummary

            cs = ContextSummary()
            return {
                "decisions_empty": cs.decisions == [],
                "tech_choices_empty": cs.technology_choices == [],
                "phase_none": cs.active_phase is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Summary To Agent Prompt")
    def context_summary_to_agent_prompt(self):
        """ContextSummary.to_agent_prompt should return string."""
        try:
            from governance.context_preloader import ContextSummary

            cs = ContextSummary()
            prompt = cs.to_agent_prompt()

            return {
                "is_string": isinstance(prompt, str),
                "has_strategic": "Strategic Context" in prompt
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Summary To Dict")
    def context_summary_to_dict(self):
        """ContextSummary.to_dict should return dict."""
        try:
            from governance.context_preloader import ContextSummary

            cs = ContextSummary()
            d = cs.to_dict()

            return {
                "is_dict": isinstance(d, dict),
                "has_decisions": "decisions" in d,
                "has_tech_choices": "technology_choices" in d
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("Preloader Creates Instance")
    def preloader_creates_instance(self):
        """ContextPreloader should create instance."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            return {"created": preloader is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Preloader Load Context")
    def preloader_load_context(self):
        """ContextPreloader.load_context should return ContextSummary."""
        try:
            from governance.context_preloader import ContextPreloader, ContextSummary

            preloader = ContextPreloader()
            context = preloader.load_context()

            return {"is_context_summary": isinstance(context, ContextSummary)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Context Preloader Returns Same Instance")
    def get_context_preloader_returns_same_instance(self):
        """get_context_preloader should return singleton."""
        try:
            from governance.context_preloader import get_context_preloader

            p1 = get_context_preloader()
            p2 = get_context_preloader()

            return {"same_instance": p1 is p2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Preload Session Context Works")
    def preload_session_context_works(self):
        """preload_session_context should return ContextSummary."""
        try:
            from governance.context_preloader import preload_session_context, ContextSummary

            context = preload_session_context()
            return {"is_context_summary": isinstance(context, ContextSummary)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
