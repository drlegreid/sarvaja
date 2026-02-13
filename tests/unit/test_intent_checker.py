"""
Unit tests for Intent Checker Module.

Batch 157a: Tests for .claude/hooks/checkers/intent_checker.py
- find_latest_evidence_file
- extract_intent_from_evidence
- check_intent_continuity
- format_intent_for_healthcheck
- get_intent_status
- reconcile_intent
- detect_amnesia
- format_amnesia_alert
"""

import importlib.util
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_intent_checker():
    mod_path = (
        Path(__file__).parent.parent.parent
        / ".claude" / "hooks" / "checkers" / "intent_checker.py"
    )
    spec = importlib.util.spec_from_file_location("intent_checker", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_intent_checker()
find_latest_evidence_file = _mod.find_latest_evidence_file
extract_intent_from_evidence = _mod.extract_intent_from_evidence
check_intent_continuity = _mod.check_intent_continuity
format_intent_for_healthcheck = _mod.format_intent_for_healthcheck
get_intent_status = _mod.get_intent_status
reconcile_intent = _mod.reconcile_intent
detect_amnesia = _mod.detect_amnesia
format_amnesia_alert = _mod.format_amnesia_alert


# ── find_latest_evidence_file ─────────────────────────────

class TestFindLatestEvidenceFile:
    def test_missing_dir(self, tmp_path):
        assert find_latest_evidence_file(tmp_path / "nope") is None

    def test_empty_dir(self, tmp_path):
        assert find_latest_evidence_file(tmp_path) is None

    def test_no_session_files(self, tmp_path):
        (tmp_path / "README.md").write_text("hi")
        assert find_latest_evidence_file(tmp_path) is None

    def test_returns_recent_file(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        f = tmp_path / f"SESSION-{today}-TOPIC.md"
        f.write_text("content")
        result = find_latest_evidence_file(tmp_path)
        assert result == f

    def test_filters_old_files(self, tmp_path):
        old_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        f = tmp_path / f"SESSION-{old_date}-OLD.md"
        f.write_text("old")
        assert find_latest_evidence_file(tmp_path, max_age_hours=24) is None

    def test_returns_most_recent(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        f1 = tmp_path / f"SESSION-{today}-FIRST.md"
        f1.write_text("first")
        time.sleep(0.05)
        f2 = tmp_path / f"SESSION-{today}-SECOND.md"
        f2.write_text("second")
        result = find_latest_evidence_file(tmp_path)
        assert result == f2

    def test_skips_unparseable_names(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        (tmp_path / "SESSION-BADNAME.md").write_text("bad")
        good = tmp_path / f"SESSION-{today}-GOOD.md"
        good.write_text("good")
        assert find_latest_evidence_file(tmp_path) == good


# ── extract_intent_from_evidence ──────────────────────────

_SAMPLE_EVIDENCE = """\
**Session ID:** SESSION-2026-02-13-TEST

## Session Intent

**Goal:** Fix authentication bug
**Source:** Backlog GAP-AUTH-001

### Planned Tasks

- [x] TASK-001
- [ ] TASK-002

## Session Outcome

**Status:** PARTIAL

### Achieved Tasks

- [x] TASK-001

### Deferred Tasks

- [ ] TASK-002

### Handoff Items (for next session)

- Continue TASK-002 from step 3
- Review failing E2E tests

### Discoveries

- New API rate limit discovered
"""


class TestExtractIntentFromEvidence:
    def test_extracts_session_id(self, tmp_path):
        f = tmp_path / "SESSION-2026-02-13-TEST.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = extract_intent_from_evidence(f)
        assert result["session_id"] == "SESSION-2026-02-13-TEST"

    def test_fallback_session_id_from_filename(self, tmp_path):
        f = tmp_path / "SESSION-2026-02-13-OTHER.md"
        f.write_text("No session ID line here")
        result = extract_intent_from_evidence(f)
        assert result["session_id"] == "SESSION-2026-02-13-OTHER"

    def test_extracts_intent_goal(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = extract_intent_from_evidence(f)
        assert result["intent"]["goal"] == "Fix authentication bug"
        assert result["intent"]["source"] == "Backlog GAP-AUTH-001"

    def test_extracts_planned_tasks(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = extract_intent_from_evidence(f)
        assert "TASK-001" in result["intent"]["planned_tasks"]
        assert "TASK-002" in result["intent"]["planned_tasks"]

    def test_extracts_outcome_status(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = extract_intent_from_evidence(f)
        assert result["outcome"]["status"] == "PARTIAL"

    def test_extracts_handoff_items(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = extract_intent_from_evidence(f)
        assert len(result["handoff_items"]) == 2
        assert "Continue TASK-002" in result["handoff_items"][0]

    def test_extracts_discoveries(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = extract_intent_from_evidence(f)
        assert len(result["discoveries"]) == 1

    def test_missing_sections_returns_defaults(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("# Just a heading\nSome text.")
        result = extract_intent_from_evidence(f)
        assert result["intent"] is None
        assert result["outcome"] is None
        assert result["handoff_items"] == []

    def test_file_read_error(self, tmp_path):
        f = tmp_path / "nonexistent.md"
        result = extract_intent_from_evidence(f)
        assert result["session_id"] == ""


# ── check_intent_continuity ──────────────────────────────

class TestCheckIntentContinuity:
    def test_no_evidence(self, tmp_path):
        result = check_intent_continuity(tmp_path)
        assert result["has_previous"] is False
        assert "No recent session" in result["recommendations"][0]

    def test_with_intent_data(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        f = tmp_path / f"SESSION-{today}-TEST.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = check_intent_continuity(tmp_path)
        assert result["has_previous"] is True
        assert result["handoff_count"] == 2
        assert result["discovery_count"] == 1

    def test_partial_status_recommendation(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        f = tmp_path / f"SESSION-{today}-PART.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = check_intent_continuity(tmp_path)
        recs = " ".join(result["recommendations"])
        assert "PARTIAL" in recs


# ── format_intent_for_healthcheck ─────────────────────────

class TestFormatIntentForHealthcheck:
    def test_no_previous_returns_empty(self):
        assert format_intent_for_healthcheck({"has_previous": False}) == []

    def test_with_previous_shows_session_info(self):
        data = {
            "has_previous": True,
            "previous_session": {"id": "S-1", "goal": "Test goal", "status": "DONE"},
            "handoff_count": 0,
            "recommendations": [],
        }
        lines = format_intent_for_healthcheck(data)
        joined = "\n".join(lines)
        assert "S-1" in joined
        assert "Test goal" in joined

    def test_with_handoffs_shows_count(self):
        data = {
            "has_previous": True,
            "previous_session": {"id": "S-1", "goal": "G", "status": "OK"},
            "handoff_count": 3,
            "first_handoff": "Do something important",
            "recommendations": [],
        }
        lines = format_intent_for_healthcheck(data)
        joined = "\n".join(lines)
        assert "3 items pending" in joined
        assert "Do something" in joined

    def test_max_three_recommendations(self):
        data = {
            "has_previous": True,
            "previous_session": {"id": "S", "goal": "G", "status": "S"},
            "handoff_count": 0,
            "recommendations": ["R1", "R2", "R3", "R4"],
        }
        lines = format_intent_for_healthcheck(data)
        text = "\n".join(lines)
        assert "R4" not in text


# ── get_intent_status ─────────────────────────────────────

class TestGetIntentStatus:
    def test_no_previous(self, tmp_path):
        result = get_intent_status(tmp_path)
        assert result["has_continuity"] is False
        assert result["summary"] == "No previous session"

    def test_with_previous(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        f = tmp_path / f"SESSION-{today}-X.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = get_intent_status(tmp_path)
        assert result["has_continuity"] is True
        assert "handoffs" in result["summary"]
        assert isinstance(result["lines"], list)


# ── reconcile_intent ──────────────────────────────────────

class TestReconcileIntent:
    def test_no_handoffs_aligned(self):
        result = reconcile_intent(["task1"], [])
        assert result["status"] == "ALIGNED"
        assert result["alignment_score"] == 1.0

    def test_all_picked_up(self):
        result = reconcile_intent(
            ["fix auth bug", "update docs"],
            ["fix auth bug", "update docs"],
        )
        assert result["status"] == "ALIGNED"
        assert result["alignment_score"] == 1.0

    def test_amnesia_detection(self):
        result = reconcile_intent(
            ["unrelated work"],
            ["handoff-1", "handoff-2", "handoff-3"],
        )
        assert result["status"] == "AMNESIA"
        assert result["alignment_score"] < 0.5
        assert len(result["missing_handoffs"]) == 3

    def test_drift_detection(self):
        result = reconcile_intent(
            ["handoff-1", "new-a", "new-b", "new-c"],
            ["handoff-1", "handoff-2"],
        )
        assert result["status"] == "DRIFT"
        assert len(result["unexpected_work"]) >= 2

    def test_partial_pickup(self):
        result = reconcile_intent(
            ["handoff-1"],
            ["handoff-1", "handoff-2"],
        )
        assert result["picked_up_count"] == 1
        assert result["alignment_score"] == 0.5

    def test_unexpected_work_capped_at_five(self):
        result = reconcile_intent(
            [f"new-{i}" for i in range(10)],
            ["handoff"],
        )
        assert len(result["unexpected_work"]) <= 5


# ── detect_amnesia ────────────────────────────────────────

class TestDetectAmnesia:
    def test_no_evidence(self, tmp_path):
        result = detect_amnesia(tmp_path)
        assert result["detected"] is False
        assert result["severity"] == "NONE"

    def test_no_handoffs(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        f = tmp_path / f"SESSION-{today}-CLEAN.md"
        f.write_text("## Session Intent\n\n**Goal:** Stuff\n**Source:** Backlog\n\n## Session Outcome\n\n**Status:** COMPLETED\n")
        result = detect_amnesia(tmp_path)
        assert result["detected"] is False

    def test_partial_status_alert(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        f = tmp_path / f"SESSION-{today}-PART.md"
        f.write_text(_SAMPLE_EVIDENCE)
        result = detect_amnesia(tmp_path)
        assert result["detected"] is True
        assert result["severity"] == "ALERT"

    def test_many_handoffs_alert(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        content = (
            "## Session Outcome\n\n**Status:** COMPLETED\n\n"
            "### Handoff Items (for next session)\n\n"
            "- Item 1\n- Item 2\n- Item 3\n"
        )
        f = tmp_path / f"SESSION-{today}-MANY.md"
        f.write_text(content)
        result = detect_amnesia(tmp_path)
        assert result["severity"] == "ALERT"

    def test_few_handoffs_warning(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        content = (
            "## Session Outcome\n\n**Status:** COMPLETED\n\n"
            "### Handoff Items (for next session)\n\n"
            "- Just one item\n"
        )
        f = tmp_path / f"SESSION-{today}-FEW.md"
        f.write_text(content)
        result = detect_amnesia(tmp_path)
        assert result["severity"] == "WARNING"


# ── format_amnesia_alert ──────────────────────────────────

class TestFormatAmnesiaAlert:
    def test_alert_format(self):
        data = {"severity": "ALERT", "previous_session": "S-1",
                "missing_handoffs": ["H1", "H2"]}
        lines = format_amnesia_alert(data, {})
        text = "\n".join(lines)
        assert "ALERT" in text
        assert "S-1" in text
        assert "H1" in text

    def test_warning_format(self):
        data = {"severity": "WARNING", "previous_session": "S-2",
                "missing_handoffs": ["Do X"]}
        lines = format_amnesia_alert(data, {})
        text = "\n".join(lines)
        assert "S-2" in text
        assert "Do X" in text[:100]

    def test_more_than_three_handoffs_truncated(self):
        data = {"severity": "ALERT", "previous_session": "S",
                "missing_handoffs": ["A", "B", "C", "D", "E"]}
        lines = format_amnesia_alert(data, {})
        text = "\n".join(lines)
        assert "and 2 more" in text
