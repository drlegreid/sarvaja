# SESSION-DSP-NOTIFY-01-v1: DSP Prompting and Blocking

**Category:** `workflow` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **GAP:** GAP-DSP-NOTIFY-001
> **Location:** [RULES-WORKFLOW.md](../operational/RULES-WORKFLOW.md)
> **Tags:** `dsp`, `notification`, `blocking`, `ux`

---

## Directive

When document entropy triggers DSP_SUGGESTED, the session MUST prompt the user explicitly. User can choose to run DSP or override with confirmation.

---

## Trigger Conditions

DSP_SUGGESTED is triggered when ANY of these conditions are met:

| Condition | Threshold | Rationale |
|-----------|-----------|-----------|
| Gap entropy | >50 open gaps | Backlog overwhelm |
| Large files | >300 lines | Code hygiene debt |
| DSM age | >7 days since last DSP | Maintenance overdue |
| Evidence files | >20 session files | Documentation sprawl |

---

## Required Behavior

### 1. Session Blocking

When `action_required == "DSP_SUGGESTED"`:

```
[DSP REQUIRED] Document entropy high.
Entropy alerts:
  - Large files detected (>300 lines)
  - No DSP cycle in 9 days
  - Evidence accumulation: 21 files

Options:
  1. Run /deep-sleep to initiate DSP cycle
  2. Type OVERRIDE to continue without DSP
```

### 2. Dashboard Alert

Dashboard Infrastructure Health view MUST show:
- Dedicated VAlert component (type="warning")
- Not buried in JSON health output
- One-click button to view DSP status

### 3. User Override

User may bypass DSP requirement by:
- Explicitly typing "OVERRIDE" or "CONTINUE"
- Override is logged for audit trail

---

## Implementation

**Health Check Hook:** `.claude/hooks/healthcheck.py`
- Check for `action_required == "DSP_SUGGESTED"`
- Return blocking message if triggered
- Accept OVERRIDE keyword

**Dashboard Component:** `agent/governance_ui/views/infra_view.py`
- Add VAlert when DSP suggested
- Link to DSP documentation

---

## Audit Trail

All DSP notifications and overrides are logged:
- Notification timestamp
- User response (DSP initiated / overridden)
- Entropy state at time of notification

---

*Per SESSION-DSM-01-v1: Deep Sleep Protocol*
*Per GOV-CONSULT-01-v1: User consultation on priority decisions*
