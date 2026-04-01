# EPIC-PERF-JSONL-IDX-01: Indexed JSONL Streaming Design

## Problem Statement

Phase 7 of EPIC-PERF-TELEM-V1 delivered LRU parse caching + a size guard (`JSONL_MAX_SIZE_MB=200`). The size guard is a **hard wall** — sessions exceeding 200MB return ZERO parsed data. Only session metadata is returned with `truncated=true`.

- `get_session_detail()` at `cc_session_ingestion.py:219` checks file size before ANY parsing
- If exceeded, returns immediately at line 227 — entire parse+paginate pipeline skipped
- Every request at any zoom level (1, 2, 3) and any page hits the same check
- **Our largest session is 505MB** — completely opaque in dashboard
- As sessions grow (long-running agents, multi-hour coding), more will cross the threshold

### User's Question That Triggered This

> "What's the impact when the size guard is reached? Can we page further and see all the data?"

Answer: No. It's a hard wall. This EPIC exists to fix that.

## Proposed Solution: Per-Page Indexed JSONL Streaming

### Component 1: JsonlIndexer (~150 lines)
Lightweight first-pass scanner builds index per JSONL line:
- `(line_number, byte_offset, entry_type, tool_name, thinking_chars)`
- No full JSON parse — extract type + tool name via partial parse
- Handle variable-length lines, multi-byte UTF-8, truncated/corrupt entries
- Target: index 505MB in <30s

### Component 2: Index Cache + Sidecar Persistence (~100 lines)
- Keyed by file path + mtime (not session_id)
- Persisted to disk as `.jsonl.idx` sidecar files — re-indexing is rare
- In-memory LRU for hot indices
- Separate from Phase 7 SessionParseCache

### Component 3: Zoom=1 Aggregates from Index
- `tool_breakdown`: Counter over indexed tool_names, no JSON parse
- `thinking_summary`: sum of indexed thinking_chars
- Result: zoom=1 works for ANY file size with ~1MB memory

### Component 4: Zoom=2/3 Seek-Based Page Fetch (~80 lines)
- Given page=P, per_page=N: look up byte offsets from index
- Seek to byte_offset, parse only those N JSONL lines
- Memory: proportional to page size, not file size

### Component 5: Tool Latency Correlation
Options evaluated:
- **(a) Store pending tool_use_ids in index** — adds ~20 bytes per tool use. Recommended.
- (b) Two-pointer correlation pass on index — second scan matching use→result
- (c) Accept latency=None for cross-page pairs — simplest, minor data loss

### Component 6: Dual-Path Size Guard
- Files <200MB: Phase 7 full-parse + LRU cache (faster, no change)
- Files >=200MB: indexed streaming (bounded memory)
- Remove hard wall, replace with WARNING log

## Hard Problems and Doubts

1. **Aggregates still need full scan** — tool_breakdown and thinking_summary summarize the ENTIRE file. Index pass can extract tool names + thinking_chars cheaply, but still reads every byte. This is a ONE-TIME cost, cached afterward.

2. **Tool latency across pages** — tool_use at line 100 matched with tool_result at line 5000. With page-only parsing, both must be visible. Index storing pending use IDs solves this but adds complexity.

3. **Two-pass architecture** — index pass + data pass = more code paths and failure modes. Each needs its own cache, invalidation, and error handling.

4. **JSONL line variability** — can't compute byte offsets without reading. Index pass must read every byte but skips full JSON parsing.

5. **Scope: ~530 lines across 4-5 files, estimated 2-3 focused sessions.**

## Test Strategy

### T1 Unit
- JsonlIndexer: index accuracy for known JSONL fixtures
- Index cache: hit/miss, mtime invalidation, sidecar read/write
- Seek-based page fetch: correct entries for page N
- Aggregates from index match full-parse result
- Latency correlation for cross-page pairs

### T2 E2E
- GET /sessions/{large_id}/detail?zoom=1 returns tool_breakdown for >200MB session
- GET /sessions/{large_id}/tools?page=1 + ?page=100 return correct data
- Index sidecar file created after first access

### T3 Playwright
- Click 505MB session — tool calls load (not truncated)
- Navigate pages — different data per page
- No hang (memory bounded)

### Regression
- Files <200MB use Phase 7 full-parse + LRU (no regression)
- All existing test_session_parse_cache.py tests pass

## Planning Session Prompt

```
Session: sarvaja2_planning_indexed_jsonl
EPIC: EPIC-PERF-TELEM-V1 — Dashboard Performance & Observability
Context: Phase 7 delivered LRU parse caching + size guard for JSONL sessions.
The size guard (JSONL_MAX_SIZE_MB=200) is a hard wall — sessions >200MB return
zero parsed data. Our largest session is 505MB. We need indexed access so ANY
session is browsable regardless of size.

Goal: Design a new phase (Phase 9) for per-page indexed JSONL streaming.

Architecture to solve:
1. JsonlIndexer — lightweight first-pass scanner that builds an index:
   (line_number, byte_offset, entry_type, tool_name, thinking_chars)
   per JSONL line. Must handle variable-length lines, multi-byte UTF-8,
   and truncated/corrupt entries gracefully.

2. Index cache — separate from SessionParseCache. Keyed by file path + mtime.
   Persisted to disk (e.g., .jsonl.idx sidecar files) so re-indexing is rare.

3. Zoom=1 aggregates from index — tool_breakdown derived from indexed tool_names,
   thinking_summary from indexed thinking_chars. No full JSON parse needed.

4. Zoom=2/3 page fetch — seek to byte_offset for page start, parse only
   per_page entries. Return paginated tool_calls / thinking_blocks.

5. Tool latency correlation — tool_use_id → tool_result matching across pages.
   Options: (a) store pending use IDs in index, (b) two-pointer correlation pass,
   (c) accept latency=None for cross-page pairs.

6. Remove or raise the 200MB hard wall — with indexing, the size guard becomes
   a WARNING not a block.

Hard constraints:
- DOC-SIZE-01-v1 (files ≤300 lines), TDD workflow, 3-tier validation
- Must not regress Phase 7 cache behavior for files <200MB
- Peak memory for 505MB file must stay <100MB
- Index pass must complete in <30s for 505MB

Deliverables: BDD scenarios, file table, dependency graph, test strategy.
Read the plan at ~/.claude/plans/curried-stirring-spark.md for context on
existing phases and patterns.
```
