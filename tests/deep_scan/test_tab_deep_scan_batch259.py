"""Batch 259 — TypeQL injection fixes in MCP traceability and trust tools.

Validates fixes for:
- BUG-259-TRACE-001: gap_id escaped before TypeQL interpolation in traceability.py
- BUG-259-TRACE-002: evidence_path escaped before TypeQL interpolation in traceability.py
- BUG-259-TRUST-001: Backslash+quote escaping in trust.py
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-259-TRACE-001: gap_id escaping ──────────────────────────────

class TestTraceGapIdEscaping:
    """trace_gap_chain must escape gap_id before TypeQL interpolation."""

    def test_gap_id_backslash_escape(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_gap_chain")
        block = src[idx:idx + 1200]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_gap_id_quote_escape(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_gap_chain")
        block = src[idx:idx + 1200]
        assert "safe_gap_id" in block

    def test_safe_gap_id_in_query(self):
        """Query must use safe_gap_id, not raw gap_id."""
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_gap_chain")
        block = src[idx:idx + 1200]
        assert '"{safe_gap_id}"' in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        assert "BUG-259-TRACE-001" in src


# ── BUG-259-TRACE-002: evidence_path escaping ───────────────────────

class TestTraceEvidencePathEscaping:
    """trace_evidence_chain must escape evidence_path before TypeQL interpolation."""

    def test_evidence_path_backslash_escape(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_evidence_chain")
        block = src[idx:idx + 1800]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_safe_evidence_path_variable(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_evidence_chain")
        block = src[idx:idx + 1800]
        assert "safe_evidence_path" in block

    def test_safe_evidence_path_in_task_query(self):
        """Task query must use safe_evidence_path."""
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_evidence_chain")
        block = src[idx:idx + 1800]
        assert '"{safe_evidence_path}"' in block

    def test_safe_evidence_path_in_session_query(self):
        """Session query must also use safe_evidence_path."""
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_evidence_chain")
        block = src[idx:idx + 1800]
        # Both queries should reference the safe variable
        count = block.count("safe_evidence_path")
        assert count >= 3, f"Expected safe_evidence_path used >=3 times, found {count}"

    def test_no_raw_evidence_path_in_queries(self):
        """Raw evidence_path must not be interpolated in f-strings after escape."""
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_evidence_chain")
        block = src[idx:idx + 1800]
        # After the escape line, f-string queries should NOT use raw evidence_path
        escape_idx = block.index("safe_evidence_path")
        after_escape = block[escape_idx:]
        assert '"{evidence_path}"' not in after_escape

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        assert "BUG-259-TRACE-002" in src


# ── BUG-259-TRUST-001: trust.py backslash escaping ──────────────────

class TestTrustEscaping:
    """trust.py must escape backslash before quotes in agent_id."""

    def test_backslash_escape_present(self):
        src = (SRC / "governance/mcp_tools/trust.py").read_text()
        idx = src.index("def governance_get_trust_score")
        block = src[idx:idx + 900]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/trust.py").read_text()
        assert "BUG-259-TRUST-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch259Imports:
    def test_traceability_importable(self):
        import governance.mcp_tools.traceability
        assert governance.mcp_tools.traceability is not None

    def test_trust_importable(self):
        import governance.mcp_tools.trust
        assert governance.mcp_tools.trust is not None

    def test_ingestion_importable(self):
        import governance.mcp_tools.ingestion
        assert governance.mcp_tools.ingestion is not None
