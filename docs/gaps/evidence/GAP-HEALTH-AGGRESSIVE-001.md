# GAP-HEALTH-AGGRESSIVE-001: ENV-based Aggressive Health Checks

**Created:** 2026-01-15
**Priority:** HIGH
**Category:** observability
**Status:** RESOLVED

## Problem Statement

Current AMNESIA detection is **too quiet**:
1. Detection threshold (50%) requires multiple indicators
2. Output suppressed in `format_summary` mode after first check
3. Overnight gap (~10 hours) only gives 40% confidence = NO WARNING
4. User reports: "never saw it catch amnesia"

## Proposed Solution

Add `SARVAJA_HEALTH_MODE` environment variable with three levels:

```bash
# In .bashrc or session startup
export SARVAJA_HEALTH_MODE=aggressive  # For surgery sessions
export SARVAJA_HEALTH_MODE=normal      # Default (current behavior)
export SARVAJA_HEALTH_MODE=quiet       # Minimal output
```

### Behavior by Mode

| Mode | Threshold | Output | MCP Check | AMNESIA Alert |
|------|-----------|--------|-----------|---------------|
| `quiet` | 70% | Summary only | Cached | Only on critical |
| `normal` | 50% | Summary after 30s | Every prompt | On threshold |
| `aggressive` | 25% | Always detailed | Every prompt + MCP query | Always show risk % |

### Aggressive Mode Features

1. **Lower AMNESIA threshold (25%)**
   - Overnight gap (10h) = 40% → TRIGGERS WARNING

2. **Always show detailed output**
   - Never switch to `format_summary`
   - Show all indicators even below threshold

3. **MCP memory query per prompt**
   - Call `chroma_query_documents(["sarvaja session {today}"])`
   - Alert if 0 results for today

4. **Full /health on session start**
   - Auto-run equivalent of `/health` command
   - Not just the lightweight hook check

## Implementation Plan

### Files to Modify

1. **`.claude/hooks/healthcheck.py`**
   ```python
   HEALTH_MODE = os.getenv("SARVAJA_HEALTH_MODE", "normal")

   # Adjust thresholds based on mode
   AMNESIA_THRESHOLDS = {
       "quiet": 0.70,
       "normal": 0.50,
       "aggressive": 0.25
   }
   ```

2. **`.claude/hooks/checkers/amnesia.py`**
   ```python
   def __init__(self, config=None, mode="normal"):
       self.DETECTION_THRESHOLD = {
           "quiet": 0.70,
           "normal": 0.50,
           "aggressive": 0.25
       }[mode]
   ```

3. **`.claude/hooks/healthcheck_formatters.py`**
   - Add `format_aggressive()` function
   - Show risk % even when below threshold

4. **`.claude/hooks/prompt_healthcheck.py`** (UserPromptSubmit)
   - In aggressive mode: query claude-mem for today's sessions
   - Alert on missing context

### New Features for Aggressive Mode

```python
def aggressive_amnesia_check():
    """Additional checks for aggressive mode."""
    alerts = []

    # 1. Query claude-mem for today's sessions
    today = datetime.now().strftime("%Y-%m-%d")
    result = chroma_query_documents([f"sarvaja session {today}"])
    if result["count"] == 0:
        alerts.append(f"NO_MEMORY_TODAY: No sessions found for {today}")

    # 2. Check TODO.md freshness
    todo_mtime = os.path.getmtime("TODO.md")
    if time.time() - todo_mtime > 86400:  # >24h old
        alerts.append("STALE_TODO: TODO.md not updated in 24h")

    # 3. Check for uncommitted changes
    git_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True)
    if len(git_status.stdout.splitlines()) > 20:
        alerts.append(f"LARGE_UNCOMMITTED: {len(git_status.stdout.splitlines())} files")

    return alerts
```

## Usage Examples

```bash
# Before surgery session
export SARVAJA_HEALTH_MODE=aggressive
claude

# Normal development
unset SARVAJA_HEALTH_MODE  # or export SARVAJA_HEALTH_MODE=normal
claude

# Quick question (minimal overhead)
SARVAJA_HEALTH_MODE=quiet claude -p "what is X?"
```

## Expected Output (Aggressive Mode)

```
=== MCP DEPENDENCY CHAIN [Hash: 35E520E7] ===

Core Services:
  [OK] PODMAN: 5 containers [6BB4]
  [OK] TYPEDB: localhost:1729 [98B5]
  [OK] CHROMADB: localhost:8001 [26FC]

AMNESIA Risk: 40% (below threshold but SHOWING in aggressive mode)
  Indicators: LONG_GAP_10h

Today's Memory: 0 sessions found
  [!] First session today - context may need refresh

Recovery Suggestions:
  - Run /remember sarvaja if context unclear
  - Check TODO.md for current tasks
```

## Acceptance Criteria

- [x] ENV variable `SARVAJA_HEALTH_MODE` recognized
- [x] Three modes with different thresholds
- [x] Aggressive mode always shows detailed output
- [ ] Aggressive mode queries claude-mem per prompt (future enhancement)
- [x] Unit tests for each mode (13 tests in `tests/test_health_modes.py`)
- [x] Documentation in CLAUDE.md (via hooks system)

## Verification Evidence (2026-01-15)

```bash
$ PYTHONPATH=.claude python -c "import os; ..."

Mode: quiet -> Threshold: 0.7, AlwaysDetailed: False
Mode: normal -> Threshold: 0.5, AlwaysDetailed: False
Mode: aggressive -> Threshold: 0.25, AlwaysDetailed: True
```

**Files Modified:**
- `.claude/hooks/healthcheck.py`:
  - Added `HEALTH_MODE`, `HEALTH_MODE_THRESHOLDS`, `AMNESIA_THRESHOLD` config (lines 137-145)
  - Modified `check_amnesia_indicators()` to use configurable threshold
  - Modified output logic to always use detailed mode in aggressive mode

## Related

- RECOVER-AMNES-01-v1: AMNESIA Recovery Protocol
- SAFETY-HEALTH-01-v1: Health Check Requirements
- GAP-HEALTH-003: Always check current state
- GAP-HEALTH-004: Per-component hashes
