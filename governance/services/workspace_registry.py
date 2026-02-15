"""
Workspace Registry — Extensible project type + skill management.

Per ASSESS-PLATFORM-GAPS-2026-02-15: Provides a data-driven registry of
workspace types, their capabilities, MCP server bindings, and agent templates.
New project types (game dev, video, financial, ML, etc.) can be added by
registering a new WorkspaceType entry — no code changes required.

Created: 2026-02-15
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceType:
    """Definition of a workspace/project type.

    Each workspace type defines:
    - What MCP servers it needs
    - What agent templates are appropriate
    - What rules are relevant
    - What capabilities it provides
    - What slash commands are available
    """
    type_id: str                           # e.g. "gamedev", "financial", "video"
    name: str                              # e.g. "Game Development"
    description: str                       # What this workspace type is for
    icon: str = "mdi-folder"               # Vuetify icon
    color: str = "#4a90d9"                 # Theme color

    # MCP servers this workspace type needs (beyond governance defaults)
    mcp_servers: List[str] = field(default_factory=list)

    # Agent templates appropriate for this workspace
    agent_templates: List[Dict[str, Any]] = field(default_factory=list)

    # Rules relevant to this workspace type
    default_rules: List[str] = field(default_factory=list)

    # Capabilities this workspace provides
    capabilities: List[str] = field(default_factory=list)

    # Slash commands available in this workspace
    commands: List[str] = field(default_factory=list)

    # File patterns to watch (e.g. "*.gd" for Godot, "*.py" for Python)
    file_patterns: List[str] = field(default_factory=list)

    # Tags for search/filtering
    tags: List[str] = field(default_factory=list)


# ── Built-in workspace types ──────────────────────────────────────────

_GOVERNANCE_DEFAULTS = WorkspaceType(
    type_id="governance",
    name="Governance Platform",
    description="Multi-agent governance with TypeDB, rules, sessions, and tasks",
    icon="mdi-shield-check",
    color="#6366f1",
    mcp_servers=["gov-core", "gov-agents", "gov-sessions", "gov-tasks"],
    agent_templates=[
        {"value": "CODING", "title": "Coding Agent", "rules": ["TEST-GUARD-01", "TEST-COMP-02", "DOC-SIZE-01"]},
        {"value": "RESEARCH", "title": "Research Agent", "rules": ["SESSION-EVID-01", "GOV-RULE-01"]},
        {"value": "CURATOR", "title": "Curator Agent", "rules": ["GOV-RULE-01", "GOV-BICAM-01", "DOC-LINK-01"]},
        {"value": "SECURITY", "title": "Security Agent", "rules": ["SAFETY-HEALTH-01", "SAFETY-DESTR-01"]},
    ],
    default_rules=["TEST-GUARD-01", "DOC-SIZE-01", "SESSION-EVID-01"],
    capabilities=["code_generation", "test_writing", "rule_compliance", "task_management"],
    commands=["task", "rule", "health", "checkpoint", "bugfix", "report"],
    file_patterns=["*.py", "*.yaml", "*.md"],
    tags=["platform", "governance", "python", "typedb"],
)

_GAMEDEV = WorkspaceType(
    type_id="gamedev",
    name="Game Development",
    description="Game projects using Godot, Unity, or other engines",
    icon="mdi-gamepad-variant",
    color="#22c55e",
    mcp_servers=["playwright"],  # For visual testing
    agent_templates=[
        {"value": "GAMEDEV", "title": "Game Dev Agent", "rules": ["TEST-GUARD-01"]},
        {"value": "SHADER", "title": "Shader Artist", "rules": []},
        {"value": "LEVEL_DESIGN", "title": "Level Designer", "rules": []},
    ],
    default_rules=["TEST-GUARD-01"],
    capabilities=["game_scripting", "shader_authoring", "scene_design", "ui_layout", "animation"],
    commands=["task", "bug"],
    file_patterns=["*.gd", "*.tscn", "*.tres", "*.gdshader", "*.cs", "*.unity"],
    tags=["game", "godot", "unity", "creative"],
)

_VIDEO = WorkspaceType(
    type_id="video",
    name="Video Production",
    description="Video editing, transcoding, and media pipeline projects",
    icon="mdi-video",
    color="#ef4444",
    mcp_servers=[],
    agent_templates=[
        {"value": "MEDIA", "title": "Media Agent", "rules": []},
        {"value": "TRANSCODER", "title": "Transcoder Agent", "rules": []},
    ],
    default_rules=[],
    capabilities=["video_processing", "ffmpeg", "subtitle_generation", "thumbnail_extraction"],
    commands=["task"],
    file_patterns=["*.mp4", "*.mkv", "*.srt", "*.ass", "*.json"],
    tags=["video", "media", "ffmpeg", "creative"],
)

_FINANCIAL = WorkspaceType(
    type_id="financial",
    name="Financial Analysis",
    description="Financial data analysis, reporting, and compliance",
    icon="mdi-finance",
    color="#f59e0b",
    mcp_servers=[],
    agent_templates=[
        {"value": "ANALYST", "title": "Financial Analyst", "rules": ["SAFETY-DESTR-01"]},
        {"value": "COMPLIANCE", "title": "Compliance Agent", "rules": ["GOV-RULE-01"]},
    ],
    default_rules=["SAFETY-DESTR-01"],
    capabilities=["data_analysis", "report_generation", "compliance_check", "risk_assessment"],
    commands=["task", "report"],
    file_patterns=["*.py", "*.csv", "*.xlsx", "*.ipynb"],
    tags=["finance", "data", "compliance", "reporting"],
)

_ML = WorkspaceType(
    type_id="ml",
    name="Machine Learning",
    description="ML model training, evaluation, and deployment",
    icon="mdi-brain",
    color="#8b5cf6",
    mcp_servers=[],
    agent_templates=[
        {"value": "ML_ENGINEER", "title": "ML Engineer", "rules": ["TEST-GUARD-01"]},
        {"value": "DATA_SCIENTIST", "title": "Data Scientist", "rules": []},
    ],
    default_rules=["TEST-GUARD-01"],
    capabilities=["model_training", "data_preprocessing", "evaluation", "deployment"],
    commands=["task", "bug"],
    file_patterns=["*.py", "*.ipynb", "*.yaml", "*.json", "*.onnx"],
    tags=["ml", "ai", "data-science", "python"],
)

_GENERIC = WorkspaceType(
    type_id="generic",
    name="Generic Project",
    description="General-purpose project without specialized tooling",
    icon="mdi-folder-outline",
    color="#64748b",
    mcp_servers=[],
    agent_templates=[
        {"value": "CUSTOM", "title": "Custom Agent", "rules": []},
    ],
    default_rules=[],
    capabilities=["code_generation", "file_operations"],
    commands=["task", "bug"],
    file_patterns=["*"],
    tags=["generic"],
)


# ── Registry ──────────────────────────────────────────────────────────

_registry: Dict[str, WorkspaceType] = {}


def _init_registry() -> None:
    """Initialize with built-in workspace types."""
    for wt in [_GOVERNANCE_DEFAULTS, _GAMEDEV, _VIDEO, _FINANCIAL, _ML, _GENERIC]:
        _registry[wt.type_id] = wt


def register_workspace_type(workspace_type: WorkspaceType) -> None:
    """Register a new workspace type dynamically.

    Can be called at startup from config files or via API.
    """
    _registry[workspace_type.type_id] = workspace_type
    logger.info(f"Registered workspace type: {workspace_type.type_id}")


def get_workspace_type(type_id: str) -> Optional[WorkspaceType]:
    """Get a workspace type by ID."""
    if not _registry:
        _init_registry()
    return _registry.get(type_id)


def list_workspace_types() -> List[WorkspaceType]:
    """List all registered workspace types."""
    if not _registry:
        _init_registry()
    return sorted(_registry.values(), key=lambda w: w.name)


def get_workspace_type_ids() -> List[str]:
    """Get all registered type IDs for dropdown menus."""
    if not _registry:
        _init_registry()
    return sorted(_registry.keys())


def get_agent_templates_for_type(type_id: str) -> List[Dict[str, Any]]:
    """Get agent templates appropriate for a workspace type."""
    wt = get_workspace_type(type_id)
    if wt:
        return wt.agent_templates
    return get_workspace_type("generic").agent_templates


def detect_project_type(path: str) -> str:
    """Auto-detect project type from filesystem indicators.

    Checks for characteristic files/directories to infer project type.
    Returns type_id string.
    """
    from pathlib import Path
    p = Path(path)
    if not p.is_dir():
        return "generic"

    # Check for Godot project
    if (p / "project.godot").exists() or any(p.glob("**/*.gd")):
        return "gamedev"

    # Check for ML project
    if any(p.glob("**/*.ipynb")) or (p / "model").is_dir():
        return "ml"

    # Check for video project
    if any(p.glob("**/*.mp4")) or any(p.glob("**/*.mkv")):
        return "video"

    # Check for Python governance/platform
    if (p / "governance").is_dir() or (p / "CLAUDE.md").exists():
        return "governance"

    # Check for financial
    if any(p.glob("**/*.xlsx")) or any(p.glob("**/*.csv")):
        return "financial"

    return "generic"


def workspace_type_to_dict(wt: WorkspaceType) -> Dict[str, Any]:
    """Convert WorkspaceType to API-friendly dict."""
    return {
        "type_id": wt.type_id,
        "name": wt.name,
        "description": wt.description,
        "icon": wt.icon,
        "color": wt.color,
        "mcp_servers": wt.mcp_servers,
        "agent_templates": wt.agent_templates,
        "default_rules": wt.default_rules,
        "capabilities": wt.capabilities,
        "commands": wt.commands,
        "file_patterns": wt.file_patterns,
        "tags": wt.tags,
    }
