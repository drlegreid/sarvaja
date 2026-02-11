"""
Rules Curator Agent (ORCH-005).

Monitors rule quality, resolves conflicts, and maintains governance integrity.

Per RULE-011: Multi-Agent Governance
Per RULE-012: Deep Sleep Protocol
Per DOC-SIZE-01-v1: Models in curator_models.py, actions in curator_actions.py.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .engine import AgentInfo, AgentRole
from .curator_models import (  # noqa: F401 — re-export for backward compat
    CurationAction,
    CurationResult,
    ConflictResolution,
    IssueSeverity,
    RuleIssue,
)
from .curator_actions import CuratorActionsMixin


class RulesCuratorAgent(CuratorActionsMixin):
    """
    Rules Curator Agent for governance quality management.

    Per ORCH-005 design from RD-AGENT-ORCHESTRATION.md.

    Responsibilities:
    - Monitor rule quality (orphans, shallow rules, circular deps)
    - Detect and resolve conflicts between rules
    - Validate rule dependencies
    - Propose rule improvements
    - Maintain governance integrity

    Usage:
        curator = RulesCuratorAgent(mcp_client)
        result = await curator.analyze_quality()
        conflicts = await curator.find_conflicts()
        resolution = await curator.resolve_conflict("RULE-001", "RULE-005")
    """

    AGENT_ID = "rules-curator"
    AGENT_NAME = "Rules Curator"
    BASE_TRUST_SCORE = 0.90

    def __init__(self, mcp_client: Any = None, api_base: str = "http://localhost:8082"):
        self._mcp_client = mcp_client
        self._api_base = api_base
        self._issues: List[RuleIssue] = []
        self._resolutions: List[ConflictResolution] = []
        self._last_analysis: Optional[datetime] = None

    def get_agent_info(self) -> AgentInfo:
        """Get agent registration info."""
        return AgentInfo(
            agent_id=self.AGENT_ID,
            name=self.AGENT_NAME,
            role=AgentRole.CURATOR,
            trust_score=self.BASE_TRUST_SCORE,
        )

    async def run_full_audit(self) -> Dict[str, CurationResult]:
        """Run a complete governance audit."""
        results = {}
        results["quality"] = await self.analyze_quality()
        results["conflicts"] = await self.find_conflicts()
        results["orphans"] = await self.find_orphans()
        return results

    def get_issues(
        self,
        severity: Optional[IssueSeverity] = None,
        resolved: Optional[bool] = None,
    ) -> List[RuleIssue]:
        """Get detected issues with optional filtering."""
        issues = self._issues
        if severity is not None:
            issues = [i for i in issues if i.severity == severity]
        if resolved is not None:
            issues = [i for i in issues if i.resolved == resolved]
        return issues

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of curator state."""
        by_sev = {}
        for sev in IssueSeverity:
            by_sev[sev.value] = len([
                i for i in self._issues
                if i.severity == sev and not i.resolved
            ])

        return {
            "agent_id": self.AGENT_ID,
            "last_analysis": self._last_analysis.isoformat() if self._last_analysis else None,
            "total_issues": len(self._issues),
            "open_issues": len([i for i in self._issues if not i.resolved]),
            "by_severity": by_sev,
            "resolutions_pending": len(self._resolutions),
        }


def create_curator_agent(
    mcp_client: Any = None,
    api_base: str = "http://localhost:8082",
) -> RulesCuratorAgent:
    """Create a Rules Curator Agent instance."""
    return RulesCuratorAgent(mcp_client=mcp_client, api_base=api_base)
