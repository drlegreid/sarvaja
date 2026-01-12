"""
Workspace Launcher for Multi-Agent Orchestration.

Per AGENT-WORKSPACES.md Phase 4: Delegation Protocol.
Per RULE-011: Multi-Agent Governance Protocol.

Provides utilities to launch Claude Code in specific agent workspaces
with task context.
"""

import json
import os
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from governance.orchestrator.handoff import (
    TaskHandoff,
    get_pending_handoffs,
    read_handoff_evidence,
    AgentRole,
)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class LaunchConfig:
    """Configuration for launching an agent workspace."""
    workspace_path: Path
    agent_role: str
    task_id: Optional[str] = None
    task_context: Optional[Dict[str, Any]] = None
    background: bool = False
    profile: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["workspace_path"] = str(self.workspace_path)
        return result


@dataclass
class LaunchResult:
    """Result of launching an agent workspace."""
    success: bool
    agent_role: str
    workspace_path: str
    pid: Optional[int] = None
    error: Optional[str] = None
    launched_at: str = ""

    def __post_init__(self):
        if not self.launched_at:
            self.launched_at = datetime.now().isoformat()


# =============================================================================
# WORKSPACE DISCOVERY
# =============================================================================

def get_workspaces_dir(project_root: Path = None) -> Path:
    """Get the workspaces directory."""
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent
    return project_root / "workspaces"


def get_workspace_path(agent_role: str, project_root: Path = None) -> Path:
    """Get the workspace path for an agent role."""
    workspaces_dir = get_workspaces_dir(project_root)
    role_lower = agent_role.lower()
    return workspaces_dir / role_lower


def list_workspaces(project_root: Path = None) -> List[str]:
    """List all available workspaces."""
    workspaces_dir = get_workspaces_dir(project_root)
    if not workspaces_dir.exists():
        return []

    return [
        d.name.upper()
        for d in workspaces_dir.iterdir()
        if d.is_dir() and (d / "CLAUDE.md").exists()
    ]


def validate_workspace(agent_role: str, project_root: Path = None) -> bool:
    """
    Validate that a workspace is properly configured.

    Checks:
    - Directory exists
    - CLAUDE.md exists
    - .mcp.json exists
    - skills/ directory exists
    """
    workspace = get_workspace_path(agent_role, project_root)

    if not workspace.exists():
        return False
    if not (workspace / "CLAUDE.md").exists():
        return False
    if not (workspace / ".mcp.json").exists():
        return False
    if not (workspace / "skills").exists():
        return False

    return True


# =============================================================================
# WORKSPACE LAUNCHER
# =============================================================================

