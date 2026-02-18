"""Deep scan batch 155: Evidence scanner + session repair.

Batch 155 findings: 10 total, 1 confirmed fix, 9 rejected.
- BUG-EVIDENCE-001: extract_rule_refs .upper() breaks version suffix -v1 → -V1
"""
import pytest
import re
from pathlib import Path
from datetime import datetime


# ── Rule ref normalization defense ──────────────


class TestRuleRefNormalizationDefense:
    """Verify rule ref extraction preserves lowercase v in version suffix."""

    def test_semantic_rule_preserves_lowercase_v(self):
        """SESSION-EVID-01-v1 stays lowercase v, not V1."""
        from governance.evidence_scanner.extractors import extract_rule_refs
        refs = extract_rule_refs("Per SESSION-EVID-01-v1")
        assert "SESSION-EVID-01-v1" in refs

    def test_uppercase_v_normalized_to_lowercase(self):
        """SESSION-EVID-01-V1 normalized to lowercase v1."""
        from governance.evidence_scanner.extractors import extract_rule_refs
        refs = extract_rule_refs("Per SESSION-EVID-01-V1")
        assert "SESSION-EVID-01-v1" in refs

    def test_all_lowercase_normalized(self):
        """session-evid-01-v1 normalized to upper prefix, lower v."""
        from governance.evidence_scanner.extractors import extract_rule_refs
        refs = extract_rule_refs("Per session-evid-01-v1")
        assert "SESSION-EVID-01-v1" in refs

    def test_legacy_rule_id_uppercased(self):
        """RULE-001 is fully uppercased (no version suffix)."""
        from governance.evidence_scanner.extractors import extract_rule_refs
        refs = extract_rule_refs("Legacy RULE-042 reference")
        assert "RULE-042" in refs

    def test_normalize_helper_exists(self):
        """_normalize_rule_id helper function exists."""
        from governance.evidence_scanner.extractors import _normalize_rule_id
        assert callable(_normalize_rule_id)

    def test_normalize_preserves_v_suffix(self):
        """_normalize_rule_id preserves lowercase -v in version."""
        from governance.evidence_scanner.extractors import _normalize_rule_id
        assert _normalize_rule_id("SESSION-EVID-01-v1") == "SESSION-EVID-01-v1"
        assert _normalize_rule_id("session-evid-01-v1") == "SESSION-EVID-01-v1"
        assert _normalize_rule_id("session-evid-01-V1") == "SESSION-EVID-01-v1"

    def test_normalize_no_version_suffix(self):
        """_normalize_rule_id uppercases fully when no version suffix."""
        from governance.evidence_scanner.extractors import _normalize_rule_id
        assert _normalize_rule_id("RULE-001") == "RULE-001"
        assert _normalize_rule_id("rule-001") == "RULE-001"


# ── Task and gap refs still uppercase defense ──────────────


class TestTaskGapRefsUppercaseDefense:
    """Verify task and gap refs still use blanket uppercase (no v suffix)."""

    def test_task_refs_uppercase(self):
        """Task refs like FH-001 are fully uppercased."""
        from governance.evidence_scanner.extractors import extract_task_refs
        refs = extract_task_refs("Task fh-001 completed")
        assert "FH-001" in refs

    def test_gap_refs_uppercase(self):
        """Gap refs like GAP-UI-001 are fully uppercased."""
        from governance.evidence_scanner.extractors import extract_gap_refs
        refs = extract_gap_refs("See gap-ui-001 for details")
        assert "GAP-UI-001" in refs


# ── Session repair guard condition defense ──────────────


class TestSessionRepairGuardDefense:
    """Verify build_repair_plan guard conditions are correct."""

    def test_timestamp_fix_skips_duration_check(self):
        """When timestamps are regenerated, duration check is skipped (correct)."""
        from governance.services.session_repair import build_repair_plan
        sessions = [{
            "session_id": "SESSION-2026-01-15-TEST",
            "description": "Backfilled from evidence file",
            "start_time": "2026-01-15T09:00:00",
            "end_time": "2026-01-20T09:00:00",  # 5 days — unrealistic
            "agent_id": "code-agent",
        }]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        fixes = plan[0]["fixes"]
        # Timestamp fix applied (backfilled session)
        assert "timestamp" in fixes
        # Duration fix NOT applied (timestamp regeneration handles it)
        assert "duration" not in fixes

    def test_negative_duration_gets_timestamp_fix(self):
        """Negative duration triggers timestamp fix (swap or regenerate)."""
        from governance.services.session_repair import build_repair_plan
        sessions = [{
            "session_id": "SESSION-2026-02-15-NEGATIVE",
            "start_time": "2026-02-15T14:00:00",
            "end_time": "2026-02-15T10:00:00",  # End before start
            "agent_id": "code-agent",
        }]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert "timestamp" in plan[0]["fixes"]

    def test_missing_agent_gets_fix(self):
        """Missing agent_id gets code-agent default."""
        from governance.services.session_repair import build_repair_plan
        sessions = [{
            "session_id": "SESSION-2026-02-15-NOAGENT",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T14:00:00",
            "agent_id": "",
        }]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert plan[0]["fixes"]["agent_id"] == "code-agent"


# ── Evidence scanner workspace root defense ──────────────


class TestEvidenceScannerWorkspaceDefense:
    """Verify WORKSPACE_ROOT and EVIDENCE_DIR resolve correctly."""

    def test_workspace_root_is_project_root(self):
        """WORKSPACE_ROOT resolves to project root (contains CLAUDE.md)."""
        from governance.evidence_scanner.extractors import WORKSPACE_ROOT
        assert Path(WORKSPACE_ROOT, "CLAUDE.md").exists()

    def test_evidence_dir_under_workspace(self):
        """EVIDENCE_DIR is workspace_root/evidence/."""
        from governance.evidence_scanner.extractors import EVIDENCE_DIR, WORKSPACE_ROOT
        assert EVIDENCE_DIR == str(Path(WORKSPACE_ROOT) / "evidence")


# ── Backfill detection patterns defense ──────────────


class TestBackfillDetectionPatternsDefense:
    """Verify is_backfilled_session covers both indicators."""

    def test_backfilled_description_detected(self):
        """Description with 'Backfilled from evidence' → backfilled."""
        from governance.services.session_repair import is_backfilled_session
        assert is_backfilled_session({"description": "Backfilled from evidence file"})

    def test_test_agent_detected(self):
        """Agent ending in '-test' → backfilled."""
        from governance.services.session_repair import is_backfilled_session
        assert is_backfilled_session({"agent_id": "code-agent-test"})

    def test_real_session_not_detected(self):
        """Normal session → not backfilled."""
        from governance.services.session_repair import is_backfilled_session
        assert not is_backfilled_session({
            "description": "Normal session",
            "agent_id": "code-agent",
        })

    def test_case_insensitive_description(self):
        """Backfill detection is case-insensitive."""
        from governance.services.session_repair import is_backfilled_session
        assert is_backfilled_session({"description": "BACKFILLED FROM EVIDENCE FILE"})
