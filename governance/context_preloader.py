"""
Context Preloader - P12.6

Auto-loads DECISION-* files and strategic context at session start.
Per GAP-CTX-002: Context Auto-Loading.

Created: 2026-01-03
Per: PHASE-12, GAP-CTX-002, RULE-024
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Project root for finding evidence files
PROJECT_ROOT = Path(__file__).parent.parent


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


class ContextPreloader:
    """
    Preloads strategic context at session start.

    Per P12.6: Context Auto-Loading.
    Per GAP-CTX-002: Agents need strategic context.

    Usage:
        preloader = ContextPreloader()
        context = preloader.load_context()
        agent_prompt = context.to_agent_prompt()
    """

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or PROJECT_ROOT
        self.evidence_dir = self.project_root / "evidence"
        self.claude_md_path = self.project_root / "CLAUDE.md"
        self._cached_context: Optional[ContextSummary] = None
        self._cache_time: Optional[datetime] = None
        # Cache for 5 minutes
        self._cache_ttl_seconds = 300

    def load_context(self, force_refresh: bool = False) -> ContextSummary:
        """
        Load all strategic context.

        Args:
            force_refresh: Skip cache and reload

        Returns:
            ContextSummary with all loaded context
        """
        # Check cache
        if not force_refresh and self._cached_context:
            if self._cache_time:
                elapsed = (datetime.now() - self._cache_time).total_seconds()
                if elapsed < self._cache_ttl_seconds:
                    logger.debug("Using cached context")
                    return self._cached_context

        logger.info("Loading strategic context...")

        context = ContextSummary()

        # Load decisions from evidence files
        context.decisions = self._load_decisions()

        # Load technology choices from CLAUDE.md
        context.technology_choices = self._load_technology_choices()

        # Detect active phase
        context.active_phase = self._detect_active_phase()

        # Count open gaps
        context.open_gaps_count = self._count_open_gaps()

        # Cache result
        self._cached_context = context
        self._cache_time = datetime.now()

        logger.info(
            f"Context loaded: {len(context.decisions)} decisions, "
            f"{len(context.technology_choices)} tech choices, "
            f"phase={context.active_phase}"
        )

        return context

    def _load_decisions(self) -> List[Decision]:
        """Load decisions from evidence/ directory."""
        decisions = []

        if not self.evidence_dir.exists():
            logger.warning(f"Evidence directory not found: {self.evidence_dir}")
            return decisions

        # Find DECISION-*.md files
        decision_files = list(self.evidence_dir.glob("DECISION-*.md"))

        # Also find SESSION-DECISIONS-*.md files
        session_decision_files = list(self.evidence_dir.glob("SESSION-DECISIONS-*.md"))

        # Parse standalone decision files first
        for file_path in decision_files:
            decision = self._parse_decision_file(file_path)
            if decision:
                decisions.append(decision)

        # Parse decisions from session files
        for file_path in session_decision_files:
            session_decisions = self._parse_session_decisions_file(file_path)
            decisions.extend(session_decisions)

        # Deduplicate by ID, keeping newest
        seen = {}
        for d in decisions:
            if d.id not in seen or d.date > seen[d.id].date:
                seen[d.id] = d

        return list(seen.values())

    def _parse_decision_file(self, file_path: Path) -> Optional[Decision]:
        """Parse a standalone DECISION-*.md file."""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract ID from filename or content
            id_match = re.search(r"DECISION-(\d+)", file_path.name)
            if id_match:
                decision_id = f"DECISION-{id_match.group(1)}"
            else:
                decision_id = file_path.stem

            # Extract title
            title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            name = title_match.group(1) if title_match else decision_id

            # Extract status
            status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
            status = status_match.group(1) if status_match else "UNKNOWN"

            # Extract date
            date_match = re.search(r"\*\*Date\*\*:\s*([\d-]+)", content)
            date = date_match.group(1) if date_match else ""

            # Extract summary (first paragraph after ## Summary)
            summary_match = re.search(
                r"##\s*Summary\s*\n+(.+?)(?=\n##|\n\*\*|\Z)",
                content,
                re.DOTALL
            )
            summary = summary_match.group(1).strip()[:200] if summary_match else ""

            return Decision(
                id=decision_id,
                name=name,
                status=status,
                date=date,
                summary=summary,
                source_file=str(file_path),
            )
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None

    def _parse_session_decisions_file(self, file_path: Path) -> List[Decision]:
        """Parse decisions from a SESSION-DECISIONS-*.md file."""
        decisions = []

        try:
            content = file_path.read_text(encoding="utf-8")

            # Find all DECISION-XXX sections
            pattern = r"##\s+(DECISION-\d+):\s+(.+?)\n"
            matches = re.finditer(pattern, content)

            for match in matches:
                decision_id = match.group(1)
                name = match.group(2).strip()

                # Find the section content
                start = match.end()
                next_section = re.search(r"\n##\s+", content[start:])
                end = start + next_section.start() if next_section else len(content)
                section = content[start:end]

                # Extract status
                status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", section)
                status = status_match.group(1) if status_match else "UNKNOWN"

                # Extract date
                date_match = re.search(r"\*\*Date\*\*:\s*([\d-]+)", section)
                date = date_match.group(1) if date_match else ""

                # Extract decision text
                decision_match = re.search(r"\*\*Decision\*\*:\s*(.+?)(?=\n\*\*|\n##|\Z)", section, re.DOTALL)
                summary = decision_match.group(1).strip()[:150] if decision_match else ""

                decisions.append(Decision(
                    id=decision_id,
                    name=name,
                    status=status,
                    date=date,
                    summary=summary,
                    source_file=str(file_path),
                ))
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")

        return decisions

    def _load_technology_choices(self) -> List[TechnologyChoice]:
        """Load technology decisions from CLAUDE.md."""
        choices = []

        if not self.claude_md_path.exists():
            logger.warning(f"CLAUDE.md not found: {self.claude_md_path}")
            return choices

        try:
            content = self.claude_md_path.read_text(encoding="utf-8")

            # Find Technology Decisions table
            # Pattern: | Decision | Choice | NOT Using | Rationale |
            table_pattern = r"\|\s*\*\*?(.+?)\*\*?\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|"

            # Find the Technology Decisions section
            tech_section = re.search(
                r"##\s*Technology Decisions.*?\n(.*?)(?=\n##|\Z)",
                content,
                re.DOTALL | re.IGNORECASE
            )

            if tech_section:
                section_content = tech_section.group(1)

                # Parse table rows
                for line in section_content.split("\n"):
                    if "|" in line and "---" not in line and "Decision" not in line:
                        parts = [p.strip() for p in line.split("|")[1:-1]]
                        if len(parts) >= 4:
                            area = parts[0].replace("**", "")
                            choice = parts[1]
                            not_using = parts[2]
                            rationale = parts[3]

                            if area and choice and area != "Decision":
                                choices.append(TechnologyChoice(
                                    area=area,
                                    choice=choice,
                                    not_using=not_using,
                                    rationale=rationale,
                                ))
        except Exception as e:
            logger.warning(f"Failed to load technology choices: {e}")

        return choices

    def _detect_active_phase(self) -> Optional[str]:
        """Detect the currently active phase from backlog files."""
        phases_dir = self.project_root / "docs" / "backlog" / "phases"

        if not phases_dir.exists():
            return None

        # Find PHASE-*.md files and check status
        for phase_file in sorted(phases_dir.glob("PHASE-*.md"), reverse=True):
            try:
                content = phase_file.read_text(encoding="utf-8")

                # Check if IN PROGRESS
                if "IN PROGRESS" in content:
                    # Extract phase number
                    match = re.search(r"PHASE-(\d+)", phase_file.name)
                    if match:
                        return f"Phase {match.group(1)}"
            except Exception:
                continue

        return None

    def _count_open_gaps(self) -> int:
        """Count open gaps from GAP-INDEX.md."""
        gap_index = self.project_root / "docs" / "gaps" / "GAP-INDEX.md"

        if not gap_index.exists():
            return 0

        try:
            content = gap_index.read_text(encoding="utf-8")

            # Count OPEN entries
            open_count = len(re.findall(r"\|\s*OPEN\s*\|", content))
            return open_count
        except Exception:
            return 0

    def invalidate_cache(self) -> None:
        """Invalidate the cached context."""
        self._cached_context = None
        self._cache_time = None


# Global preloader instance
_preloader: Optional[ContextPreloader] = None


def get_context_preloader() -> ContextPreloader:
    """Get or create global context preloader."""
    global _preloader
    if _preloader is None:
        _preloader = ContextPreloader()
    return _preloader


def preload_session_context(force_refresh: bool = False) -> ContextSummary:
    """
    Convenience function to preload context.

    Called at session start per P12.6.
    """
    return get_context_preloader().load_context(force_refresh)


def get_agent_context_prompt() -> str:
    """
    Get context prompt for agent injection.

    Returns markdown summary of strategic context.
    """
    context = preload_session_context()
    return context.to_agent_prompt()
