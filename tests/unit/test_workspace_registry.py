"""Tests for workspace registry — extensible project type management.

Per ASSESS-PLATFORM-GAPS-2026-02-15 Fix E: Validates WorkspaceType dataclass,
registry CRUD, auto-detection, agent template retrieval, and API integration.
"""
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest


# ── WorkspaceType dataclass ──────────────────────────────────────────


def test_workspace_type_defaults():
    """WorkspaceType has sensible defaults for optional fields."""
    from governance.services.workspace_registry import WorkspaceType
    wt = WorkspaceType(type_id="test", name="Test", description="desc")
    assert wt.icon == "mdi-folder"
    assert wt.color == "#4a90d9"
    assert wt.mcp_servers == []
    assert wt.agent_templates == []
    assert wt.capabilities == []
    assert wt.tags == []


def test_workspace_type_full_init():
    """WorkspaceType can be initialized with all fields."""
    from governance.services.workspace_registry import WorkspaceType
    wt = WorkspaceType(
        type_id="custom",
        name="Custom",
        description="Custom workspace",
        icon="mdi-star",
        color="#ff0000",
        mcp_servers=["server1"],
        agent_templates=[{"value": "A", "title": "Agent A", "rules": []}],
        default_rules=["RULE-001"],
        capabilities=["cap1", "cap2"],
        commands=["cmd1"],
        file_patterns=["*.py"],
        tags=["tag1"],
    )
    assert wt.type_id == "custom"
    assert len(wt.mcp_servers) == 1
    assert wt.agent_templates[0]["value"] == "A"
    assert wt.capabilities == ["cap1", "cap2"]


# ── Registry functions ───────────────────────────────────────────────


def test_list_workspace_types_returns_all_builtins():
    """list_workspace_types returns all 6 built-in types."""
    from governance.services.workspace_registry import list_workspace_types
    types = list_workspace_types()
    type_ids = {wt.type_id for wt in types}
    assert "governance" in type_ids
    assert "gamedev" in type_ids
    assert "video" in type_ids
    assert "financial" in type_ids
    assert "ml" in type_ids
    assert "generic" in type_ids
    assert len(types) >= 6


def test_get_workspace_type_returns_correct_type():
    """get_workspace_type returns specific type by ID."""
    from governance.services.workspace_registry import get_workspace_type
    wt = get_workspace_type("gamedev")
    assert wt is not None
    assert wt.name == "Game Development"
    assert "*.gd" in wt.file_patterns
    assert "game" in wt.tags


def test_get_workspace_type_unknown_returns_none():
    """get_workspace_type returns None for unknown type."""
    from governance.services.workspace_registry import get_workspace_type
    assert get_workspace_type("nonexistent") is None


def test_get_workspace_type_ids_sorted():
    """get_workspace_type_ids returns sorted list."""
    from governance.services.workspace_registry import get_workspace_type_ids
    ids = get_workspace_type_ids()
    assert ids == sorted(ids)
    assert "generic" in ids


def test_register_workspace_type_adds_new():
    """register_workspace_type adds a new type to registry."""
    from governance.services.workspace_registry import (
        WorkspaceType, register_workspace_type, get_workspace_type, _registry,
    )
    custom = WorkspaceType(
        type_id="iot",
        name="IoT Platform",
        description="IoT device management",
        tags=["iot", "embedded"],
    )
    register_workspace_type(custom)
    assert get_workspace_type("iot") is not None
    assert get_workspace_type("iot").name == "IoT Platform"
    # Cleanup
    _registry.pop("iot", None)


def test_register_workspace_type_overwrites_existing():
    """register_workspace_type overwrites existing type with same ID."""
    from governance.services.workspace_registry import (
        WorkspaceType, register_workspace_type, get_workspace_type, _registry,
    )
    original_name = get_workspace_type("generic").name
    updated = WorkspaceType(
        type_id="generic",
        name="Updated Generic",
        description="Updated",
    )
    register_workspace_type(updated)
    assert get_workspace_type("generic").name == "Updated Generic"
    # Restore
    _registry["generic"] = WorkspaceType(
        type_id="generic",
        name=original_name,
        description="General-purpose project without specialized tooling",
        icon="mdi-folder-outline",
        color="#64748b",
        capabilities=["code_generation", "file_operations"],
        commands=["task", "bug"],
        file_patterns=["*"],
        tags=["generic"],
        agent_templates=[{"value": "CUSTOM", "title": "Custom Agent", "rules": []}],
    )


