"""Session Evidence MCP Tools. Per EPIC-TEST-COMPRESS-001."""
import json
from typing import Optional

from governance.mcp_tools.common import format_mcp_result

# Import summary compressor for test compression
try:
    from tests.evidence.summary_compressor import SummaryCompressor
    SUMMARY_COMPRESSOR_AVAILABLE = True
except ImportError:
    SUMMARY_COMPRESSOR_AVAILABLE = False

# Import holographic store for multi-resolution queries
try:
    from tests.evidence.holographic_store import get_global_store, HolographicTestStore
    HOLOGRAPHIC_AVAILABLE = True
except ImportError:
    HOLOGRAPHIC_AVAILABLE = False


def register_session_evidence_tools(mcp) -> None:
    """Register session evidence MCP tools."""

    @mcp.tool()
    def session_test_summary(tests_json: str, format: str = "compact") -> str:
        """Get compressed test summary. Per EPIC-TEST-COMPRESS-001.

        Args:
            tests_json: JSON array [{test_id, name, category, status, duration_ms, error}]
            format: compact (default), oneline, toon, or dict
        """
        if not SUMMARY_COMPRESSOR_AVAILABLE:
            return format_mcp_result({"error": "SummaryCompressor not available"})
        try:
            tests = json.loads(tests_json)
        except json.JSONDecodeError as e:
            return format_mcp_result({"error": f"Invalid JSON: {e}"})

        summary = SummaryCompressor().compress_test_list(tests)
        formatters = {"oneline": summary.format_oneline, "toon": summary.format_toon,
                      "dict": lambda: summary.to_dict(), "compact": summary.format_compact}
        output = formatters.get(format, summary.format_compact)()
        if format == "dict":
            return format_mcp_result(output)
        return format_mcp_result({
            "summary": output, "compression": summary.compression_ratio,
            "stats": {"total": summary.total, "passed": summary.passed,
                      "failed": summary.failed, "skipped": summary.skipped}
        })

    @mcp.tool()
    def test_evidence_push(
        test_id: str,
        name: str,
        status: str,
        category: str = "unknown",
        duration_ms: float = 0.0,
        error_message: Optional[str] = None,
        fixtures_json: Optional[str] = None,
        linked_rules: Optional[str] = None,
    ) -> str:
        """Push test evidence to holographic store. Per FH-001.

        Args:
            test_id: Unique test identifier
            name: Test name
            status: passed, failed, or skipped
            category: unit, integration, or e2e
            duration_ms: Test duration
            error_message: Error if failed
            fixtures_json: JSON with fixture/request/response data
            linked_rules: Comma-separated rule IDs
        """
        if not HOLOGRAPHIC_AVAILABLE:
            return format_mcp_result({"error": "HolographicStore not available"})

        store = get_global_store()

        fixtures = {}
        if fixtures_json:
            try:
                fixtures = json.loads(fixtures_json)
            except json.JSONDecodeError:
                fixtures = {"raw": fixtures_json}

        rules = [r.strip() for r in linked_rules.split(",")] if linked_rules else []

        evidence_hash = store.push_event(
            test_id=test_id,
            name=name,
            status=status,
            category=category,
            duration_ms=duration_ms,
            error_message=error_message,
            fixtures=fixtures,
            linked_rules=rules,
        )

        return format_mcp_result({
            "evidence_hash": evidence_hash,
            "test_id": test_id,
            "status": status,
            "store_count": store.count,
            "message": f"Evidence pushed: {evidence_hash}"
        })

    @mcp.tool()
    def test_evidence_query(
        zoom: int = 1,
        test_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """Query test evidence at specified zoom level. Per FH-001 holographic principle.

        Zoom levels:
            0: One-line summary (pass/fail count)
            1: Compact summary with failures (default)
            2: Per-test list with metadata
            3: Full detail with fixtures

        Args:
            zoom: Detail level 0-3
            test_id: Filter to specific test (substring match)
            category: Filter by category (unit, integration, e2e)
            status: Filter by status (passed, failed, skipped)
        """
        if not HOLOGRAPHIC_AVAILABLE:
            return format_mcp_result({"error": "HolographicStore not available"})

        store = get_global_store()

        if store.count == 0:
            return format_mcp_result({
                "zoom": zoom,
                "count": 0,
                "message": "No evidence in store. Push events first."
            })

        result = store.query(zoom=zoom, test_id=test_id, category=category, status=status)
        return format_mcp_result(result)

    @mcp.tool()
    def test_evidence_get(evidence_hash: str) -> str:
        """Get specific test evidence by hash. Per FH-001.

        Args:
            evidence_hash: 16-char hash from test_evidence_push
        """
        if not HOLOGRAPHIC_AVAILABLE:
            return format_mcp_result({"error": "HolographicStore not available"})

        store = get_global_store()
        evidence = store.get_by_hash(evidence_hash)

        if not evidence:
            return format_mcp_result({"error": f"Evidence not found: {evidence_hash}"})

        return format_mcp_result(evidence.to_full_dict())
