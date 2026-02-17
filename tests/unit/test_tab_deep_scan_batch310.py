"""
Deep Scan Batch 310-313: Defense tests for security fixes.

Tests for:
  BUG-310-READ-001: sessions/read.py backslash-first escape (3 sites)
  BUG-310-LINK-001: sessions/linking.py backslash-first escape (10 sites)
  BUG-311-EVID-001: evidence_transcript.py path traversal guard
  BUG-311-EVID-002: evidence_transcript.py file size guard
  BUG-313-VEC-001: vector_store/store.py newline escape in delete_by_source
"""

import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-310-READ-001: sessions/read.py backslash-first escape ──────────


class TestSessionReadEscapeOrder:
    """Verify sessions/read.py uses backslash-first escape on all string fields."""

    def _read_src(self):
        return (SRC / "governance/typedb/queries/sessions/read.py").read_text()

    def test_build_session_from_id_escape(self):
        src = self._read_src()
        idx = src.find("def _build_session_from_id")
        assert idx != -1
        block = src[idx:idx + 300]
        assert "BUG-310-READ-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_get_session_escape(self):
        src = self._read_src()
        idx = src.find("def get_session(self, session_id")
        assert idx != -1
        block = src[idx:idx + 300]
        assert "BUG-310-READ-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_get_tasks_for_session_escape(self):
        src = self._read_src()
        idx = src.find("def get_tasks_for_session")
        assert idx != -1
        block = src[idx:idx + 300]
        assert "BUG-310-READ-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_no_quote_only_escapes_remain(self):
        """Ensure no .replace('"', '\\"') without preceding backslash escape."""
        src = self._read_src()
        # Count correct two-step patterns
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)\.replace\('\"', '\\\\\"'\)"
        correct = len(re.findall(pattern, src))
        # Count all .replace('"', '\\"')
        quote_only = src.count('.replace(\'"\', \'\\\\"\')') - correct
        assert quote_only == 0, f"Found {quote_only} quote-only escapes in read.py"


# ── BUG-310-LINK-001: sessions/linking.py backslash-first escape ───────


class TestSessionLinkingEscapeOrder:
    """Verify sessions/linking.py uses backslash-first escape on all string fields."""

    def _read_src(self):
        return (SRC / "governance/typedb/queries/sessions/linking.py").read_text()

    def test_link_evidence_escape(self):
        src = self._read_src()
        idx = src.find("def link_evidence_to_session")
        end_idx = src.find("def get_session_evidence")
        assert idx != -1
        block = src[idx:end_idx]
        assert "BUG-310-LINK-001" in block
        # Should have 3 backslash-first escapes: evidence_source, evidence_id, session_id
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)"
        matches = re.findall(pattern, block)
        assert len(matches) >= 3, f"Expected >=3 backslash-first in link_evidence, got {len(matches)}"

    def test_get_session_evidence_escape(self):
        src = self._read_src()
        idx = src.find("def get_session_evidence")
        assert idx != -1
        block = src[idx:idx + 400]
        assert "BUG-310-LINK-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_link_rule_escape(self):
        src = self._read_src()
        idx = src.find("def link_rule_to_session")
        end_idx = src.find("def link_decision_to_session")
        assert idx != -1
        block = src[idx:end_idx]
        assert "BUG-310-LINK-001" in block
        # Should have 2 escapes: session_id and rule_id
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)"
        matches = re.findall(pattern, block)
        assert len(matches) >= 2, f"Expected >=2 backslash-first in link_rule, got {len(matches)}"

    def test_link_decision_escape(self):
        src = self._read_src()
        idx = src.find("def link_decision_to_session")
        end_idx = src.find("def get_session_rules")
        assert idx != -1
        block = src[idx:end_idx]
        assert "BUG-310-LINK-001" in block
        # Should have 2 escapes: session_id and decision_id
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)"
        matches = re.findall(pattern, block)
        assert len(matches) >= 2, f"Expected >=2 backslash-first in link_decision, got {len(matches)}"

    def test_get_session_rules_escape(self):
        src = self._read_src()
        idx = src.find("def get_session_rules")
        assert idx != -1
        block = src[idx:idx + 400]
        assert "BUG-310-LINK-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_get_session_decisions_escape(self):
        src = self._read_src()
        idx = src.find("def get_session_decisions")
        assert idx != -1
        block = src[idx:idx + 400]
        assert "BUG-310-LINK-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_no_quote_only_escapes_remain(self):
        """Ensure no .replace('"', '\\"') without preceding backslash escape."""
        src = self._read_src()
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)\.replace\('\"', '\\\\\"'\)"
        correct = len(re.findall(pattern, src))
        quote_only = src.count('.replace(\'"\', \'\\\\"\')') - correct
        assert quote_only == 0, f"Found {quote_only} quote-only escapes in linking.py"

    def test_total_backslash_first_count(self):
        """Verify total count of backslash-first escapes matches expected."""
        src = self._read_src()
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)\.replace\('\"', '\\\\\"'\)"
        count = len(re.findall(pattern, src))
        # 10 escapes across 6 functions
        assert count >= 10, f"Expected >=10 backslash-first escapes in linking.py, got {count}"


