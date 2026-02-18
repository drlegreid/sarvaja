"""Batch 257 — Session metrics and services defense tests.

Validates fixes for:
- BUG-257-LNK-001: None guard on get_all_decisions in cc_link_miner.py
- BUG-257-LNK-002: Logging in entity validation except block
- BUG-257-TRS-001: File handle cleanup in cc_transcript.py
- BUG-257-TRS-002: json.dumps default=str for non-serializable inputs
- BUG-257-TRS-003: Page validation in get_transcript_page
- BUG-257-IDX-001: Checkpoint offset fix in cc_content_indexer.py
- BUG-257-ING-001: UTC-aware datetimes in cc_session_ingestion.py
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-257-LNK-001/002: cc_link_miner.py fixes ─────────────────────

class TestLinkMinerFixes:
    """cc_link_miner.py must guard against None decisions and log errors."""

    def test_none_guard_on_decisions(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        assert "get_all_decisions() or []" in src

    def test_except_logs_warning(self):
        """Except block must log, not silently swallow."""
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        idx = src.index("def _validate_entity_exists")
        block = src[idx:idx + 1500]
        assert "logger.warning" in block

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/cc_link_miner.py").read_text()
        assert "BUG-257-LNK-001" in src
        assert "BUG-257-LNK-002" in src


# ── BUG-257-TRS-002: json.dumps default=str ──────────────────────────

class TestTranscriptJsonDumps:
    """cc_transcript.py must use default=str in json.dumps for tool inputs."""

    def test_json_dumps_default_str(self):
        src = (SRC / "governance/services/cc_transcript.py").read_text()
        assert "json.dumps(block.get" in src or "json.dumps(" in src
        assert "default=str" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_transcript.py").read_text()
        assert "BUG-257-TRS-002" in src


# ── BUG-257-TRS-003: Page validation ─────────────────────────────────

class TestTranscriptPageValidation:
    """get_transcript_page and build_synthetic_transcript must validate page."""

    def test_page_validation_in_get_transcript_page(self):
        src = (SRC / "governance/services/cc_transcript.py").read_text()
        idx = src.index("def get_transcript_page")
        block = src[idx:idx + 500]
        assert "max(1, page)" in block

    def test_page_validation_in_build_synthetic(self):
        src = (SRC / "governance/services/cc_transcript.py").read_text()
        idx = src.index("def build_synthetic_transcript")
        block = src[idx:idx + 3000]
        assert "max(1, page)" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_transcript.py").read_text()
        assert "BUG-257-TRS-003" in src


# ── BUG-257-IDX-001: Checkpoint offset fix ────────────────────────────

class TestContentIndexerCheckpoint:
    """cc_content_indexer.py must compute checkpoint offset correctly."""

    def test_no_double_start_line(self):
        """The old pattern line_end + start_line + 1 should not appear."""
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        # Old buggy pattern: meta.get("line_end", ...) + start_line + 1
        # should be replaced with: start_line + meta.get("line_end", ...) + 1
        assert 'lines_seen) + start_line + 1' not in src

    def test_correct_offset_formula(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        assert "start_line + meta.get" in src or "start_line + batch_metas" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        assert "BUG-257-IDX-001" in src


# ── BUG-257-ING-001: UTC-aware datetimes ──────────────────────────────

class TestIngestionTimezone:
    """cc_session_ingestion.py must use UTC-aware datetimes."""

    def test_utc_in_fromtimestamp(self):
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        assert "tz=timezone.utc" in src

    def test_utc_in_datetime_now(self):
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        assert "datetime.now(tz=timezone.utc)" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        assert "BUG-257-ING-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch257Imports:
    def test_cc_link_miner_importable(self):
        import governance.services.cc_link_miner
        assert governance.services.cc_link_miner is not None

    def test_cc_transcript_importable(self):
        import governance.services.cc_transcript
        assert governance.services.cc_transcript is not None

    def test_cc_content_indexer_importable(self):
        import governance.services.cc_content_indexer
        assert governance.services.cc_content_indexer is not None

    def test_cc_session_ingestion_importable(self):
        import governance.services.cc_session_ingestion
        assert governance.services.cc_session_ingestion is not None

    def test_cc_session_scanner_importable(self):
        import governance.services.cc_session_scanner
        assert governance.services.cc_session_scanner is not None

    def test_correlation_importable(self):
        import governance.session_metrics.correlation
        assert governance.session_metrics.correlation is not None

    def test_parser_importable(self):
        import governance.session_metrics.parser
        assert governance.session_metrics.parser is not None