def prepare_launch_environment(
    agent_role: str,
    task_id: Optional[str] = None,
    task_context: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Prepare environment variables for workspace launch.

    Args:
        agent_role: Agent role
        task_id: Optional task ID
        task_context: Optional task context dict

    Returns:
        Dict of environment variables
    """
    env = os.environ.copy()

    # Agent identification
    env["AGENT_ROLE"] = agent_role.upper()
    env["AGENT_WORKSPACE"] = agent_role.lower()

    # Task context
    if task_id:
        env["TASK_ID"] = task_id
    if task_context:
        env["TASK_CONTEXT"] = json.dumps(task_context)

    # Ensure TypeDB/ChromaDB connection
    env.setdefault("TYPEDB_HOST", "localhost")
    env.setdefault("TYPEDB_PORT", "1729")
    env.setdefault("CHROMADB_HOST", "localhost")
    env.setdefault("CHROMADB_PORT", "8001")

    return env


def launch_workspace(
    agent_role: str,
    task_id: Optional[str] = None,
    handoff: Optional[TaskHandoff] = None,
    background: bool = False,
    project_root: Path = None,
    dry_run: bool = False
) -> LaunchResult:
    """
    Launch Claude Code in an agent workspace.

    Args:
        agent_role: Agent role (RESEARCH, CODING, CURATOR, SYNC)
        task_id: Optional task ID to work on
        handoff: Optional TaskHandoff with context
        background: Whether to run in background
        project_root: Project root directory
        dry_run: If True, don't actually launch

    Returns:
        LaunchResult with status
    """
    workspace = get_workspace_path(agent_role, project_root)

    # Validate workspace
    if not validate_workspace(agent_role, project_root):
        return LaunchResult(
            success=False,
            agent_role=agent_role,
            workspace_path=str(workspace),
            error=f"Invalid workspace: {workspace}"
        )

    # Prepare task context
    task_context = None
    if handoff:
        task_context = handoff.to_dict()
        task_id = task_id or handoff.task_id

    # Prepare environment
    env = prepare_launch_environment(agent_role, task_id, task_context)

    # Build command
    cmd = ["claude"]

    # Use profile matching workspace name
    profile = agent_role.lower()
    cmd.extend(["--profile", profile])

    if dry_run:
        return LaunchResult(
            success=True,
            agent_role=agent_role,
            workspace_path=str(workspace),
            error=f"DRY RUN: Would execute: {' '.join(cmd)} in {workspace}"
        )

    try:
        # Launch process
        if background:
            process = subprocess.Popen(
                cmd,
                cwd=workspace,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return LaunchResult(
                success=True,
                agent_role=agent_role,
                workspace_path=str(workspace),
                pid=process.pid
            )
        else:
            # Run in foreground (blocking)
            result = subprocess.run(
                cmd,
                cwd=workspace,
                env=env,
            )
            return LaunchResult(
                success=result.returncode == 0,
                agent_role=agent_role,
                workspace_path=str(workspace),
                error=None if result.returncode == 0 else f"Exit code: {result.returncode}"
            )

    except FileNotFoundError:
        return LaunchResult(
            success=False,
            agent_role=agent_role,
            workspace_path=str(workspace),
            error="claude command not found. Is Claude Code CLI installed?"
        )
    except Exception as e:
        return LaunchResult(
            success=False,
            agent_role=agent_role,
            workspace_path=str(workspace),
            error=str(e)
        )


def launch_for_handoff(handoff: TaskHandoff, **kwargs) -> LaunchResult:
    """
    Launch workspace for a specific handoff.

    Args:
        handoff: TaskHandoff to process
        **kwargs: Additional args for launch_workspace

    Returns:
        LaunchResult
    """
    return launch_workspace(
        agent_role=handoff.to_agent,
        handoff=handoff,
        **kwargs
    )


def launch_all_pending(
    for_agent: Optional[str] = None,
    background: bool = True,
    project_root: Path = None,
    dry_run: bool = False
) -> List[LaunchResult]:
    """
    Launch workspaces for all pending handoffs.

    Args:
        for_agent: Filter by target agent
        background: Run in background (default True)
        project_root: Project root directory
        dry_run: If True, don't actually launch

    Returns:
        List of LaunchResults
    """
    handoffs = get_pending_handoffs(for_agent=for_agent)
    results = []

    for handoff in handoffs:
        result = launch_for_handoff(
            handoff,
            background=background,
            project_root=project_root,
            dry_run=dry_run
        )
        results.append(result)

    return results


# =============================================================================
# SCRIPT GENERATOR
# =============================================================================

def generate_launch_script(
    agent_roles: Optional[List[str]] = None,
    output_path: Path = None
) -> str:
    """
    Generate a shell script to launch multiple agent workspaces.

    Args:
        agent_roles: List of roles to launch (default: all)
        output_path: Optional path to write script

    Returns:
        Shell script content
    """
    if agent_roles is None:
        agent_roles = ["RESEARCH", "CODING", "CURATOR", "SYNC"]

    lines = [
        "#!/bin/bash",
        "# Agent Workspace Launcher",
        "# Per AGENT-WORKSPACES.md: Multi-agent orchestration",
        "",
        "WORKSPACES=(\"research\" \"coding\" \"curator\" \"sync\")",
        "",
        "for ws in \"${WORKSPACES[@]}\"; do",
        "    if [[ -d \"workspaces/$ws\" ]]; then",
        "        echo \"Launching $ws agent...\"",
        "        cd workspaces/$ws",
        "        claude --profile $ws &",
        "        cd ../..",
        "    else",
        "        echo \"Workspace not found: workspaces/$ws\"",
        "    fi",
        "done",
        "",
        "echo \"All agents launched. Monitor via governance dashboard.\"",
    ]

    script = "\n".join(lines)

    if output_path:
        output_path.write_text(script)
        output_path.chmod(0o755)  # Make executable

    return script
