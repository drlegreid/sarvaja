# GAP-UI-EXP-008: Agents Trust Score Data Mismatch

**Status:** RESOLVED
**Priority:** MEDIUM (downgraded from CRITICAL)
**Category:** data_integrity
**Discovered:** 2026-01-14 via Playwright exploratory testing
**Resolved:** 2026-01-14

## Problem Statement (CORRECTED)

Initial analysis was incorrect. The Agents view displays **correct** trust scores from the REST API. The perceived "mismatch" was between:
- REST API (calculated scores: 0.95, 0.92, 0.90, etc.) - **Used by UI**
- MCP Tool (raw TypeDB values: 0.8 for all) - **Different data source**

## Technical Details

### Architecture Explanation

Two data sources exist by design:

1. **REST API (`/api/agents`)**: Uses `_calculate_trust_score()` from `_AGENT_BASE_CONFIG`
   - task-orchestrator: base_trust=0.95
   - local-assistant: base_trust=0.92
   - rules-curator: base_trust=0.90
   - code-agent: base_trust=0.88
   - research-agent: base_trust=0.85
   - Others: default 0.8

2. **MCP Tool (`governance_list_agents`)**: Returns raw TypeDB values
   - All agents stored with trust_score=0.8 (default)

### Verified Behavior

**UI Display (via REST API):**
| Agent | Trust Score | Source |
|-------|-------------|--------|
| Task Orchestrator | 95% | config base_trust |
| Local Assistant | 92% | config base_trust |
| Rules Curator | 90% | config base_trust |
| Code Agent | 88% | config base_trust |
| Research Agent | 85% | config base_trust |
| Others | 80% | TypeDB default |

**MCP Response (via TypeDB):**
All agents: 0.8 (never synced from config)

### Root Cause

This is **working as designed**. The REST API:
1. Queries TypeDB for agent entities
2. Merges with `_AGENT_BASE_CONFIG` for base trust
3. Calculates dynamic trust using `_calculate_trust_score()`

The MCP tool returns raw TypeDB data without applying the config merge.

### Fix Applied

Fixed TypeDB query to read `trust-score` attribute (was missing):
- `governance/typedb/queries/agents.py:24-45` - Added `has trust-score $trust` to query
- `governance/typedb/queries/agents.py:47-66` - Same for get_agent()
- `governance/typedb/queries/agents.py:92-95` - Fixed delete query syntax

### Remaining Work

To fully sync data sources:
1. Option A: Run sync script to update TypeDB with config values
2. Option B: Make MCP also use `_calculate_trust_score()` logic
3. Option C: Document as "expected behavior" (different sources)

## Evidence

```bash
# REST API returns calculated scores
$ curl http://localhost:8082/api/agents | jq '.[].trust_score'
0.95
0.92
0.9
0.88
0.85
0.8
0.8
0.8

# MCP returns TypeDB raw values
governance_list_agents() → all 0.8
```

## Resolution

**UI is correct.** The perceived issue was comparing two different data sources.
Code fix applied to ensure TypeDB queries actually read the trust-score attribute.

## Related

- Rules: RULE-011 (Multi-Agent Governance), RULE-025 (Test Data Integrity)
- Files Modified: governance/typedb/queries/agents.py
- Session: SESSION-2026-01-14-GAP-EXP-008-FIX

---
*Per GAP-DOC-01-v1: Full technical details in evidence file*
