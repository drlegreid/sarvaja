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
            if tu.tool_use_id:
                use_index[tu.tool_use_id] = (tu.name, tu.is_mcp, entry.timestamp)

    # Match tool_results to tool_uses
    # BUG-278-CORR-001: Pop matched entries to prevent duplicate correlations on retry
    correlated = []
    for entry in entries:
        for tr in entry.tool_results:
            if not tr.tool_use_id or tr.tool_use_id not in use_index:
                continue
            tool_name, is_mcp, use_ts = use_index.pop(tr.tool_use_id)
            # BUG-267-CORR-001: Guard against mixed timezone (aware vs naive) TypeError
            try:
                delta = entry.timestamp - use_ts
            except TypeError:
                delta = None
            if delta is None:
                latency_ms = 0
            else:
                # BUG-183-007: Guard against negative latency from out-of-order entries
                latency_ms = max(0, int(delta.total_seconds() * 1000))
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
