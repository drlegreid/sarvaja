# Health Check Requirements

> **Gaps:** GAP-HEALTH-001, GAP-HEALTH-002, GAP-HEALTH-003, GAP-HEALTH-004
> **Rule:** RULE-021 (MCP Healthcheck Protocol)
> **Date:** 2026-01-02

---

## GAP-HEALTH-001: Retry History and Rotation

**Current State:** `.claude/hooks/.healthcheck_state.json` stores single point-in-time status

**Issue:** No historical retry tracking; state persists indefinitely across sessions

**Required Changes:**
1. Add `retry_history[]` array to track all retry attempts with timestamps
2. Add `session_id` field to link state to Claude Code session
3. Implement rotation: Archive old state files on session end (keep last 5)
4. Add `total_retries_this_session` counter for debugging

**Implementation Path:** Modify `.claude/hooks/healthcheck.py` to:
- Append to retry_history on each check
- Detect session change (new Claude Code instance) via env or timestamp gap
- Archive previous session state to `.healthcheck_state.{timestamp}.json`
- Cap retry_history to last 100 entries to prevent unbounded growth

---

## GAP-HEALTH-002: Entropy Detection (RULE-012 DSP Trigger)

**Status:** RESOLVED 2026-01-02

**Problem:** Healthcheck doesn't detect document entropy that should trigger DEEP SLEEP mode

**Per RULE-012:** Files >300 lines, document bloat, excessive gaps should trigger DSP

**Required Checks in healthcheck.py:**
1. `check_file_entropy()` - Scan for files >300 lines in governance/, agent/, docs/
2. `check_gap_entropy()` - Count OPEN gaps, ALERT if >100 open HIGH/CRITICAL
3. `check_test_debt()` - Detect skipped tests, failing tests ratio
4. `check_rule_staleness()` - Rules without recent updates or evidence

**ALERT Thresholds:**
| Metric | Warning | Alert (DSP Trigger) |
|--------|---------|---------------------|
| Files >300 lines | 3+ | 5+ |
| OPEN HIGH/CRITICAL gaps | 20+ | 40+ |
| Test failure rate | 5% | 10% |
| Rules without evidence | 5+ | 10+ |

**Output:** Add `entropy_status` to healthcheck JSON with `needs_dsp: true/false`

---

## GAP-HEALTH-003: Stale Hash Detection

**Status:** RESOLVED 2026-01-02

**Issue:** `.claude/hooks/.healthcheck_state.json` shows stale data:
```json
{"master_hash": "DEADBEEF", "components": {"docker": "DOWN", "typedb": "DOWN", "chromadb": "DOWN"}}
```

**Reality:** Services are UP (TypeDB 1729, ChromaDB 8001 responding)

**Problem:** `unchanged_since` timestamp triggers retry ceiling, returns cached data

**Bug:** Hash doesn't change when system state changes (documents modified, etc.)

**User Principle:** "What worked now might break in next moment" - hash should reflect current reality

**Remediation:** Fixed healthcheck.py to:
1. Reset `unchanged_since` on actual state changes
2. Include document hashes in computation
3. Never return stale cached data when services are actually UP

---

## GAP-HEALTH-004: Historical Audit Trail

**Status:** RESOLVED 2026-01-02

**Problem:** Current healthcheck state is mutable and can become stale. Manual resets required. No way to know what went wrong if previous state wasn't captured.

**User Principle:** "What worked now might break in next moment" - need historical chain

**Required Capabilities:**

### 1. Immutable State Snapshots
- Each healthcheck creates NEW immutable snapshot (never overwrites)
- Previous state hash embedded in current (blockchain-style chain)
- Auto-managed by script, NO manual resets ever needed

### 2. Per-Component Hash Drill-Down
- Master hash = MERKLE_ROOT([docker_hash, typedb_hash, chromadb_hash, ...])
- Each component has own hash: `typedb_hash = SHA256(status + port + last_response)`
- When master hash changes, can drill down to see WHICH component changed

### 3. Historical Audit Trail
- `.claude/hooks/audit/` directory with dated JSONL files
- Format: `2026-01-02.jsonl` with one JSON object per line per check
- Each entry: `{timestamp, master_hash, component_hashes, prev_hash, delta}`
- Delta shows what changed from previous state

### 4. Automatic State Transitions
- Script detects state transitions automatically (e.g., DOWN→UP, UP→DOWN)
- On transition: log old state, log new state, compute delta
- Never require manual intervention to clear stale state
- `unchanged_since` resets automatically when actual state changes

### 5. AMNESIA Detection Integration
- Compare current chain with expected chain
- If chain broken (hash mismatch) → AMNESIA indicator
- Report: "State diverged at timestamp X, component Y changed"

**Proposed State File Structure:**
```json
{
  "master_hash": "A1B2C3D4",
  "prev_hash": "Z9Y8X7W6",
  "timestamp": "2026-01-02T19:45:00",
  "component_hashes": {
    "docker": {"hash": "ABCD1234", "status": "OK", "changed": false},
    "typedb": {"hash": "EFGH5678", "status": "OK", "changed": false},
    "chromadb": {"hash": "IJKL9012", "status": "OK", "changed": false}
  },
  "chain_length": 47,
  "session_start": "2026-01-02T19:00:00"
}
```

**Audit Trail Entry Format (JSONL):**
```json
{"ts":"2026-01-02T19:45:00","master":"A1B2C3D4","prev":"Z9Y8X7W6","delta":null}
{"ts":"2026-01-02T19:45:30","master":"B2C3D4E5","prev":"A1B2C3D4","delta":{"typedb":"DOWN→UP"}}
```

---

*Per RULE-021: MCP Healthcheck Protocol*
