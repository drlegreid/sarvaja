# GAP-DSP-NOTIFY-001: DSP Notifications Not Prominent

**Priority:** HIGH | **Category:** ux/observability | **Status:** RESOLVED
**Discovered:** 2026-01-20 | **Source:** Session audit
**User Directive:** 2026-01-20 - MUST block session + dashboard alert
**Resolution:** 2026-01-20 - All 5 criteria implemented (DSP Session)

---

## Problem Statement

The DSP (Deep Sleep Protocol) detection logic exists and works correctly. However, when DSP is suggested, the notification is buried in JSON health check output and not surfaced prominently to the user.

**Current State:**
- Detection: `_detect_document_entropy()` in `governance/mcp_tools/decisions.py:204-270`
- Triggers: Gap entropy >50, Large files >300 lines, DSM >7 days old, Evidence >20 files
- Output: Sets `action_required: DSP_SUGGESTED` in health check response
- **Problem:** User must manually read health check JSON to see the hint

**Issues Identified:**
1. **Not prominent** - DSP hint buried in JSON response
2. **No blocking** - Session continues regardless of entropy state
3. **No separate alert channel** - Dashboard doesn't show DSP status

---

## User Requirements (2026-01-20)

> DSP should prompt user explicitly to make DEEP SLEEP protocol - **block the session** + add **separate alert to dashboard**. Ensure we capture this in rules.

---

## Evidence (2026-01-20 Session)

```yaml
action_required: DSP_SUGGESTED
entropy_alerts[3]:
  - "Large files detected (>300 lines): workflow_compliance.py:653"
  - "No DSP cycle in 9 days (threshold: 7)"
  - "Evidence accumulation: 21 session files"
dsp_hint: Document entropy high. Consider running DSP cycle (RULE-012)
```

3/4 entropy signals fired, but no prominent notification was shown.

---

## Required Solutions (Per User Directive)

| Component | Description | Complexity |
|-----------|-------------|------------|
| **1. Session Blocking** | When DSP_SUGGESTED, prompt user with explicit choice: run DSP or override | MEDIUM |
| **2. Dashboard Alert** | Dedicated DSP alert card in Infrastructure Health UI (not buried in status) | MEDIUM |
| **3. Rule Creation** | Create SESSION-DSP-01-v1 rule codifying blocking behavior | LOW |

### Implementation Details

**1. Session Blocking (`healthcheck.py`):**
```python
if action_required == "DSP_SUGGESTED":
    print("[DSP REQUIRED] Document entropy high.")
    print("Run /deep-sleep or explicitly override to continue.")
    # Return blocking status for Claude Code to handle
```

**2. Dashboard Alert (`infra_view.py`):**
- Dedicated `VAlert` component with type="warning"
- Shows when `action_required == "DSP_SUGGESTED"`
- One-click button to initiate DSP cycle

**3. Rule Content:**
```markdown
# SESSION-DSP-01-v1: Deep Sleep Protocol Prompting

When document entropy triggers DSP_SUGGESTED:
1. Session MUST prompt user explicitly
2. Dashboard MUST show dedicated alert
3. User can override with explicit confirmation
```

---

## Acceptance Criteria

1. [x] When DSP is suggested, session **blocks** with explicit prompt - **healthcheck_formatters.py**
2. [x] User must explicitly choose: run DSP or override - **OVERRIDE keyword documented**
3. [x] Dashboard shows dedicated DSP alert card (not buried in JSON) - **infra_view.py build_dsp_alert()**
4. [x] Rule SESSION-DSP-NOTIFY-01-v1 created and synced to TypeDB - **Active in TypeDB**
5. [x] `/deep-sleep` command available for quick DSP initiation - **.claude/commands/deep-sleep.md**

## Implementation (2026-01-20)

**Files Modified:**
- `docs/rules/leaf/SESSION-DSP-NOTIFY-01-v1.md` - Rule created
- `.claude/hooks/healthcheck_formatters.py` - DSP detection + prominent box notification
- `agent/governance_ui/views/infra_view.py` - VAlert with DSP status
- `agent/governance_ui/controllers/data_loaders.py` - DSP state population
- `.claude/commands/deep-sleep.md` - Quick DSP initiation command (2026-01-20 DSP Session)

**TypeDB Rule:** SESSION-DSP-NOTIFY-01-v1 (ACTIVE, HIGH priority)

---

## Related

- RULE-012 (SESSION-DSM-01-v1): Deep Sleep Protocol
- GAP-INFRA-HEALTH-UI: Infrastructure Health UI integration
- GAP-MONITOR-IPC-001: Event bridging for UI

---

*Per GOV-TRANSP-01-v1: Task logged with full scope definition*