# ── BUG-311-EVID-001: evidence_transcript.py path traversal guard ──────


class TestEvidenceTranscriptPathTraversal:
    """Verify find_evidence_file blocks path traversal."""

    def test_source_has_path_guard(self):
        src = (SRC / "governance/services/evidence_transcript.py").read_text()
        assert "BUG-311-EVID-001" in src
        assert ".resolve()" in src
        assert "startswith" in src

    def test_traversal_blocked(self):
        """Verify path traversal session_id is rejected."""
        from governance.services.evidence_transcript import find_evidence_file
        result = find_evidence_file("../../etc/passwd")
        assert result is None

    def test_normal_session_id_works(self):
        """Non-traversal ID should not raise (may return None if file missing)."""
        from governance.services.evidence_transcript import find_evidence_file
        result = find_evidence_file("SESSION-2026-01-01-TEST")
        # Just checking it doesn't raise — file likely doesn't exist
        assert result is None or isinstance(result, Path)


# ── BUG-311-EVID-002: evidence_transcript.py file size guard ───────────


class TestEvidenceTranscriptSizeGuard:
    """Verify parse_evidence_transcript has file size check."""

    def test_source_has_size_guard(self):
        src = (SRC / "governance/services/evidence_transcript.py").read_text()
        assert "BUG-311-EVID-002" in src
        assert "_MAX_EVIDENCE_BYTES" in src
        assert "file_too_large" in src


# ── BUG-313-VEC-001: store.py newline escape in delete_by_source ───────


class TestVectorStoreNewlineEscape:
    """Verify delete_by_source strips newlines from source_id."""

    def test_source_has_newline_escape(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        idx = src.find("def delete_by_source")
        assert idx != -1
        block = src[idx:idx + 700]
        assert "BUG-313-VEC-001" in block
        assert ".replace('\\n', '')" in block
        assert ".replace('\\r', '')" in block

    def test_backslash_first_preserved(self):
        """Verify backslash-first escape is still present."""
        src = (SRC / "governance/vector_store/store.py").read_text()
        idx = src.find("def delete_by_source")
        block = src[idx:idx + 700]
        assert ".replace('\\\\', '\\\\\\\\')" in block


# ── Import verification ─────────────────────────────────────────────


class TestBatch310Imports:
    """Verify all fixed modules import cleanly."""

    def test_import_session_read(self):
        from governance.typedb.queries.sessions import read  # noqa: F401

    def test_import_session_linking(self):
        from governance.typedb.queries.sessions import linking  # noqa: F401

    def test_import_evidence_transcript(self):
        from governance.services import evidence_transcript  # noqa: F401

    def test_import_vector_store(self):
        from governance.vector_store import store  # noqa: F401
