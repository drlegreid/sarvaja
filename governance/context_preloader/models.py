"""
Context Preloader Models.

Per GAP-FILE-022: Extracted from context_preloader.py
Per DOC-SIZE-01-v1: Files under 400 lines

Data classes for strategic context representation.

Created: 2026-01-03
Refactored: 2026-01-14
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Decision:
    """Parsed strategic decision."""
    id: str
    name: str
    status: str
    date: str
    summary: str
    rationale: str = ""
    source_file: str = ""


@dataclass
class TechnologyChoice:
    """Technology decision from CLAUDE.md."""
    area: str
    choice: str
    not_using: str
    rationale: str


@dataclass
class ContextSummary:
    """Summary of preloaded context."""
    decisions: List[Decision] = field(default_factory=list)
    technology_choices: List[TechnologyChoice] = field(default_factory=list)
    active_phase: Optional[str] = None
    open_gaps_count: int = 0
    loaded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_agent_prompt(self) -> str:
        """
        Convert to agent-friendly context prompt.

        This is injected into agent context at session start.
        """
        lines = [
            "## Strategic Context (Auto-Loaded)",
            "",
        ]

        # Technology decisions (most important)
        if self.technology_choices:
            lines.append("### Technology Decisions")
            lines.append("| Area | Use | NOT Using |")
            lines.append("|------|-----|-----------|")
            for tc in self.technology_choices[:6]:
                lines.append(f"| {tc.area} | {tc.choice} | {tc.not_using} |")
            lines.append("")

        # Strategic decisions
        if self.decisions:
            lines.append("### Active Decisions")
            for d in self.decisions:
                if d.status.upper() in ("APPROVED", "IMPLEMENTED", "ACTIVE"):
                    lines.append(f"- **{d.id}**: {d.name} ({d.status})")
            lines.append("")

        # Current phase
        if self.active_phase:
            lines.append(f"### Current Phase: {self.active_phase}")
            lines.append("")

        lines.append(f"*Context loaded at {self.loaded_at}*")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decisions": [
                {
                    "id": d.id,
                    "name": d.name,
                    "status": d.status,
                    "summary": d.summary,
                }
                for d in self.decisions
            ],
            "technology_choices": [
                {
                    "area": tc.area,
                    "choice": tc.choice,
                    "not_using": tc.not_using,
                }
                for tc in self.technology_choices
            ],
            "active_phase": self.active_phase,
            "open_gaps_count": self.open_gaps_count,
            "loaded_at": self.loaded_at,
        }


__all__ = ["Decision", "TechnologyChoice", "ContextSummary"]