# ── Agent templates ──────────────────────────────────────────────────


def test_get_agent_templates_for_governance():
    """Governance workspace has 4 agent templates."""
    from governance.services.workspace_registry import get_agent_templates_for_type
    templates = get_agent_templates_for_type("governance")
    assert len(templates) == 4
    values = [t["value"] for t in templates]
    assert "CODING" in values
    assert "RESEARCH" in values


def test_get_agent_templates_for_gamedev():
    """Game dev workspace has its own templates."""
    from governance.services.workspace_registry import get_agent_templates_for_type
    templates = get_agent_templates_for_type("gamedev")
    assert len(templates) == 3
    values = [t["value"] for t in templates]
    assert "GAMEDEV" in values
    assert "SHADER" in values


def test_get_agent_templates_unknown_falls_back_to_generic():
    """Unknown type falls back to generic templates."""
    from governance.services.workspace_registry import get_agent_templates_for_type
    templates = get_agent_templates_for_type("nonexistent")
    values = [t["value"] for t in templates]
    assert "CUSTOM" in values


# ── Auto-detection ───────────────────────────────────────────────────


def test_detect_project_type_godot():
    """detect_project_type identifies Godot projects."""
    from governance.services.workspace_registry import detect_project_type
    with patch("pathlib.Path.is_dir", return_value=True):
        with patch("pathlib.Path.exists", return_value=True):  # project.godot
            result = detect_project_type("/some/game")
    assert result == "gamedev"


def test_detect_project_type_ml_notebook():
    """detect_project_type identifies ML projects from notebooks."""
    from governance.services.workspace_registry import detect_project_type
    with patch("pathlib.Path.is_dir", return_value=True):
        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.glob") as mock_glob:
                def glob_side_effect(pattern):
                    if "*.ipynb" in pattern:
                        return [Path("notebook.ipynb")]
                    if "*.gd" in pattern:
                        return []
                    return []
                mock_glob.side_effect = glob_side_effect
                result = detect_project_type("/some/ml-project")
    assert result == "ml"


