# TASK-EPIC-01-v1: EPIC-Driven Task Comprehension

| Field | Value |
|-------|-------|
| **Category** | Governance |
| **Priority** | CRITICAL |
| **Status** | ACTIVE |
| **Created** | 2026-02-14 |

## Directive

All tasks MUST be comprehended within the context of **EPICs, domains, and actions/concerns**. Isolated task items without EPIC context are prohibited.

## Requirements

### 1. EPIC Framing (MANDATORY)

When identifying remaining work, gaps, or next steps:

1. **Frame within an EPIC** — or create a new one if none exists
2. **Specify domain(s)** affected (e.g., testing, governance, UI, infrastructure)
3. **Define concrete actions** with acceptance criteria
4. **Cross-reference** related rules, gaps, and evidence

### 2. Session Handoff Format (MANDATORY)

Session reports MUST express remaining work as structured EPIC references:

**WRONG:**
> "The remaining gap is integration + visual (Tier 2 & 3) testing per TEST-E2E-01-v1."

**CORRECT:**
> **EPIC-TESTING-E2E: Data Flow Verification Pipeline**
> - **Domain:** Testing (Tier 2 Integration + Tier 3 Visual)
> - **Rule:** TEST-E2E-01-v1
> - **Tasks:**
>   - T1: API integration tests for session endpoints (curl + assertions)
>   - T2: API integration tests for task/rule endpoints
>   - T3: Playwright visual verification for dashboard views
>   - T4: Playwright visual verification for session detail
> - **Acceptance:** All changed data flows verified at 3 tiers
> - **Evidence:** Test results in `evidence/test-results/`

### 3. Task Hierarchy (MANDATORY)

```
Strategic Plan
  └── EPIC (initiative with clear goal)
       └── Domain (system area: testing, UI, infra, governance)
            └── Action (concrete deliverable with acceptance criteria)
                 └── Concern (risk, dependency, or constraint)
```

### 4. Backlog Items

Every backlog item (gap, task, R&D) MUST have:
- Parent EPIC reference (or be promoted to EPIC if standalone)
- Domain classification
- At least one acceptance criterion

## Rationale

Loose task descriptions lose context across session boundaries and compactions. EPIC framing preserves strategic intent, enables prioritization across domains, and ensures handoffs carry enough context for autonomous continuation.

---

*Per WORKFLOW-AUTO-02-v1: Autonomous task continuation requires structured context.*
*Per RECOVER-AMNES-01-v1: EPIC structure survives compaction and enables recovery.*
