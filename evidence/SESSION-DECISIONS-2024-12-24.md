# Session Decision Audit - 2024-12-24

**Time:** ~02:15 - 03:20 UTC+02:00  
**Purpose:** Audit decisions made vs gaps left

---

## DECISION-001: Remove Opik from Stack

**Date:** 2024-12-24  
**Context:** Evaluating whether Opik (8 services) is justified for current needs

**Options Considered:**
1. **Keep Opik** - LLM tracing, experiment tracking
   - Pros: Industry standard observability
   - Cons: 8 containers, ~3GB RAM, not connected to session/memory workflow
2. **Remove Opik, build custom UI** - TypeDB or simple graph DB
   - Pros: Aligned with actual needs (session viewer, memory browser, task UI)
   - Cons: Development effort

**Decision:** Remove Opik, plan custom solution  
**Rationale:** 
- Opik is LLM observability, not session/memory management
- 8 services for features not being used
- Custom solution aligns with TypeDB R&D (upsell potential)
- Simpler stack = fewer freeze/crash issues

**Status:** IMPLEMENTED

---

## Decisions Made ✅

| Decision | Status | Evidence |
|----------|--------|----------|
| **DECISION-001: Remove Opik** | ✅ IMPLEMENTED | docker-compose.yml updated |
| Fix GAP-001 ChromaDB | ✅ RESOLVED | Inject HttpClient into `_client` |
| Fix GAP-002 Opik config | ✅ RESOLVED | OPIK_URL_OVERRIDE (now removed) |
| TypeDB for upsell | ✅ DOCUMENTED | Added to R&D backlog #15 |
| Replace Agno ChromaDb → Memory MCP | ✅ DOCUMENTED | Added to R&D backlog #16 |
| Strategic MCP analysis | ✅ DOCUMENTED | Only memory + octocode needed |
| Tests not needed for R&D | ✅ DECIDED | Health checks only |
| Doc cross-links | ✅ IMPLEMENTED | CLAUDE.md updated |

---

## Decisions PENDING ⚠️

| Topic | Question | Status |
|-------|----------|--------|
| **MCP cleanup** | Remove unused MCPs from config? | NOT DONE |
| **OctoCode MCP** | Add to mcp_config.json? | NOT DONE |
| **Ollama model** | Is gemma3:4b still downloading? | UNCHECKED |
| **Opik UI** | Is it accessible at localhost:5173? | UNCHECKED |
| **DSM batch 1401-1500** | Resume localgai work? | NOT DECIDED |
| **Memory MCP vs Agno** | When to migrate? | NOT SCHEDULED |

---

## Questions Raised But Not Answered

1. **"do we need these mcps from strategic point of view?"**
   - Answer given: Only memory + octocode
   - Action taken: None (config not cleaned)

2. **"do we need our existing tests along the way?"**
   - Answer given: Health checks only
   - Action taken: None (tests not removed/updated)

3. **"why we ain't using octocode mcp"**
   - Answer given: Was RISKY in angelgai
   - Action taken: Added to backlog, NOT installed

4. **"mcps were loaded but not using them"**
   - Answer given: Acknowledged gap
   - Action taken: Added GAP-013, no workflow change

---

## Gaps in Task System

### Problem
- Decisions logged in chat, not in task system
- No decision log in TODO.md
- Hard to track what was decided vs discussed

### Solution (RULE-006 Proposal)
Add decision logging to workflow:
```
Every session MUST log decisions in:
1. TODO.md - Add DECISION-XXX entries
2. evidence/ - SESSION-DECISIONS-{date}.md
```

---

## Action Items for Next Session

- [x] Check Ollama model status → gemma3:4b downloaded ✅
- [x] Check Opik UI accessibility → localhost:5173 returns 200 ✅
- [x] Fix LiteLLM "No connected db" error → ✅ FIXED (commit 63ee954)
- [ ] Clean up unused MCPs from config
- [ ] Add OctoCode MCP with GitHub PAT
- [x] Update gap index (GAP-001, GAP-002, GAP-003 now FIXED) ✅
- [x] Add RULE-006 for decision logging → ✅ ADDED (commit a2efccb)

### ~~Known Issue: LiteLLM DB Connection~~ ✅ FIXED
```
Original Error: {"error":{"message":"No connected db.","type":"no_db_connection"}}
Root Cause: master_key setting required DB-backed validation
Fix Applied: 
  - Disabled Opik callbacks
  - Used simple dev key (sk-litellm-dev-key)
  - Set allow_user_auth: false
Status: ✅ RESOLVED (commit 63ee954)
```

### Known Issue: Ollama Memory Constraint
```
Error: model requires more system memory (4.0 GiB) than is available (4.0 GiB)
Cause: Container memory limit exactly matches model requirement
Options:
  1. Increase container memory limit
  2. Use smaller model (gemma2:2b)
  3. Accept occasional OOM errors
```

---

*Generated to audit session decision gaps*