def test_detect_project_type_governance():
    """detect_project_type identifies governance platform via CLAUDE.md."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        # Create governance/ subdir — the detection marker
        os.makedirs(os.path.join(tmp, "governance"))
        from governance.services.workspace_registry import detect_project_type
        result = detect_project_type(tmp)
    assert result == "governance"


def test_detect_project_type_nondir_returns_generic():
    """detect_project_type returns generic for non-directory paths."""
    from governance.services.workspace_registry import detect_project_type
    with patch("pathlib.Path.is_dir", return_value=False):
        result = detect_project_type("/nonexistent")
    assert result == "generic"


# ── workspace_type_to_dict ───────────────────────────────────────────


def test_workspace_type_to_dict_all_keys():
    """workspace_type_to_dict includes all fields."""
    from governance.services.workspace_registry import (
        WorkspaceType, workspace_type_to_dict,
    )
    wt = WorkspaceType(type_id="t", name="N", description="D")
    d = workspace_type_to_dict(wt)
    expected_keys = {
        "type_id", "name", "description", "icon", "color",
        "mcp_servers", "agent_templates", "default_rules",
        "capabilities", "commands", "file_patterns", "tags",
    }
    assert set(d.keys()) == expected_keys
    assert d["type_id"] == "t"


# ── ProjectCreate model with project_type ────────────────────────────


def test_project_create_model_has_project_type():
    """ProjectCreate model includes project_type field with default."""
    from governance.models import ProjectCreate
    proj = ProjectCreate(name="Test")
    assert proj.project_type == "generic"


def test_project_create_model_custom_type():
    """ProjectCreate accepts custom project_type."""
    from governance.models import ProjectCreate
    proj = ProjectCreate(name="Game", project_type="gamedev")
    assert proj.project_type == "gamedev"


def test_project_response_model_has_project_type():
    """ProjectResponse model includes project_type field."""
    from governance.models import ProjectResponse
    resp = ProjectResponse(project_id="PROJ-1", name="Test")
    assert resp.project_type == "generic"


# ── Project service with project_type ────────────────────────────────


def test_create_project_stores_project_type():
    """create_project stores project_type in memory fallback."""
    from governance.services.projects import create_project, _projects_store
    with patch("governance.services.projects._get_client", return_value=None):
        result = create_project(
            project_id="PROJ-TEST-TYPE",
            name="Test Type",
            project_type="ml",
        )
    assert result["project_type"] == "ml"
    _projects_store.pop("PROJ-TEST-TYPE", None)


def test_create_project_default_type_is_generic():
    """create_project defaults to generic project_type."""
    from governance.services.projects import create_project, _projects_store
    with patch("governance.services.projects._get_client", return_value=None):
        result = create_project(
            project_id="PROJ-DEFAULT-TYPE",
            name="Default",
        )
    assert result["project_type"] == "generic"
    _projects_store.pop("PROJ-DEFAULT-TYPE", None)


# ── API routes ───────────────────────────────────────────────────────


def test_list_workspace_types_endpoint():
    """GET /workspace-types returns all types."""
    from governance.routes.projects.crud import list_workspace_types_endpoint
    result = list_workspace_types_endpoint()
    assert "items" in result
    type_ids = [wt["type_id"] for wt in result["items"]]
    assert "governance" in type_ids
    assert "gamedev" in type_ids
    assert len(type_ids) >= 6


def test_get_workspace_type_endpoint_found():
    """GET /workspace-types/{id} returns specific type."""
    from governance.routes.projects.crud import get_workspace_type_endpoint
    result = get_workspace_type_endpoint("gamedev")
    assert result["type_id"] == "gamedev"
    assert result["name"] == "Game Development"


def test_get_workspace_type_endpoint_not_found():
    """GET /workspace-types/{id} raises 404 for unknown type."""
    from governance.routes.projects.crud import get_workspace_type_endpoint
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        get_workspace_type_endpoint("nonexistent")
    assert exc_info.value.status_code == 404


def test_get_agent_templates_endpoint():
    """GET /workspace-types/{id}/agent-templates returns templates."""
    from governance.routes.projects.crud import get_agent_templates_endpoint
    result = get_agent_templates_endpoint("governance")
    assert result["type_id"] == "governance"
    assert len(result["templates"]) == 4


def test_detect_workspace_type_endpoint():
    """POST /workspace-types/detect returns auto-detected type."""
    from governance.routes.projects.crud import detect_workspace_type
    with patch(
        "governance.routes.projects.crud.detect_project_type",
        return_value="gamedev",
    ):
        result = detect_workspace_type(path="/some/game")
    assert result["detected_type"] == "gamedev"
    assert result["workspace"]["type_id"] == "gamedev"


# ── Agent registration templates ─────────────────────────────────────


def test_agent_registration_templates_from_registry():
    """Agent registration AGENT_TYPE_TEMPLATES comes from workspace registry."""
    from agent.governance_ui.views.agents.registration import AGENT_TYPE_TEMPLATES
    assert len(AGENT_TYPE_TEMPLATES) >= 4
    values = [t["value"] for t in AGENT_TYPE_TEMPLATES]
    assert "CODING" in values
    assert "RESEARCH" in values


# ── Built-in workspace properties ────────────────────────────────────


def test_governance_workspace_has_mcp_servers():
    """Governance workspace requires 4 MCP servers."""
    from governance.services.workspace_registry import get_workspace_type
    wt = get_workspace_type("governance")
    assert len(wt.mcp_servers) == 4
    assert "gov-core" in wt.mcp_servers


def test_video_workspace_capabilities():
    """Video workspace has media-specific capabilities."""
    from governance.services.workspace_registry import get_workspace_type
    wt = get_workspace_type("video")
    assert "video_processing" in wt.capabilities
    assert "ffmpeg" in wt.capabilities


def test_financial_workspace_default_rules():
    """Financial workspace has safety rules by default."""
    from governance.services.workspace_registry import get_workspace_type
    wt = get_workspace_type("financial")
    assert "SAFETY-DESTR-01" in wt.default_rules


def test_ml_workspace_file_patterns():
    """ML workspace watches for notebooks and model files."""
    from governance.services.workspace_registry import get_workspace_type
    wt = get_workspace_type("ml")
    assert "*.ipynb" in wt.file_patterns
    assert "*.onnx" in wt.file_patterns


def test_generic_workspace_is_catch_all():
    """Generic workspace accepts all file patterns."""
    from governance.services.workspace_registry import get_workspace_type
    wt = get_workspace_type("generic")
    assert "*" in wt.file_patterns
    assert len(wt.agent_templates) == 1
    assert wt.agent_templates[0]["value"] == "CUSTOM"
