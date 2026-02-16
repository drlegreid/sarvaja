"""Tool call correlation: tool_use → tool_result join (GAP-SESSION-METRICS-CORRELATION).

Matches tool_use blocks (in assistant entries) with their corresponding
tool_result blocks (in subsequent user entries) by tool_use_id.
Calculates per-call latency and provides server attribution via mcpMeta.
"""

from __future__ import annotations

from collections import defaultdict

from governance.session_metrics.models import CorrelatedToolCall, ParsedEntry


def correlate_tool_calls(entries: list[ParsedEntry]) -> list[CorrelatedToolCall]:
    """Join tool_use entries with their tool_result entries by ID.

    Builds a lookup of tool_use_id → (tool_name, is_mcp, timestamp) from
    assistant entries, then matches against tool_result blocks in subsequent
    entries.

    Args:
        entries: Parsed log entries in chronological order.

    Returns:
        List of correlated tool calls with latency measurements.
    """
    # Build tool_use index: id → (name, is_mcp, timestamp)
    use_index: dict[str, tuple[str, bool, object]] = {}
    for entry in entries:
        for tu in entry.tool_uses:
            # Extract tool_use_id from the content block
            # ToolUseInfo doesn't store id, so we need to find it from
            # the entry context. The id is set per tool_use block.
            pass

    # We need tool_use IDs. Let's build from raw data by scanning
    # tool_uses alongside their parent entries.
    # Since ToolUseInfo doesn't have the id field, we need to
    # re-extract from the entry's tool_uses with position tracking.
    #
    # Better approach: scan all entries, build use_index from
    # tool_use blocks that have IDs embedded in content.
    # But ToolUseInfo.from_content_block doesn't store id...
    # We need to enhance this. For now, let's use a different strategy:
    # look at the raw content to get IDs.
    #
    # Actually, let's just add tool_use_id to ToolUseInfo. But that
    # would change the existing model. Instead, let's build the index
    # by scanning entries that have tool_uses, and extracting the id
    # from the content blocks directly... but we don't have raw content
    # in ParsedEntry.
    #
    # The cleanest fix: add tool_use_id to ToolUseInfo.

    # Since we enhanced ToolUseInfo with tool_use_id, use it directly:
    use_index = {}
    for entry in entries:
        for tu in entry.tool_uses:
            if tu.tool_use_id:
                use_index[tu.tool_use_id] = (tu.name, tu.is_mcp, entry.timestamp)

    # Match tool_results to tool_uses
    correlated = []
    for entry in entries:
        for tr in entry.tool_results:
            if tr.tool_use_id in use_index:
                tool_name, is_mcp, use_ts = use_index[tr.tool_use_id]
                delta = entry.timestamp - use_ts
                latency_ms = int(delta.total_seconds() * 1000)
                correlated.append(CorrelatedToolCall(
                    tool_use_id=tr.tool_use_id,
                    tool_name=tool_name,
                    is_mcp=is_mcp,
                    use_timestamp=use_ts,
                    result_timestamp=entry.timestamp,
                    latency_ms=latency_ms,
                    server_name=tr.server_name,
                ))

    return correlated


def summarize_correlation(correlated: list[CorrelatedToolCall]) -> dict:
    """Aggregate correlation statistics.

    Returns:
        Dict with total_correlated, avg_latency_ms, mcp_avg_latency_ms,
        per_server breakdown, per_tool breakdown.
    """
    if not correlated:
        return {
            "total_correlated": 0,
            "avg_latency_ms": 0,
            "mcp_avg_latency_ms": 0,
            "per_server": {},
            "per_tool": {},
        }

    total = len(correlated)
    avg_latency = sum(c.latency_ms for c in correlated) // total

    mcp_calls = [c for c in correlated if c.is_mcp]
    mcp_avg = (sum(c.latency_ms for c in mcp_calls) // len(mcp_calls)
               if mcp_calls else 0)

    # Per-server breakdown
    server_groups: dict[str, list[int]] = defaultdict(list)
    for c in correlated:
        if c.server_name:
            server_groups[c.server_name].append(c.latency_ms)

    per_server = {}
    for server, latencies in server_groups.items():
        # BUG-CORR-001: Guard against empty latency lists
        if not latencies:
            continue
        per_server[server] = {
            "count": len(latencies),
            "avg_latency_ms": sum(latencies) // len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
        }

    # Per-tool breakdown
    tool_groups: dict[str, list[int]] = defaultdict(list)
    for c in correlated:
        tool_groups[c.tool_name].append(c.latency_ms)

    per_tool = {}
    for tool, latencies in tool_groups.items():
        # BUG-CORR-001: Guard against empty latency lists
        if not latencies:
            continue
        per_tool[tool] = {
            "count": len(latencies),
            "avg_latency_ms": sum(latencies) // len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
        }

    return {
        "total_correlated": total,
        "avg_latency_ms": avg_latency,
        "mcp_avg_latency_ms": mcp_avg,
        "per_server": per_server,
        "per_tool": per_tool,
    }
