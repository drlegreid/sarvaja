# GOV-BIND-01-v1: Rule-to-Tool Binding

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL
**Created:** 2026-01-29

> **Tags:** `governance`, `enforcement`, `mcp`, `binding`, `traceability`

---

## Directive

Every rule that mandates a verification action MUST bind to a specific tool call. Rules that describe intent without naming the executable tool are advisory, not enforceable.

---

## Problem Statement

Rules written as intent ("verify visually", "test endpoint", "check health") fail to trigger agent action because:

1. **Ambiguity** — "verify visually" could mean screenshot, manual check, or nothing
2. **No enforcement path** — without a tool name, no hook or audit can verify compliance
3. **Silent skipping** — agents follow the letter (write tests) but skip the spirit (live verification) because no specific tool was named

**Evidence**: GAP-UI-048 and GAP-SESSION-METRICS-UI both passed all unit tests but were never verified with the available MCP tools (`rest-api`, `playwright`). The rules said "verify" without saying "call `mcp__playwright__browser_snapshot()`".

---

## Binding Requirements

### Level 1: Tool-Bound Rule (REQUIRED for HIGH/CRITICAL rules)

Every HIGH or CRITICAL rule that requires an action MUST include a **Tool Bindings** section:

```markdown
## Tool Bindings

| Action | Tool | Example Call |
|--------|------|-------------|
| Verify API | `mcp__rest-api__test_request` | `test_request("GET", "/api/endpoint")` |
| Verify UI | `mcp__playwright__browser_snapshot` | `browser_snapshot()` |
| Save context | `mcp__claude-mem__chroma_save_session_context` | `chroma_save_session_context(...)` |
```

### Level 2: Verification Gate (REQUIRED for rules governing feature completion)

Rules that gate feature completion (marking RESOLVED/DONE) MUST include a decision tree:

```
Condition met?
├── YES → Tool X called? → PASS / BLOCK
└── NO  → Skip
```

### Level 3: Audit Trail (RECOMMENDED)

Tool calls triggered by rules SHOULD be traceable:
- API calls logged via `add_api_trace()`
- MCP calls logged via session evidence
- Screenshots saved as evidence artifacts

---

## Binding Checklist for Rule Authors

When writing or updating a rule, verify:

| Check | Question | Pass |
|-------|----------|------|
| Named tool | Does the rule name a specific MCP tool or CLI command? | Tool name appears in rule text |
| Example call | Does the rule show HOW to call the tool? | Example with parameters shown |
| Gate condition | Does the rule define WHEN the tool must be called? | Trigger condition documented |
| Skip policy | Does the rule say what happens if the tool is unavailable? | BLOCK or document as blocked |
| Evidence | Does the rule say what output proves compliance? | Expected output described |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| "Verify the feature works" | "Call `mcp__playwright__browser_snapshot()` and confirm element exists" |
| "Test the endpoint" | "Call `mcp__rest-api__test_request('GET', '/api/path')` and confirm 200" |
| "Check health" | "Call `health_check()` and confirm all services UP" |
| "Save context before risk" | "Call `chroma_save_session_context(session_id, summary, ...)` " |
| Write rules with only process descriptions | Include Tool Bindings table with exact tool names |
| Assume agents will infer which tool to use | Name the tool explicitly — agents follow what's written |

---

## Rules Updated Per This Directive

| Rule | Before | After |
|------|--------|-------|
| ARCH-MCP-01-v1 | Listed stale MCPs, no verification gate | 7-server inventory, verification gate with tool bindings |
| TEST-UI-VERIFY-01-v1 | "Screenshot/Snapshot" (no tool named) | `mcp__playwright__browser_snapshot()` explicitly named |

---

## Validation

- [ ] Every HIGH/CRITICAL rule has a Tool Bindings section
- [ ] Feature-completion rules have verification gates
- [ ] Rule audits check for unbound directives (intent without tool)
- [ ] New rules pass the Binding Checklist before activation

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per ARCH-MCP-01-v1: MCP Usage Protocol*
