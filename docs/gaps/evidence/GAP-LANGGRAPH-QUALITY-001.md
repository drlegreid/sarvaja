# GAP-LANGGRAPH-QUALITY-001: LangGraph Quality Workflow Enhancement

**Status:** DEFERRED | **Priority:** MEDIUM | **Type:** ENHANCEMENT
**Updated:** 2026-01-26 | **Reason:** Option C selected - keep as-is, revisit when multi-agent active

## Summary

LangGraph implementation exists but is:
1. Optional (not in requirements.txt)
2. Limited to governance proposals only
3. Not enforcing quality gates for general operations

## Current Implementation

**Location:** `governance/langgraph/` (6 files)

**Workflow:**
```
START → SUBMIT → VALIDATE → ASSESS → VOTE → DECIDE → IMPLEMENT → COMPLETE → END
```

**Quality Gates:**
1. Trust score validation (min 0.3)
2. Format validation (hypothesis, evidence, rule_id)
3. Impact assessment with risk scoring
4. Weighted voting with quorum (50%) and approval threshold (60%)
5. Rollback capability for changes

**Fallback:** When LangGraph not installed, simple sequential execution

## Enhancement Proposal

### Option A: Make LangGraph Required
- Add to requirements.txt
- Enforce graph-based execution for all governance operations

### Option B: Extend Workflow Coverage
- Create workflows for:
  - Task completion (quality gates before DONE)
  - Session closure (evidence requirements)
  - Gap creation (validation gates)

### Option C: Keep as-is (RECOMMENDED for now)
- Current fallback pattern works
- Focus on TypeDB rule quality first
- Revisit when multi-agent execution is active

## Related

- GOV-BICAM-01-v1: Multi-agent governance requires quality workflows
- RULE-011: Bicameral model with weighted voting
- RD-RULE-APPLICABILITY: Needs quality enforcement foundation

---

## Resolution (2026-01-26)

**Status:** DEFERRED

**Decision:** Option C selected - Keep as-is for now.

**Rationale:**
1. Current fallback pattern is functional and tested
2. Focus priority is on TypeDB rule quality and Robot Framework migration
3. Multi-agent execution is not yet active in production
4. Enhancement can be revisited when multi-agent workflows require it

**Trigger for Revisit:**
- When multi-agent execution becomes active
- When GOV-BICAM-01-v1 governance workflows are implemented
- When quality gate failures become frequent

---
*Per GOV-BICAM-01-v1: Multi-Agent Governance Protocol*
