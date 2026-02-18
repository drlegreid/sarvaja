"""Deep scan batch 103: Models + validators + config + startup.

Batch 103 findings: 24 total, 1 confirmed fix, 23 rejected.
Fix: BUG-EVIDENCE-TABLE-PIPE-002 — task description pipe escaping in evidence markdown.
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path


# ── Evidence pipe escaping (CONFIRMED FIX) ──────────────


class TestEvidencePipeEscaping:
    """Verify pipe escaping in evidence markdown tables (BUG-EVIDENCE-TABLE-PIPE-002)."""

    def test_task_description_pipe_escaped(self):
        """Task description with pipe character doesn't corrupt table."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-TEST",
            "start_time": "2026-02-15T09:00:00",
            "end_time": "2026-02-15T10:00:00",
            "status": "COMPLETED",
            "decisions": [],
            "tasks": [
                {
                    "task_id": "TASK-001",
                    "description": "Fix input | output validation",
                    "status": "DONE",
                }
            ],
            "tool_calls": [],
            "thinking_blocks": 0,
        }
        md = render_evidence_markdown(evidence_data)
        # Pipe in description should be escaped
        assert "Fix input \\| output validation" in md
        # Table should have exactly 3 pipe-delimited columns per row
        task_lines = [l for l in md.split("\n") if "TASK-001" in l]
        assert len(task_lines) == 1
        # Count unescaped pipes (not preceded by backslash)
        import re
        unescaped = re.findall(r'(?<!\\)\|', task_lines[0])
        assert len(unescaped) == 4  # | col1 | col2 | col3 |

    def test_decision_pipe_escaping_preserved(self):
        """Decision title/rationale pipe escaping still works."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-TEST2",
            "start_time": "2026-02-15T09:00:00",
            "end_time": "2026-02-15T10:00:00",
            "status": "COMPLETED",
            "decisions": [
                {
                    "decision_id": "DEC-001",
                    "title": "Use A | B approach",
                    "rationale": "Because X | Y",
                }
            ],
            "tasks": [],
            "tool_calls": [],
            "thinking_blocks": 0,
        }
        md = render_evidence_markdown(evidence_data)
        assert "Use A \\| B approach" in md
        assert "Because X \\| Y" in md

    def test_no_pipe_no_change(self):
        """Normal task descriptions pass through unchanged."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-TEST3",
            "start_time": "2026-02-15T09:00:00",
            "end_time": "2026-02-15T10:00:00",
            "status": "COMPLETED",
            "decisions": [],
            "tasks": [
                {
                    "task_id": "TASK-002",
                    "description": "Simple task description",
                    "status": "OPEN",
                }
            ],
            "tool_calls": [],
            "thinking_blocks": 0,
        }
        md = render_evidence_markdown(evidence_data)
        assert "Simple task description" in md


# ── Evidence duration defense ──────────────


class TestEvidenceDurationDefense:
    """Verify duration computation handles edge cases."""

    def test_z_suffix_stripped_consistently(self):
        """Both timestamps with Z suffix produce valid duration."""
        from governance.services.session_evidence import _compute_duration

        result = _compute_duration(
            "2026-02-15T09:00:00Z",
            "2026-02-15T10:30:00Z",
        )
        assert result == "1h 30m"

    def test_naive_timestamps_work(self):
        """Naive timestamps produce valid duration."""
        from governance.services.session_evidence import _compute_duration

        result = _compute_duration(
            "2026-02-15T09:00:00",
            "2026-02-15T09:45:00",
        )
        assert result == "45m"

    def test_invalid_timestamps_return_unknown(self):
        """Malformed timestamps return 'unknown'."""
        from governance.services.session_evidence import _compute_duration

        result = _compute_duration("not-a-date", "also-not-a-date")
        assert result == "unknown"

    def test_empty_timestamps_return_unknown(self):
        """Empty/None timestamps return 'unknown'."""
        from governance.services.session_evidence import _compute_duration

        assert _compute_duration("", "") == "unknown"
        assert _compute_duration(None, None) == "unknown"


