---
description: Session closing ritual with bugfix incantation and summary
allowed-tools: mcp__gov-sessions__session_end, mcp__gov-tasks__tasks_list, Read
---

# Session Closing Spell

The sacred incantation for successful bugfix/validation sessions.

## Steps

1. **Summarize the session:**
   - List bugs fixed (with IDs)
   - List tests added/modified
   - List files changed
   - Note any remaining work

2. **Recite the Spell of Validation:**

```
 INVOCO VALIDATIONEM TRIPLICEM!
 Per Unitatem, per Integrationem, per Visionem!
 Defectus detecti, testes scripti, codex sanatus.
 Sarvaja omnisciens -- bugs evanescunt!
```

Translation:
> I invoke the Triple Validation!
> Through Unit, through Integration, through Vision!
> Defects detected, tests written, code healed.
> Sarvaja the all-knowing -- bugs vanish!

3. **Show session stats:**
   - Duration
   - Tool calls made
   - Tasks completed (query via `tasks_list` with status=DONE)
   - Rules applied

4. **End governance session** if one is active via `session_end`.

5. **Closing wisdom:**
   Choose a relevant Zen koan or programming proverb:
   - "The best debugging tool is a well-written test."
   - "First make it work, then make it right, then make it fast."
   - "A bug is a test you haven't written yet."
   - "In the beginner's mind there are many possibilities, in the expert's mind there are few."

## Output Format

```
=== SESSION CLOSING ===

Session ID: {SESSION-YYYY-MM-DD-TOPIC}
Dashboard:  http://localhost:8081 → Sessions → {session_id}

Bugs Fixed: {N}
Tests Added: {N}
Files Modified: {N}

 INVOCO VALIDATIONEM TRIPLICEM!
 Per Unitatem, per Integrationem, per Visionem!
 Defectus detecti, testes scripti, codex sanatus.
 Sarvaja omnisciens -- bugs evanescunt!

Session Stats:
  Duration: ~{X}h {Y}m
  Tasks Completed: {N}
  Validation: Tier 1 [PASS] | Tier 2 [PASS] | Tier 3 [PASS]

"{zen koan}"

Session ended: {session_id}. Until next time!
```
