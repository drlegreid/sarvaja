"""
Unit tests for Workflow Checker Module.

Batch 157b: Tests for .claude/hooks/checkers/workflow_checker.py
- ValidationResult / GapTransition dataclasses
- VALID_TRANSITIONS / RESOLUTION_RULES constants
- validate_gap_transition
- _get_gap_category
- validate_session_start / validate_session_end
- check_workflow_compliance
- format_workflow_for_healthcheck / get_workflow_status
"""

import importlib.util
from datetime import datetime
from pathlib import Path

import pytest


def _load_workflow_checker():
    mod_path = (
        Path(__file__).parent.parent.parent
        / ".claude" / "hooks" / "checkers" / "workflow_checker.py"
    )
    spec = importlib.util.spec_from_file_location("workflow_checker", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_workflow_checker()
ValidationResult = _mod.ValidationResult
GapTransition = _mod.GapTransition
VALID_TRANSITIONS = _mod.VALID_TRANSITIONS
RESOLUTION_RULES = _mod.RESOLUTION_RULES
validate_gap_transition = _mod.validate_gap_transition
_get_gap_category = _mod._get_gap_category
validate_session_start = _mod.validate_session_start
validate_session_end = _mod.validate_session_end
check_workflow_compliance = _mod.check_workflow_compliance
format_workflow_for_healthcheck = _mod.format_workflow_for_healthcheck
get_workflow_status = _mod.get_workflow_status


# ── ValidationResult dataclass ────────────────────────────

class TestValidationResult:
    def test_constructor(self):
        vr = ValidationResult(
            rule_id="R-1", check_name="chk", status="PASS", message="ok"
        )
        assert vr.rule_id == "R-1"
        assert vr.evidence is None

    def test_to_dict_keys(self):
        vr = ValidationResult(
            rule_id="R", check_name="c", status="FAIL",
            message="m", evidence="e"
        )
        d = vr.to_dict()
        assert set(d.keys()) == {
            "rule_id", "check_name", "status", "message",
            "evidence", "timestamp"
        }
        # timestamp should be ISO format string
        datetime.fromisoformat(d["timestamp"])

    def test_default_timestamp(self):
        vr = ValidationResult(rule_id="R", check_name="c", status="PASS", message="m")
        assert isinstance(vr.timestamp, datetime)


# ── GapTransition dataclass ───────────────────────────────

class TestGapTransition:
    def test_defaults(self):
        gt = GapTransition(
            gap_id="GAP-1", from_state="OPEN",
            to_state="IN_PROGRESS", timestamp=datetime.now()
        )
        assert gt.evidence is None
        assert gt.validated is False


# ── Constants ─────────────────────────────────────────────

class TestConstants:
    def test_resolved_is_terminal(self):
        assert VALID_TRANSITIONS["RESOLVED"] == []

    def test_open_has_targets(self):
        assert "IN_PROGRESS" in VALID_TRANSITIONS["OPEN"]
        assert "RESOLVED" in VALID_TRANSITIONS["OPEN"]

    def test_all_states_present(self):
        for state in ["OPEN", "IN_PROGRESS", "PARTIAL", "DEFERRED", "RESOLVED"]:
            assert state in VALID_TRANSITIONS

    def test_resolution_rules_categories(self):
        assert "UI" in RESOLUTION_RULES
        assert "functionality" in RESOLUTION_RULES
        assert "infra" in RESOLUTION_RULES

    def test_resolution_rule_structure(self):
        for cat, cfg in RESOLUTION_RULES.items():
            assert "rule" in cfg
            assert "evidence_pattern" in cfg


# ── _get_gap_category ─────────────────────────────────────

class TestGetGapCategory:
    def test_ui(self):
        assert _get_gap_category("GAP-UI-001") == "UI"

    def test_infra(self):
        assert _get_gap_category("GAP-INFRA-PROCS-002") == "infra"

    def test_mcp(self):
        assert _get_gap_category("GAP-MCP-READINESS-001") == "functionality"

    def test_workflow(self):
        assert _get_gap_category("GAP-WORKFLOW-XYZ") == "functionality"

    def test_unknown(self):
        assert _get_gap_category("GAP-OTHER-001") == "general"


# ── validate_gap_transition ───────────────────────────────

class TestValidateGapTransition:
    def test_invalid_transition(self):
        r = validate_gap_transition("GAP-1", "RESOLVED", "OPEN")
        assert r.status == "FAIL"
        assert "not allowed" in r.message

    def test_valid_non_resolved(self):
        r = validate_gap_transition("GAP-1", "OPEN", "IN_PROGRESS")
        assert r.status == "PASS"

    def test_resolve_ui_without_evidence(self):
        r = validate_gap_transition("GAP-UI-001", "OPEN", "RESOLVED")
        assert r.status == "WARNING"
        assert "E2E" in r.message or "evidence" in r.message.lower()

    def test_resolve_ui_wrong_evidence(self):
        r = validate_gap_transition("GAP-UI-001", "OPEN", "RESOLVED",
                                    evidence="just a note")
        assert r.status == "WARNING"
        assert "pattern" in r.message.lower()

    def test_resolve_ui_correct_evidence(self):
        r = validate_gap_transition("GAP-UI-001", "OPEN", "RESOLVED",
                                    evidence="test_dashboard.py passed")
        assert r.status == "PASS"

    def test_resolve_general_no_evidence_ok(self):
        r = validate_gap_transition("GAP-DATA-001", "OPEN", "RESOLVED")
        assert r.status == "PASS"

    def test_unknown_from_state(self):
        r = validate_gap_transition("GAP-1", "FANTASY", "OPEN")
        assert r.status == "FAIL"


# ── validate_session_start ────────────────────────────────

class TestValidateSessionStart:
    def test_all_present(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# Rules")
        (tmp_path / "TODO.md").write_text("# Tasks")
        (tmp_path / "evidence").mkdir()
        results = validate_session_start(tmp_path)
        statuses = [r.status for r in results]
        assert all(s == "PASS" for s in statuses)

    def test_missing_claude_md(self, tmp_path):
        (tmp_path / "TODO.md").write_text("")
        (tmp_path / "evidence").mkdir()
        results = validate_session_start(tmp_path)
        claude_check = next(r for r in results if r.check_name == "claude_md_exists")
        assert claude_check.status == "FAIL"

    def test_missing_todo(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("")
        (tmp_path / "evidence").mkdir()
        results = validate_session_start(tmp_path)
        todo_check = next(r for r in results if r.check_name == "todo_md_exists")
        assert todo_check.status == "WARNING"

    def test_missing_evidence_dir(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("")
        (tmp_path / "TODO.md").write_text("")
        results = validate_session_start(tmp_path)
        ev_check = next(r for r in results if r.check_name == "evidence_dir_exists")
        assert ev_check.status == "FAIL"


# ── validate_session_end ──────────────────────────────────

class TestValidateSessionEnd:
    def test_evidence_exists(self, tmp_path):
        ef = tmp_path / "SESSION-X.md"
        ef.write_text("evidence")
        results = validate_session_end("S-1", str(ef), ["T1"])
        assert results[0].status == "PASS"
        assert results[1].status == "PASS"

    def test_evidence_missing_file(self, tmp_path):
        results = validate_session_end("S-1", str(tmp_path / "nope.md"))
        assert results[0].status == "FAIL"

    def test_no_evidence_path(self):
        results = validate_session_end("S-1")
        assert results[0].status == "WARNING"

    def test_no_tasks(self):
        results = validate_session_end("S-1", None, [])
        task_check = next(r for r in results if r.check_name == "tasks_documented")
        assert task_check.status == "WARNING"


# ── check_workflow_compliance ─────────────────────────────

class TestCheckWorkflowCompliance:
    def test_compliant(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("")
        (tmp_path / "TODO.md").write_text("")
        (tmp_path / "evidence").mkdir()
        result = check_workflow_compliance(tmp_path)
        assert result["overall_status"] == "COMPLIANT"
        assert result["checks_passed"] == 3

    def test_violations(self, tmp_path):
        # Nothing exists
        result = check_workflow_compliance(tmp_path)
        assert result["overall_status"] == "VIOLATIONS"
        assert result["checks_failed"] >= 1
        assert len(result["violations"]) >= 1

    def test_warnings_only(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("")
        (tmp_path / "evidence").mkdir()
        # TODO.md missing → WARNING (not FAIL)
        result = check_workflow_compliance(tmp_path)
        assert result["overall_status"] == "WARNINGS"


# ── format_workflow_for_healthcheck ───────────────────────

class TestFormatWorkflowForHealthcheck:
    def test_compliant_format(self):
        data = {
            "overall_status": "COMPLIANT",
            "checks_passed": 3, "checks_failed": 0, "checks_warning": 0,
            "violations": [], "warnings": [],
        }
        lines = format_workflow_for_healthcheck(data)
        text = "\n".join(lines)
        assert "COMPLIANT" in text
        assert "Passed: 3" in text

    def test_violations_shown(self):
        data = {
            "overall_status": "VIOLATIONS",
            "checks_passed": 1, "checks_failed": 1, "checks_warning": 0,
            "violations": [{"rule_id": "R-1", "message": "bad"}],
            "warnings": [],
        }
        lines = format_workflow_for_healthcheck(data)
        text = "\n".join(lines)
        assert "[R-1]" in text
        assert "bad" in text

    def test_max_three_violations(self):
        viols = [{"rule_id": f"R-{i}", "message": f"v{i}"} for i in range(5)]
        data = {
            "overall_status": "VIOLATIONS",
            "checks_passed": 0, "checks_failed": 5, "checks_warning": 0,
            "violations": viols, "warnings": [],
        }
        lines = format_workflow_for_healthcheck(data)
        text = "\n".join(lines)
        assert "R-4" not in text  # 4th+ truncated


# ── get_workflow_status ───────────────────────────────────

class TestGetWorkflowStatus:
    def test_compliant(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("")
        (tmp_path / "TODO.md").write_text("")
        (tmp_path / "evidence").mkdir()
        result = get_workflow_status(tmp_path)
        assert result["compliant"] is True
        assert "COMPLIANT" in result["summary"]

    def test_non_compliant(self, tmp_path):
        result = get_workflow_status(tmp_path)
        assert result["compliant"] is False
        assert "raw" in result
