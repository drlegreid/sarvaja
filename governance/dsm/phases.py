"""
DSP Phases Enum
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Defines the Deep Sleep Protocol phases per RULE-012.
"""
from typing import List, Optional
from enum import Enum


class DSPPhase(Enum):
    """Deep Sleep Protocol phases per RULE-012."""
    IDLE = "idle"              # Not in a cycle
    AUDIT = "audit"            # Inventory gaps, orphans, loops
    HYPOTHESIZE = "hypothesize"  # Form improvement theories
    MEASURE = "measure"        # Quantify current state
    OPTIMIZE = "optimize"      # Apply improvements
    VALIDATE = "validate"      # Run tests
    DREAM = "dream"            # Autonomous exploration
    REPORT = "report"          # Generate evidence
    COMPLETE = "complete"      # Cycle finished

    @classmethod
    def phase_order(cls) -> List["DSPPhase"]:
        """Return phases in order (excluding IDLE and COMPLETE)."""
        return [
            cls.AUDIT,
            cls.HYPOTHESIZE,
            cls.MEASURE,
            cls.OPTIMIZE,
            cls.VALIDATE,
            cls.DREAM,
            cls.REPORT
        ]

    def next_phase(self) -> Optional["DSPPhase"]:
        """Get next phase in sequence."""
        order = self.phase_order()
        if self == DSPPhase.IDLE:
            return DSPPhase.AUDIT
        if self == DSPPhase.COMPLETE:
            return None
        try:
            idx = order.index(self)
            if idx + 1 < len(order):
                return order[idx + 1]
            return DSPPhase.COMPLETE
        except ValueError:
            return None

    def prev_phase(self) -> Optional["DSPPhase"]:
        """Get previous phase in sequence."""
        order = self.phase_order()
        if self in (DSPPhase.IDLE, DSPPhase.AUDIT):
            return DSPPhase.IDLE
        if self == DSPPhase.COMPLETE:
            return DSPPhase.REPORT
        try:
            idx = order.index(self)
            if idx > 0:
                return order[idx - 1]
            return DSPPhase.IDLE
        except ValueError:
            return None

    @property
    def required_mcps(self) -> List[str]:
        """MCPs required for this phase per RULE-012."""
        mcp_map = {
            DSPPhase.AUDIT: ["claude-mem", "governance"],
            DSPPhase.HYPOTHESIZE: ["sequential-thinking"],
            DSPPhase.MEASURE: ["powershell", "llm-sandbox"],
            DSPPhase.OPTIMIZE: ["filesystem", "git"],
            DSPPhase.VALIDATE: ["pytest", "llm-sandbox"],
            DSPPhase.DREAM: ["claude-mem", "sequential-thinking"],
            DSPPhase.REPORT: ["filesystem", "git"]
        }
        return mcp_map.get(self, [])
