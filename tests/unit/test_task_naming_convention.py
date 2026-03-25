"""Tests for FIX-NOM-001 + FIX-NOM-002: Task ID naming convention.

FIX-NOM-001: Convention is {PROJECT}-{TYPE}-{SEQ} (e.g., SARVAJA-BUG-001)
FIX-NOM-002: Auto-prefix task_id with project name when workspace/project is set.

When no project is available, falls back to existing {TYPE}-{SEQ} pattern.
"""

import pytest
from unittest.mock import patch, MagicMock


# ── Project prefix derivation ────────────────────────────────────────


class TestDeriveProjectPrefix:
    """Test project_id → prefix derivation."""

    def test_sarvaja_platform(self):
        from governance.services.task_id_gen import derive_project_prefix
        assert derive_project_prefix("sarvaja-platform") == "SARVAJA"

    def test_proj_gamedev(self):
        from governance.services.task_id_gen import derive_project_prefix
        assert derive_project_prefix("PROJ-GAMEDEV") == "GAMEDEV"

    def test_jobhunt_2026(self):
        from governance.services.task_id_gen import derive_project_prefix
        assert derive_project_prefix("jobhunt-2026") == "JOBHUNT"

    def test_simple_name(self):
        from governance.services.task_id_gen import derive_project_prefix
        assert derive_project_prefix("myproject") == "MYPROJECT"

    def test_empty_string(self):
        from governance.services.task_id_gen import derive_project_prefix
        assert derive_project_prefix("") == ""

    def test_none_returns_empty(self):
        from governance.services.task_id_gen import derive_project_prefix
        assert derive_project_prefix(None) == ""


# ── Project-prefixed ID generation ───────────────────────────────────


class TestGenerateTaskIdWithProject:
    """Test generate_task_id with project prefix."""

    def test_with_project_prefix(self):
        from governance.services.task_id_gen import generate_task_id
        tid = generate_task_id("bug", client=None, project_prefix="SARVAJA")
        assert tid.startswith("SARVAJA-BUG-")
        assert len(tid.split("-")) == 3

    def test_without_project_prefix_unchanged(self):
        """Backward compat: no project prefix = old pattern."""
        from governance.services.task_id_gen import generate_task_id
        tid = generate_task_id("bug", client=None)
        assert tid.startswith("BUG-")

    def test_project_prefix_with_feature(self):
        from governance.services.task_id_gen import generate_task_id
        tid = generate_task_id("feature", client=None, project_prefix="GAMEDEV")
        assert tid.startswith("GAMEDEV-FEAT-")

    def test_project_prefix_with_spec(self):
        """spec type generates SARVAJA-SPEC-NNN (EPIC-TASK-TAXONOMY-V2)."""
        from governance.services.task_id_gen import generate_task_id
        tid = generate_task_id("spec", client=None, project_prefix="SARVAJA")
        assert tid.startswith("SARVAJA-SPEC-")

    def test_project_prefix_sequence_increments(self):
        """Sequence should increment across calls."""
        from governance.services.task_id_gen import generate_task_id, _counters
        # Reset counter for this test
        _counters.pop("TESTPROJ-BUG", None)
        tid1 = generate_task_id("bug", client=None, project_prefix="TESTPROJ")
        tid2 = generate_task_id("bug", client=None, project_prefix="TESTPROJ")
        seq1 = int(tid1.split("-")[-1])
        seq2 = int(tid2.split("-")[-1])
        assert seq2 == seq1 + 1

    def test_empty_project_prefix_falls_back(self):
        from governance.services.task_id_gen import generate_task_id
        tid = generate_task_id("bug", client=None, project_prefix="")
        assert tid.startswith("BUG-")


# ── Workspace-to-project resolution ─────────────────────────────────


class TestResolveProjectFromWorkspace:
    """Test resolving project prefix from workspace_id."""

    def test_resolve_known_workspace(self):
        from governance.services.task_id_gen import resolve_project_prefix
        ws_store = {
            "WS-AAA": {"project_id": "sarvaja-platform"},
            "WS-BBB": {"project_id": "PROJ-GAMEDEV"},
        }
        assert resolve_project_prefix("WS-AAA", ws_store) == "SARVAJA"
        assert resolve_project_prefix("WS-BBB", ws_store) == "GAMEDEV"

    def test_resolve_unknown_workspace(self):
        from governance.services.task_id_gen import resolve_project_prefix
        assert resolve_project_prefix("WS-UNKNOWN", {}) == ""

    def test_resolve_none_workspace(self):
        from governance.services.task_id_gen import resolve_project_prefix
        assert resolve_project_prefix(None, {}) == ""

    def test_resolve_workspace_without_project(self):
        from governance.services.task_id_gen import resolve_project_prefix
        ws_store = {"WS-AAA": {"name": "test"}}  # no project_id
        assert resolve_project_prefix("WS-AAA", ws_store) == ""


# ── Extract sequence with project prefix ─────────────────────────────


class TestExtractSequenceWithProject:
    """Test _extract_sequence handles project-prefixed IDs."""

    def test_standard_pattern(self):
        from governance.services.task_id_gen import _extract_sequence
        assert _extract_sequence("BUG-042", "BUG") == 42

    def test_project_prefixed_pattern(self):
        from governance.services.task_id_gen import _extract_sequence
        assert _extract_sequence("SARVAJA-BUG-042", "SARVAJA-BUG") == 42

    def test_no_match(self):
        from governance.services.task_id_gen import _extract_sequence
        assert _extract_sequence("FEAT-001", "BUG") == 0
