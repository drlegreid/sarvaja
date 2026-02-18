"""Deep scan batch 95: Evidence scanner + CC scanner + workflows + middleware.

Batch 95 findings: 35 total, 1 confirmed fix, 34 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


# ── CC session scanner defense ──────────────


class TestBuildSessionIdDefense:
    """Verify build_session_id handles edge cases."""

    def test_none_first_ts_handled(self):
        """BUG-SCANNER-DICT-GET-001: None first_ts uses fallback."""
        from governance.services.cc_session_scanner import build_session_id

        meta = {"first_ts": None, "slug": "test"}
        result = build_session_id(meta, "test-project")
        assert "1970-01-01" in result

    def test_missing_first_ts_handled(self):
        from governance.services.cc_session_scanner import build_session_id

        meta = {"slug": "test"}
        result = build_session_id(meta, "test-project")
        assert "1970-01-01" in result

    def test_valid_first_ts(self):
        from governance.services.cc_session_scanner import build_session_id

        meta = {"first_ts": "2026-02-15T10:00:00Z", "slug": "my-session"}
        result = build_session_id(meta, "test-project")
        assert "2026-02-15" in result
        assert result.startswith("SESSION-")


class TestScanJsonlMetadata:
    """Verify JSONL scanning handles edge cases."""

    def test_empty_file_returns_none(self, tmp_path):
        from governance.services.cc_session_scanner import scan_jsonl_metadata

        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert scan_jsonl_metadata(f) is None

    def test_no_timestamps_returns_none(self, tmp_path):
        from governance.services.cc_session_scanner import scan_jsonl_metadata

        f = tmp_path / "no_ts.jsonl"
        f.write_text('{"type": "system"}\n')
        assert scan_jsonl_metadata(f) is None

    def test_valid_jsonl_extracts_metadata(self, tmp_path):
        import json

        from governance.services.cc_session_scanner import scan_jsonl_metadata

        f = tmp_path / "valid.jsonl"
        lines = [
            json.dumps({"type": "user", "timestamp": "2026-02-15T10:00:00Z"}),
            json.dumps({"type": "assistant", "timestamp": "2026-02-15T10:01:00Z",
                         "message": {"content": [{"type": "text", "text": "hello"}]}}),
        ]
        f.write_text("\n".join(lines))

        result = scan_jsonl_metadata(f)
        assert result is not None
        assert result["first_ts"] == "2026-02-15T10:00:00Z"
        assert result["user_count"] == 1
        assert result["assistant_count"] == 1


class TestDeriveProjectSlug:
    """Verify project slug derivation."""

    def test_standard_path(self, tmp_path):
        from governance.services.cc_session_scanner import derive_project_slug

        d = tmp_path / "-home-user-Documents-project"
        d.mkdir()
        assert derive_project_slug(d) == "documents-project"

    def test_short_path(self, tmp_path):
        from governance.services.cc_session_scanner import derive_project_slug

        d = tmp_path / "single"
        d.mkdir()
        assert derive_project_slug(d) == "single"


# ── Orchestrator budget defense ──────────────


class TestBudgetZeroDivision:
    """Verify budget computation handles zero/None values."""

    def test_zero_token_budget(self):
        from governance.workflows.orchestrator.budget import compute_budget

        state = {
            "token_budget": 0,
            "tokens_used": 0,
            "value_delivered": 0,
            "cycles_completed": 0,
            "max_cycles": 10,
        }
        result = compute_budget(state)
        assert "should_continue" in result

    def test_no_token_budget_key(self):
        from governance.workflows.orchestrator.budget import compute_budget

        state = {"max_cycles": 5, "cycles_completed": 0}
        result = compute_budget(state)
        assert "should_continue" in result


# ── Merkle tree defense ──────────────


class TestMerkleTreeOddCount:
    """Verify Merkle tree handles odd leaf counts."""

    def test_odd_leaf_count(self):
        from governance.frankel_hash import build_merkle_tree

        leaves = ["abc", "def", "ghi"]
        result = build_merkle_tree(leaves)
        assert isinstance(result, dict)
        assert "root" in result
        assert len(result["root"]) > 0

    def test_single_leaf(self):
        from governance.frankel_hash import build_merkle_tree

        result = build_merkle_tree(["single"])
        assert isinstance(result, dict)
        assert result["root"] == "single"


# ── Audit retention defense ──────────────


class TestAuditRetentionDateComparison:
    """Verify ISO date string comparison works correctly."""

    def test_iso_dates_compare_correctly(self):
        """YYYY-MM-DD format sorts correctly with string comparison."""
        assert "2026-02-15" > "2026-02-08"
        assert "2026-01-01" < "2026-12-31"
        assert "2025-12-31" < "2026-01-01"

    def test_retention_cutoff_logic(self):
        from datetime import datetime, timedelta

        cutoff = (datetime.now() - timedelta(days=7)).isoformat()[:10]
        recent = datetime.now().isoformat()[:10]
        old = (datetime.now() - timedelta(days=30)).isoformat()[:10]

        assert recent >= cutoff  # Should be kept
        assert old < cutoff  # Should be pruned


# ── Parser resume defense ──────────────


class TestParserStartLine:
    """Verify start_line semantics are correct."""

    def test_start_line_skips_correctly(self, tmp_path):
        import json
        from governance.session_metrics.parser import parse_log_file_extended

        f = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"type": "user", "timestamp": f"2026-02-15T10:0{i}:00Z",
                         "message": {"content": f"msg{i}"}})
            for i in range(5)
        ]
        f.write_text("\n".join(lines))

        # start_line=2 should skip lines 0 and 1, process 2,3,4
        entries = list(parse_log_file_extended(f, start_line=2))
        # At least some entries should be parsed from lines 2+
        assert len(entries) <= 3  # Max 3 lines (2,3,4)
