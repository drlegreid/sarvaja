"""Batch 252 — Services layer defense tests.

Validates fixes for:
- BUG-252-SES-001: Path traversal sanitization in session_evidence.py
- BUG-252-SRP-001: ValueError guard in generate_timestamps
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-252-SES-001: Path traversal in session_evidence ──────────────

class TestSessionEvidencePathTraversal:
    """generate_session_evidence must sanitize session_id in file path."""

    def test_re_sub_present(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        idx = src.index("def generate_session_evidence")
        block = src[idx:idx + 1500]
        assert "re.sub(" in block or "_re.sub(" in block

    def test_safe_session_id_used(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        idx = src.index("def generate_session_evidence")
        block = src[idx:idx + 1500]
        assert "safe_session_id" in block

    def test_no_raw_session_id_in_path(self):
        """session_id must NOT appear directly in filepath construction."""
        src = (SRC / "governance/services/session_evidence.py").read_text()
        idx = src.index("def generate_session_evidence")
        block = src[idx:idx + 1500]
        assert 'f"{session_id}.md"' not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        assert "BUG-252-SES-001" in src


# ── BUG-252-SRP-001: ValueError guard in generate_timestamps ─────────

class TestGenerateTimestampsGuard:
    """generate_timestamps must not crash on invalid date strings."""

    def test_try_except_present(self):
        src = (SRC / "governance/services/session_repair.py").read_text()
        idx = src.index("def generate_timestamps")
        block = src[idx:idx + 800]
        assert "try:" in block
        assert "except ValueError:" in block

    def test_valid_date_works(self):
        from governance.services.session_repair import generate_timestamps
        start, end = generate_timestamps("2026-02-17")
        assert "2026-02-17" in start
        assert "T09:00:00" in start

    def test_invalid_date_does_not_crash(self):
        from governance.services.session_repair import generate_timestamps
        start, end = generate_timestamps("9999-99-99")
        # Should not raise — falls back to today
        assert start is not None
        assert end is not None

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/session_repair.py").read_text()
        assert "BUG-252-SRP-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch252Imports:
    def test_session_evidence_importable(self):
        import governance.services.session_evidence
        assert governance.services.session_evidence is not None

    def test_session_repair_importable(self):
        import governance.services.session_repair
        assert governance.services.session_repair is not None

    def test_projects_importable(self):
        import governance.services.projects
        assert governance.services.projects is not None

    def test_rules_importable(self):
        import governance.services.rules
        assert governance.services.rules is not None

    def test_sessions_importable(self):
        import governance.services.sessions
        assert governance.services.sessions is not None

    def test_sessions_lifecycle_importable(self):
        import governance.services.sessions_lifecycle
        assert governance.services.sessions_lifecycle is not None

    def test_tasks_importable(self):
        import governance.services.tasks
        assert governance.services.tasks is not None

    def test_tasks_mutations_importable(self):
        import governance.services.tasks_mutations
        assert governance.services.tasks_mutations is not None
