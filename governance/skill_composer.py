"""
Skill Composition Engine (RD-WORKSPACE Phase 3).

Per AGENT-WORKSPACES.md: Composable skills and wisdom for agent workspaces.
Per RULE-011: Multi-Agent Governance Protocol.

This module helps agent workspaces:
1. Load rules relevant to their role and skills
2. Filter wisdom (rules) by tags
3. Compose skill sets for task delegation
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Skill:
    """Represents a skill definition from workspace skills/ directory."""
    skill_id: str
    name: str
    tags: List[str]
    requires: List[str]  # Required tools
    procedure: str
    evidence_output: str = ""

    @classmethod
    def from_markdown(cls, path: Path) -> Optional["Skill"]:
        """Parse skill from markdown file."""
        if not path.exists():
            return None

        content = path.read_text()
        lines = content.split("\n")

        skill_id = ""
        name = ""
        tags = []
        requires = []
        procedure_lines = []
        evidence_lines = []
        in_procedure = False
        in_evidence = False

        for line in lines:
            if line.startswith("**ID:**"):
                skill_id = line.split("**ID:**")[1].strip()
            elif line.startswith("**Tags:**"):
                tags_str = line.split("**Tags:**")[1].strip()
                tags = [t.strip() for t in tags_str.split(",")]
            elif line.startswith("**Requires:**"):
                req_str = line.split("**Requires:**")[1].strip()
                requires = [r.strip() for r in req_str.split(",")]
            elif line.startswith("# Skill:"):
                name = line.replace("# Skill:", "").strip()
            elif line.startswith("## Procedure"):
                in_procedure = True
                in_evidence = False
            elif line.startswith("## Evidence Output"):
                in_procedure = False
                in_evidence = True
            elif line.startswith("## "):
                in_procedure = False
                in_evidence = False
            elif in_procedure:
                procedure_lines.append(line)
            elif in_evidence:
                evidence_lines.append(line)

        if not skill_id:
            return None

        return cls(
            skill_id=skill_id,
            name=name,
            tags=tags,
            requires=requires,
            procedure="\n".join(procedure_lines).strip(),
            evidence_output="\n".join(evidence_lines).strip()
        )


@dataclass
class AgentWisdom:
    """Wisdom (filtered rules) for an agent workspace."""
    agent_role: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    rule_filter: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "agent_role": self.agent_role,
            "rules_count": len(self.rules),
            "skills_count": len(self.skills),
            "rule_filter": self.rule_filter,
            "rules": self.rules,
            "skills": [asdict(s) for s in self.skills]
        }


# =============================================================================
# ROLE-TAG MAPPING
# =============================================================================

# Default tags for each agent role (from AGENT-WORKSPACES.md)
ROLE_TAG_MAP: Dict[str, List[str]] = {
    "RESEARCH": ["research", "analysis", "exploration", "documentation"],
    "CODING": ["coding", "testing", "architecture", "implementation"],
    "CURATOR": ["governance", "quality", "validation", "review"],
    "SYNC": ["sync", "deployment", "backup", "git"],
}

# Priority filter per role
ROLE_PRIORITY_FILTER: Dict[str, List[str]] = {
    "RESEARCH": ["CRITICAL", "HIGH"],
    "CODING": ["CRITICAL", "HIGH", "MEDIUM"],
    "CURATOR": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    "SYNC": ["CRITICAL", "HIGH"],
}


# =============================================================================
# SKILL COMPOSITION
# =============================================================================

def load_workspace_skills(workspace_path: Path) -> List[Skill]:
    """
    Load all skill definitions from a workspace's skills/ directory.

    Args:
        workspace_path: Path to workspace (e.g., workspaces/research)

    Returns:
        List of Skill objects
    """
    skills_dir = workspace_path / "skills"
    if not skills_dir.exists():
        return []

    skills = []
    for skill_file in skills_dir.glob("*.md"):
        skill = Skill.from_markdown(skill_file)
        if skill:
            skills.append(skill)

    return skills


def filter_rules_by_tags(
    rules: List[Dict[str, Any]],
    tags: Set[str]
) -> List[Dict[str, Any]]:
    """
    Filter rules that have any matching tags.

    Args:
        rules: List of rule dicts
        tags: Set of tags to match

    Returns:
        Filtered list of rules
    """
    result = []
    for rule in rules:
        rule_tags_str = rule.get("tags", "") or ""
        rule_tags = {t.strip().lower() for t in rule_tags_str.split(",") if t.strip()}

        if tags.intersection(rule_tags):
            result.append(rule)
        elif not rule_tags:
            # Rules without tags apply to all roles
            result.append(rule)

    return result


def filter_rules_by_role(
    rules: List[Dict[str, Any]],
    agent_role: str
) -> List[Dict[str, Any]]:
    """
    Filter rules applicable to an agent role.

    Args:
        rules: List of rule dicts
        agent_role: Agent role (RESEARCH, CODING, CURATOR, SYNC)

    Returns:
        Filtered list of rules
    """
    result = []
    role_upper = agent_role.upper()

    for rule in rules:
        roles_str = rule.get("applicable_roles", "") or ""
        roles = {r.strip().upper() for r in roles_str.split(",") if r.strip()}

        if role_upper in roles:
            result.append(rule)
        elif not roles:
            # Rules without roles apply to all agents
            result.append(rule)

    return result


def compose_agent_wisdom(
    agent_role: str,
    all_rules: List[Dict[str, Any]],
    workspace_path: Optional[Path] = None
) -> AgentWisdom:
    """
    Compose wisdom (rules + skills) for an agent workspace.

    Args:
        agent_role: Agent role (RESEARCH, CODING, CURATOR, SYNC)
        all_rules: All available rules from TypeDB
        workspace_path: Optional path to workspace for skills

    Returns:
        AgentWisdom with filtered rules and loaded skills
    """
    role_upper = agent_role.upper()

    # Get default tags for role
    default_tags = set(ROLE_TAG_MAP.get(role_upper, []))

    # Get priority filter for role
    priority_filter = ROLE_PRIORITY_FILTER.get(role_upper, ["CRITICAL", "HIGH"])

    # Filter rules by tags
    tagged_rules = filter_rules_by_tags(all_rules, default_tags)

    # Filter by role
    role_rules = filter_rules_by_role(tagged_rules, role_upper)

    # Filter by priority
    filtered_rules = [
        r for r in role_rules
        if r.get("priority", "MEDIUM") in priority_filter
    ]

    # Load skills from workspace
    skills = []
    if workspace_path and workspace_path.exists():
        skills = load_workspace_skills(workspace_path)

    return AgentWisdom(
        agent_role=role_upper,
        rules=filtered_rules,
        skills=skills,
        rule_filter={
            "tags": list(default_tags),
            "priorities": priority_filter,
            "role": role_upper
        }
    )


def get_agent_wisdom_json(
    agent_role: str,
    all_rules: List[Dict[str, Any]],
    workspace_path: Optional[Path] = None
) -> str:
    """
    Get agent wisdom as JSON string.

    Args:
        agent_role: Agent role
        all_rules: All available rules
        workspace_path: Optional workspace path

    Returns:
        JSON string with wisdom data
    """
    wisdom = compose_agent_wisdom(agent_role, all_rules, workspace_path)
    return json.dumps(wisdom.to_dict(), indent=2)


# =============================================================================
# WORKSPACE HELPER
# =============================================================================

def get_workspace_path(agent_role: str, project_root: Path = None) -> Path:
    """
    Get the workspace path for an agent role.

    Args:
        agent_role: Agent role (RESEARCH, CODING, CURATOR, SYNC)
        project_root: Optional project root path

    Returns:
        Path to workspace directory
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent

    role_lower = agent_role.lower()
    return project_root / "workspaces" / role_lower
