"""Context Preloader Core. Per P12.6, GAP-FILE-022. Auto-loads DECISION files at session start."""

import re
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .models import Decision, TechnologyChoice, ContextSummary

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent.parent

class ContextPreloader:
    """Preloads strategic context at session start. Per P12.6, GAP-CTX-002."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or PROJECT_ROOT
        self.evidence_dir = self.project_root / "evidence"
        self.claude_md_path = self.project_root / "CLAUDE.md"
        self._cached_context: Optional[ContextSummary] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl_seconds = 300

    def load_context(self, force_refresh: bool = False) -> ContextSummary:
        """Load all strategic context."""
        if not force_refresh and self._cached_context and self._cache_time:
            if (datetime.now() - self._cache_time).total_seconds() < self._cache_ttl_seconds:
                return self._cached_context
        logger.info("Loading strategic context...")
        context = ContextSummary()
        context.decisions = self._load_decisions()
        context.technology_choices = self._load_technology_choices()
        context.active_phase = self._detect_active_phase()
        context.open_gaps_count = self._count_open_gaps()
        self._cached_context, self._cache_time = context, datetime.now()
        logger.info(f"Context loaded: {len(context.decisions)} decisions, {len(context.technology_choices)} tech choices")
        return context

    def _load_decisions(self) -> List[Decision]:
        """Load decisions from evidence/ directory."""
        decisions = []
        if not self.evidence_dir.exists():
            return decisions
        for fp in self.evidence_dir.glob("DECISION-*.md"):
            if d := self._parse_decision_file(fp):
                decisions.append(d)
        for fp in self.evidence_dir.glob("SESSION-DECISIONS-*.md"):
            decisions.extend(self._parse_session_decisions_file(fp))
        seen = {}
        for d in decisions:
            if d.id not in seen or d.date > seen[d.id].date:
                seen[d.id] = d
        return list(seen.values())

    def _parse_decision_file(self, file_path: Path) -> Optional[Decision]:
        """Parse a standalone DECISION-*.md file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            id_match = re.search(r"DECISION-(\d+)", file_path.name)
            decision_id = f"DECISION-{id_match.group(1)}" if id_match else file_path.stem
            title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
            date_match = re.search(r"\*\*Date\*\*:\s*([\d-]+)", content)
            summary_match = re.search(r"##\s*Summary\s*\n+(.+?)(?=\n##|\n\*\*|\Z)", content, re.DOTALL)
            return Decision(
                id=decision_id, name=title_match.group(1) if title_match else decision_id,
                status=status_match.group(1) if status_match else "UNKNOWN",
                date=date_match.group(1) if date_match else "",
                summary=summary_match.group(1).strip()[:200] if summary_match else "",
                source_file=str(file_path))
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None

    def _parse_session_decisions_file(self, file_path: Path) -> List[Decision]:
        """Parse decisions from a SESSION-DECISIONS-*.md file."""
        decisions = []
        try:
            content = file_path.read_text(encoding="utf-8")
            for match in re.finditer(r"##\s+(DECISION-\d+):\s+(.+?)\n", content):
                decision_id, name = match.group(1), match.group(2).strip()
                start = match.end()
                next_section = re.search(r"\n##\s+", content[start:])
                section = content[start:start + next_section.start() if next_section else len(content)]
                status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", section)
                date_match = re.search(r"\*\*Date\*\*:\s*([\d-]+)", section)
                decision_match = re.search(r"\*\*Decision\*\*:\s*(.+?)(?=\n\*\*|\n##|\Z)", section, re.DOTALL)
                decisions.append(Decision(
                    id=decision_id, name=name, status=status_match.group(1) if status_match else "UNKNOWN",
                    date=date_match.group(1) if date_match else "",
                    summary=decision_match.group(1).strip()[:150] if decision_match else "",
                    source_file=str(file_path)))
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
        return decisions

    def _load_technology_choices(self) -> List[TechnologyChoice]:
        """Load technology decisions from CLAUDE.md."""
        choices = []
        if not self.claude_md_path.exists():
            return choices
        try:
            content = self.claude_md_path.read_text(encoding="utf-8")
            tech_section = re.search(r"##\s*Technology Decisions.*?\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
            if tech_section:
                for line in tech_section.group(1).split("\n"):
                    if "|" in line and "---" not in line and "Decision" not in line:
                        parts = [p.strip() for p in line.split("|")[1:-1]]
                        if len(parts) >= 4:
                            area = parts[0].replace("**", "")
                            if area and parts[1] and area != "Decision":
                                choices.append(TechnologyChoice(area=area, choice=parts[1], not_using=parts[2], rationale=parts[3]))
        except Exception as e:
            logger.warning(f"Failed to load technology choices: {e}")
        return choices

    def _detect_active_phase(self) -> Optional[str]:
        """Detect the currently active phase from backlog files."""
        phases_dir = self.project_root / "docs" / "backlog" / "phases"
        if not phases_dir.exists():
            return None
        for pf in sorted(phases_dir.glob("PHASE-*.md"), reverse=True):
            try:
                if "IN PROGRESS" in pf.read_text(encoding="utf-8"):
                    if m := re.search(r"PHASE-(\d+)", pf.name):
                        return f"Phase {m.group(1)}"
            except Exception as e:
                # BUG-PRELOADER-001: Log instead of silently skipping
                logger.debug(f"Failed to read phase file {pf}: {e}")
                continue
        return None

    def _count_open_gaps(self) -> int:
        """Count open gaps from GAP-INDEX.md."""
        gap_index = self.project_root / "docs" / "gaps" / "GAP-INDEX.md"
        if not gap_index.exists():
            return 0
        try:
            return len(re.findall(r"\|\s*OPEN\s*\|", gap_index.read_text(encoding="utf-8")))
        except Exception:
            return 0

    def invalidate_cache(self) -> None:
        """Invalidate the cached context."""
        self._cached_context, self._cache_time = None, None

_preloader: Optional[ContextPreloader] = None

def get_context_preloader() -> ContextPreloader:
    """Get or create global context preloader."""
    global _preloader
    if _preloader is None:
        _preloader = ContextPreloader()
    return _preloader

def preload_session_context(force_refresh: bool = False) -> ContextSummary:
    """Preload context at session start. Per P12.6."""
    return get_context_preloader().load_context(force_refresh)

def get_agent_context_prompt() -> str:
    """Get context prompt for agent injection."""
    return preload_session_context().to_agent_prompt()

__all__ = ["ContextPreloader", "get_context_preloader", "preload_session_context", "get_agent_context_prompt"]
