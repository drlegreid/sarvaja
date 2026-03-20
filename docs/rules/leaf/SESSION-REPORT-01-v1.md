# SESSION-REPORT-01-v1: Session ID Output at Session End

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `session`, `reporting`, `verification`, `dashboard`, `feedback-loop`

---

## Directive

Session ID MUST be output at session end for manual verification in dashboard. The `session_end()` function MUST return `session_id` and `dashboard_url` in its response. This enables the user to verify session data was persisted correctly via the dashboard UI, closing the feedback loop between automated capture and human verification.

---

## Requirements

### session_end() Response

The `session_end()` MCP tool MUST include these fields in its response:

| Field | Format | Example |
|-------|--------|---------|
| `session_id` | `SESSION-{date}-{topic}` | `SESSION-2026-03-20-QA-RULES` |
| `dashboard_url` | `http://localhost:8081/#/sessions/{id}` | Full clickable URL |
| `duration` | Human-readable | `2h 15m` |
| `status` | Session status | `COMPLETED` |

### Output Format

At session end, the following MUST be visible to the user:

```
Session: SESSION-2026-03-20-QA-RULES
Dashboard: http://localhost:8081/#/sessions/SESSION-2026-03-20-QA-RULES
Duration: 2h 15m | Status: COMPLETED
```

### Verification Flow

```
session_end() → returns session_id
  → User clicks dashboard_url
    → Verifies: session exists, duration correct, decisions logged
    → Closes feedback loop
```

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| End session silently with no ID output | Always return session_id + dashboard_url |
| Output session ID without dashboard link | Include full URL for one-click verification |
| Rely on user to search for session in dashboard | Provide direct link to the specific session |

---

## Implementation Reference

- `session_end()` in `governance/mcp_tools/mcp_server_sessions.py`
- Dashboard URL pattern: `http://localhost:8081/#/sessions/{session_id}`
- Implemented in P2-10b (2026-03-19)

---

*Per SESSION-EVID-01-v1: Session Evidence Logging*
*Per REPORT-DEC-01-v1: Decision Logging & Rationale*