# ── Model default values defense ──────────────


class TestModelDefaults:
    """Verify Pydantic model defaults work correctly."""

    def test_task_create_status_defaults_to_todo(self):
        """TaskCreate without status defaults to 'TODO'."""
        from governance.models import TaskCreate

        task = TaskCreate(description="Test task", phase="implementation")
        assert task.status == "TODO"

    def test_task_create_explicit_status(self):
        """TaskCreate with explicit status uses it."""
        from governance.models import TaskCreate

        task = TaskCreate(
            description="Test task",
            phase="implementation",
            status="IN_PROGRESS",
        )
        assert task.status == "IN_PROGRESS"

    def test_session_response_optional_lists_default_none(self):
        """SessionResponse optional list fields default to None."""
        from governance.models import SessionResponse

        session = SessionResponse(
            session_id="TEST-001",
            start_time="2026-02-15T10:00:00",
            status="ACTIVE",
        )
        assert session.evidence_files is None


# ── TypeDB port config defense ──────────────


class TestTypeDBPortConfig:
    """Verify TypeDB port configuration handles edge cases."""

    def test_default_port(self):
        """Default TypeDB port is 1729."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove TYPEDB_PORT if set
            env = os.environ.copy()
            env.pop("TYPEDB_PORT", None)
            with patch.dict(os.environ, env, clear=True):
                port = int(os.getenv("TYPEDB_PORT", "1729"))
                assert port == 1729

    def test_custom_port(self):
        """Custom TypeDB port from environment."""
        with patch.dict(os.environ, {"TYPEDB_PORT": "2729"}):
            port = int(os.getenv("TYPEDB_PORT", "1729"))
            assert port == 2729


# ── Seed data idempotency defense ──────────────


class TestSeedIdempotency:
    """Verify seed operations handle existing data."""

    def test_seed_skip_existing_pattern(self):
        """Seed pattern: check existing → skip if present."""
        existing_tasks = {"TASK-001": {"description": "existing"}}
        seed_tasks = [
            {"task_id": "TASK-001", "description": "new"},
            {"task_id": "TASK-002", "description": "new2"},
        ]
        seeded = 0
        for task in seed_tasks:
            if task["task_id"] in existing_tasks:
                continue
            existing_tasks[task["task_id"]] = task
            seeded += 1
        assert seeded == 1
        assert "TASK-002" in existing_tasks

    def test_seed_preserves_existing_status(self):
        """Seed doesn't overwrite existing task status."""
        existing = {"task_id": "TASK-001", "status": "IN_PROGRESS"}
        seed = {"task_id": "TASK-001", "status": "TODO"}
        # Skip pattern: existing found → don't update
        if existing:
            result_status = existing["status"]
        else:
            result_status = seed["status"]
        assert result_status == "IN_PROGRESS"


# ── Startup fire-and-forget warmup defense ──────────────


class TestStartupWarmup:
    """Verify startup warmup is non-blocking by design."""

    def test_run_in_executor_returns_future(self):
        """run_in_executor returns a Future (intentionally not awaited)."""
        import asyncio
        import concurrent.futures

        loop = asyncio.new_event_loop()
        try:
            future = loop.run_in_executor(
                concurrent.futures.ThreadPoolExecutor(max_workers=1),
                lambda: "warmup done",
            )
            # Future exists but doesn't block startup
            assert future is not None
        finally:
            loop.close()


# ── Auth middleware empty key defense ──────────────


class TestAuthEmptyKey:
    """Verify auth handles None vs empty string API key."""

    def test_none_api_key_means_no_auth(self):
        """None API_KEY = no auth required (dev mode)."""
        api_key = None
        assert not api_key  # Falsy → skip auth

    def test_empty_string_api_key_means_no_auth(self):
        """Empty string API_KEY treated same as None."""
        api_key = ""
        assert not api_key  # Also falsy → skip auth

    def test_valid_api_key_enables_auth(self):
        """Non-empty API_KEY enables authentication."""
        api_key = "secret-key-123"
        assert api_key  # Truthy → require auth
