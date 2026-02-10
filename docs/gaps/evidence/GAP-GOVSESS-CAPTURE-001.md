# GAP-GOVSESS-CAPTURE-001: Gov-Sessions Not Capturing Live Sessions

**Date:** 2026-02-09 | **Priority:** CRITICAL | **Status:** OPEN

## Problem

Gov-sessions MCP tools exist and work, but **no live Claude Code sessions are being captured**. The last real session recorded was SESSION-2026-01-30-45A2EB (a test session). Despite active development sessions on Jan 14, 21, 24, Feb 8, and Feb 9, gov-sessions has zero records.

## Evidence: Session Duration Analysis

### All 18 Sessions in Gov-Sessions

| Session ID | Duration (h) | Type | Agent | Notes |
|-----------|-------------|------|-------|-------|
| SESSION-2026-01-30-45A2EB | 0.0 | Live test | claude-code-test | Only session with agent_id |
| SESSION-2024-12-24-001 | 9.0 | Original | - | Realistic |
| SESSION-2024-12-24-002 | 8.0 | Original | - | Realistic |
| SESSION-2024-12-25-001 | 13.0 | Original | - | Realistic |
| SESSION-2024-12-25-002 | 6.0 | Original | - | Realistic |
| SESSION-2024-12-26-001 | 9659.6 | Original | - | Broken: end_time overwritten |
| 11x Backfilled sessions | 330.5 each | Backfill | - | All identical timestamps |

### Sessions in ChromaDB (claude-mem) NOT in Gov-Sessions

| ChromaDB Session | Date | Topic |
|-----------------|------|-------|
| SESSION-2026-01-14-SARVAJA-RENAME-COMPLETE | 2026-01-14 | Project rename |
| SESSION-2026-01-14-SARVAJA-MIGRATION | 2026-01-14 | Migration |
| SESSION-2026-01-21-QA-REVIEW | 2026-01-21 | QA review |
| SESSION-2026-01-24-APPLICABILITY-BUGFIX | 2026-01-24 | Bug fix |
| SESSION-2026-02-08-QUALITY-HEURISTICS | 2026-02-08 | Heuristic fixes |

## Root Cause

No **session bridge** exists between Claude Code operations and gov-sessions MCP. The plan (EPIC-A.2) calls for a `session_bridge.py` that:
1. Creates a SessionCollector on chat/command start
2. Records tool calls via `session_tool_call`
3. Records thoughts via `session_thought`
4. Ends session with evidence on completion

Without this bridge, gov-sessions is a static archive with only seed/backfill data.

## Related Gaps

| Gap ID | Issue |
|--------|-------|
| GAP-GOVSESS-TIMESTAMP-001 | Backfilled sessions have artificial timestamps |
| GAP-GOVSESS-AGENT-001 | 17/18 sessions lack agent_id |
| GAP-GOVSESS-DURATION-001 | SESSION-2024-12-26-001 shows 9659.6h |
| GAP-MCP-001 | Original gov-sessions integration gap (RESOLVED) |

## Fix: Plan EPIC-A.2 (Session Bridge)

File: `governance/routes/chat/session_bridge.py` (new, <200 lines)
- `start_chat_session(agent_id, topic)` → creates SessionCollector
- `record_chat_tool_call(collector, tool, args, result, duration_ms)`
- `record_chat_thought(collector, thought, type)`
- `end_chat_session(collector)` → syncs to TypeDB + ChromaDB

Integration point: `governance/routes/chat/endpoints.py:send_chat_message()` (line 141)

## Impact

- All governance metrics are based on stale/artificial data
- Agent-session linking impossible (no live sessions)
- Heuristic checks (H-SESSION-*) effectively disabled (all sessions are backfilled → SKIP)
- Dashboard sessions view shows only historical data
