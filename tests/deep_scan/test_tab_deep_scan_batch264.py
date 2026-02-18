"""Batch 264 — Runner store encoding, checkpoint path, and silent exception tests.

Validates fixes for:
- BUG-264-STORE-001: write_text with encoding="utf-8" in runner_store.py
- BUG-264-STORE-002: read_text with encoding="utf-8" in runner_store.py
- BUG-265-CKPT-001: File-anchored checkpoint dir in ingestion_checkpoint.py
- BUG-264-CROSS-001: Logging in except block in heuristic_checks_cross.py
- BUG-264-EXPLR-001: Logging in except blocks in heuristic_checks_exploratory.py
- BUG-265-EVID-001: Logging in _compute_duration except in session_evidence.py
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-264-STORE-001/002: runner_store.py encoding ─────────────────

class TestRunnerStoreEncoding:
    """runner_store.py must specify encoding in write_text and read_text."""

    def test_write_text_encoding(self):
        src = (SRC / "governance/routes/tests/runner_store.py").read_text()
        idx = src.index("def _persist_result")
        block = src[idx:idx + 600]
        assert 'encoding="utf-8"' in block

    def test_read_text_encoding(self):
        src = (SRC / "governance/routes/tests/runner_store.py").read_text()
        idx = src.index("def _load_persisted_results")
        block = src[idx:idx + 600]
        assert 'encoding="utf-8"' in block

    def test_bug_markers_present(self):
        src = (SRC / "governance/routes/tests/runner_store.py").read_text()
        assert "BUG-264-STORE-001" in src
        assert "BUG-264-STORE-002" in src


# ── BUG-265-CKPT-001: ingestion_checkpoint.py path ──────────────────

class TestCheckpointPathAnchored:
    """Checkpoint dir must be file-anchored, not CWD-relative."""

    def test_not_bare_relative_path(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        # Must NOT have a bare Path(".ingestion_checkpoints")
        assert 'Path(".ingestion_checkpoints")' not in src

    def test_anchored_to_file(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        assert "Path(__file__)" in src
        assert ".ingestion_checkpoints" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        assert "BUG-265-CKPT-001" in src


# ── BUG-264-CROSS-001: heuristic_checks_cross.py logging ────────────

class TestCrossCheckLogging:
    """check_testid_coverage except block must log, not silently pass."""

    def test_except_logs(self):
        src = (SRC / "governance/routes/tests/heuristic_checks_cross.py").read_text()
        idx = src.index("def check_testid_coverage")
        block = src[idx:idx + 1500]
        assert "logger.debug" in block or "logging.getLogger" in block

    def test_no_bare_pass_after_except(self):
        """No bare 'except Exception: pass' should exist in the function."""
        src = (SRC / "governance/routes/tests/heuristic_checks_cross.py").read_text()
        idx = src.index("def check_testid_coverage")
        block = src[idx:idx + 1500]
        lines = block.split("\n")
        for i, line in enumerate(lines):
            if "except Exception" in line:
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                assert next_line != "pass", f"Bare pass after except at block line {i}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tests/heuristic_checks_cross.py").read_text()
        assert "BUG-264-CROSS-001" in src


# ── BUG-264-EXPLR-001: heuristic_checks_exploratory.py logging ──────

class TestExploratoryCheckLogging:
    """All except blocks in exploratory checks must log, not silently pass."""

    def test_no_bare_except_pass(self):
        """No bare 'except Exception:\\n        pass' should exist."""
        src = (SRC / "governance/routes/tests/heuristic_checks_exploratory.py").read_text()
        lines = src.split("\n")
        bare_passes = []
        for i, line in enumerate(lines):
            if line.strip().startswith("except Exception"):
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if next_line == "pass":
                    bare_passes.append(i + 1)
        assert not bare_passes, f"Bare except/pass at lines: {bare_passes}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tests/heuristic_checks_exploratory.py").read_text()
        assert "BUG-264-EXPLR-001" in src


# ── BUG-265-EVID-001: session_evidence.py logging ───────────────────

class TestEvidenceDurationLogging:
    """_compute_duration except block must log, not silently return."""

    def test_except_logs(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        idx = src.index("def _compute_duration")
        block = src[idx:idx + 1200]
        assert "logger.debug" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        assert "BUG-265-EVID-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch264Imports:
    def test_runner_store_importable(self):
        import governance.routes.tests.runner_store
        assert governance.routes.tests.runner_store is not None

    def test_ingestion_checkpoint_importable(self):
        import governance.services.ingestion_checkpoint
        assert governance.services.ingestion_checkpoint is not None

    def test_heuristic_checks_cross_importable(self):
        import governance.routes.tests.heuristic_checks_cross
        assert governance.routes.tests.heuristic_checks_cross is not None

    def test_heuristic_checks_exploratory_importable(self):
        import governance.routes.tests.heuristic_checks_exploratory
        assert governance.routes.tests.heuristic_checks_exploratory is not None

    def test_session_evidence_importable(self):
        import governance.services.session_evidence
        assert governance.services.session_evidence is not None
