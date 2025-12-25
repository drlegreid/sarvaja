# Governance Rules - Sim.ai

Rules governing process, documentation, and agent collaboration.

---

## RULE-001: Session Evidence Logging

**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

All agent sessions MUST produce evidence logs that include:

1. **Thought Chain Documentation**
   - Every decision point with rationale
   - Alternatives considered and why rejected
   - Assumptions made and their basis

2. **Artifact Tracking**
   - Files created/modified with timestamps
   - Dependencies introduced
   - Configuration changes

3. **Session Metadata**
   - Session ID, start/end times
   - Models invoked with token counts
   - Tools used with invocation counts

4. **Export Requirements**
   - Session logs exported to `./docs/SESSION-{date}-{topic}.md`
   - Machine-readable YAML metadata block
   - Human-readable narrative

### Implementation

```python
session_log = {
    "session_id": str,
    "timestamp": datetime,
    "thought_chain": [
        {"step": int, "decision": str, "rationale": str, "alternatives": list[str], "confidence": float}
    ],
    "artifacts": [
        {"path": str, "action": "create|modify|delete", "timestamp": datetime}
    ],
    "metadata": {"models": dict, "tools": dict, "tokens": int}
}
```

### Validation
- [ ] Session log exists in `./docs/`
- [ ] Contains thought chain with ≥3 decision points
- [ ] Metadata block is valid YAML
- [ ] All artifacts are tracked

---

## RULE-003: Sync Protocol for Skills & Sessions

**Category:** `governance` | **Priority:** HIGH | **Status:** DRAFT

### Directive

Local skills and sessions MUST be syncable to:
- Remote storage (optional cloud backup)
- Team shared repositories
- Cross-device continuity

See `./docs/SYNC-AGENT-DESIGN.md` for implementation.

---

## RULE-006: Decision Logging

**Category:** `governance` | **Priority:** MEDIUM | **Status:** ACTIVE

### Directive

All strategic decisions MUST be logged in task system, not just chat.

### Decision Log Format

```markdown
## DECISION-XXX: [Title]

**Date:** YYYY-MM-DD
**Context:** [Why this decision was needed]
**Options Considered:**
1. Option A - [pros/cons]
2. Option B - [pros/cons]

**Decision:** [What was decided]
**Rationale:** [Why this option]
**Action:** [What was done / to be done]
**Status:** IMPLEMENTED | PENDING | DEFERRED
```

### Validation
- [ ] Session ends with decision audit
- [ ] Major decisions have DECISION-XXX entry
- [ ] evidence/SESSION-DECISIONS-*.md exists

---

## RULE-011: Multi-Agent Governance Protocol

**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

Multi-agent systems MUST implement structured governance with human oversight, consensus mechanisms, and evidence-based conflict resolution.

### Governance Layers (Bicameral Model)

```
┌─────────────────────────────────────────────────────────────────────┐
│ UPPER CHAMBER (Human Oversight)                                      │
│ - Veto authority on rule changes                                    │
│ - Strategic steering and prioritization                             │
│ - Ambiguity resolution when AI cannot decide                        │
├─────────────────────────────────────────────────────────────────────┤
│ LOWER CHAMBER (AI Execution)                                         │
│ - Task execution from TypeDB queue                                  │
│ - Evidence collection and hypothesis testing                        │
│ - Peer review and consensus voting                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Governance MCP Tools

| Tool | Responsibility |
|------|----------------|
| `governance_propose_rule` | Submit rule changes with evidence |
| `governance_vote` | Peer review voting on proposals |
| `governance_dispute` | Raise conflicts for resolution |
| `governance_get_trust_score` | Agent reliability scoring |
| `governance_escalate_to_human` | Trigger human oversight |

### Trust Score Algorithm

```python
Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)
```

### Validation
- [ ] Governance MCP server implemented
- [ ] TypeDB schema extended
- [ ] Trust scoring operational
- [ ] Human escalation workflow tested

### R&D Optimization: Rule Quality & Decomposition

**Principle:** Heavy rules SHOULD be decomposed into smaller, composable rules following **category theory** and **functional abstraction** patterns.

#### Decomposition Triggers

| Signal | Action | Example |
|--------|--------|---------|
| Rule > 50 lines | Split by concern | `RULE-001` → `RULE-001a` (format) + `RULE-001b` (validation) |
| Collateral docs exist | Extract to separate rule | README section → standalone `RULE-XXX` |
| Multiple enforcement points | Create abstract base | `RULE-SESSION-*` family |
| Cross-cutting concern | Extract morphism | `RULE-LOGGING` applies to all |

#### Category Theory Alignment

```
┌─────────────────────────────────────────────────────────────┐
│                RULE COMPOSITION (Functorial)                 │
├─────────────────────────────────────────────────────────────┤
│  Objects: Rule entities (RULE-001, RULE-002, ...)           │
│  Morphisms: Rule relationships (extends, requires, groups)   │
│  Composition: Rule chaining (A requires B, B requires C)    │
│  Identity: Self-referential rules (meta-governance)         │
└─────────────────────────────────────────────────────────────┘

Category: Rules → Enforcement
  - map: rule_id → enforcement_function
  - compose: (check_a ∘ check_b) → combined_validation
  - identity: RULE-013 (applicability convention)
```

#### Group Theory Patterns

| Pattern | Application | Example |
|---------|-------------|---------|
| **Closure** | Rules in category stay in category | All `governance` rules compose |
| **Associativity** | Order independence | `(A ∧ B) ∧ C = A ∧ (B ∧ C)` |
| **Identity** | Neutral element | `RULE-NONE` (pass-through) |
| **Inverse** | Deprecation/rollback | `RULE-XXX-DEPRECATED` |

#### Quality Checklist (R&D Cycle)

During DSP or R&D cycles, evaluate each rule:

- [ ] **Atomic?** Rule addresses single concern
- [ ] **Composable?** Can combine with other rules cleanly
- [ ] **Abstract?** No implementation-specific details in directive
- [ ] **Collateral-free?** All related docs referenced, not duplicated
- [ ] **Testable?** Validation checklist is executable
- [ ] **Morphism-aware?** Relationships to other rules documented

#### Refactoring Workflow

```
1. IDENTIFY: Rule > 50 lines OR has collateral docs
2. EXTRACT: Split by concern into rule family (RULE-XXX-a, RULE-XXX-b)
3. COMPOSE: Define morphisms (extends, requires, groups)
4. VALIDATE: Each sub-rule passes atomic test
5. DOCUMENT: Update RULES-DIRECTIVES.md with family relationships
```

---

## RULE-013: Rules Applicability Convention

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All code comments, gaps, and TODOs MUST reference applicable governance rules using format:

```
{TYPE}({RULE-ID}): {Description}
```

### Examples

```python
# Good
# TODO(RULE-002): Extract to separate module
# FIXME(RULE-009): Version mismatch - check container version
# GAP-020(RULE-005): Memory threshold exceeded

# Bad
# TODO: Fix this later
# FIXME: This is broken
```

### Gap Format in TODO.md

```markdown
| ID | Gap | Priority | Category | Rule |
|----|-----|----------|----------|------|
| GAP-020 | Memory monitoring | HIGH | stability | RULE-005 |
```

### Validation
- [ ] All TODO comments have RULE-XXX reference
- [ ] Gaps in TODO.md have Rule column populated
- [ ] No orphan gaps in codebase

---

## RULE-018: Objective Reporting

**Category:** `reporting` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All comparisons, analyses, and recommendations MUST use **functional feature comparison** rather than subjective ratings or flattery patterns.

### Prohibited Patterns

| Pattern | Problem | Example |
|---------|---------|---------|
| Star ratings | Subjective, non-measurable | `⭐⭐⭐ vs ⭐⭐` |
| Comparative superlatives | Unfounded preference | "React is better" |
| Flattery phrasing | Non-technical bias | "You're right to choose..." |
| Vague recommendations | No functional basis | "This one feels faster" |

### Required Patterns

| Pattern | Purpose | Example |
|---------|---------|---------|
| Feature matrix | Objective capability list | `| Feature | A | B |` |
| Technical constraints | Measurable limits | "Max 10 concurrent connections" |
| Integration requirements | Concrete dependencies | "Requires Python 3.10+" |
| Build effort | Countable work items | "3 new files, 2 endpoints" |

### Functional Comparison Template

```markdown
| Feature | Option A | Option B | Option C |
|---------|----------|----------|----------|
| Protocol | REST | SSE | WebSocket |
| State sync | Polling | JSON Patch | Full refresh |
| Dependencies | 2 packages | 5 packages | 0 packages |
| Platform support | Web only | Web + Mobile | Web only |
```

### Anti-Patterns to Avoid

```markdown
# BAD: Subjective rating
| Criteria | A | B |
|----------|---|---|
| Performance | ⭐⭐⭐ | ⭐⭐ |
| Ease of use | ⭐⭐ | ⭐⭐⭐ |

# GOOD: Functional comparison
| Criteria | A | B |
|----------|---|---|
| Cold start | 120ms | 450ms |
| Bundle size | 45KB | 180KB |
```

### Validation
- [ ] No star ratings in comparison tables
- [ ] All recommendations cite functional features
- [ ] Subjective terms ("better", "easier") replaced with measurable terms
- [ ] Comparisons include "What Each Lacks" section

### Rationale

Functional comparisons enable:
1. **Reproducible decisions** - Others can verify claims
2. **Context-aware choices** - Features matter differently per use case
3. **Future-proof analysis** - Ratings become stale, features don't

---

## RULE-019: UI/UX Design Standards

**Category:** `reporting` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All user interface implementations MUST follow established design patterns and accessibility standards.

### Design Principles

| Principle | Requirement | Validation |
|-----------|-------------|------------|
| **Accessibility** | WCAG 2.1 AA compliance | Axe/Lighthouse audit |
| **Responsiveness** | Mobile-first, breakpoints defined | Device testing |
| **Consistency** | Design tokens, component library | Style guide adherence |
| **Performance** | Core Web Vitals thresholds | LCP < 2.5s, FID < 100ms, CLS < 0.1 |

### Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Component Hierarchy                   │
├─────────────────────────────────────────────────────────┤
│  Design Tokens (colors, spacing, typography)            │
│       ↓                                                 │
│  Primitives (Button, Input, Card)                       │
│       ↓                                                 │
│  Composites (Form, Modal, DataTable)                    │
│       ↓                                                 │
│  Features (TaskPanel, AgentStatus, ResultsView)         │
│       ↓                                                 │
│  Pages/Views (Dashboard, Settings, Playground)          │
└─────────────────────────────────────────────────────────┘
```

### Implementation Patterns

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Composition** | Combine primitives into features | `<TaskPanel><TaskInput/><TaskStatus/></TaskPanel>` |
| **Slots/Children** | Flexible content injection | `<Card>{children}</Card>` |
| **Controlled Components** | Form state management | `value={state}` + `onChange={handler}` |
| **Render Props** | Share behavior without inheritance | `render={(data) => <View data={data}/>}` |
| **Hooks/Composables** | Reusable stateful logic | `useAgentStatus()`, `useTaskProgress()` |

### State Management

| Scope | Pattern | Tool |
|-------|---------|------|
| **Component** | Local state | useState, ref |
| **Feature** | Lifted state | Props drilling, Context |
| **Global** | Store | Zustand, Redux, Pinia |
| **Server** | Cache | TanStack Query, SWR |
| **URL** | Router state | Search params, path |

### Required Documentation

Each UI component MUST include:

```markdown
## ComponentName

### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|

### Usage
\`\`\`tsx
<ComponentName prop="value" />
\`\`\`

### Accessibility
- Keyboard navigation: [describe]
- Screen reader: [describe]
- Focus management: [describe]

### States
- Default | Hover | Active | Disabled | Loading | Error
```

### Anti-Patterns

| Anti-Pattern | Problem | Alternative |
|--------------|---------|-------------|
| Prop drilling > 3 levels | Maintenance burden | Context or store |
| Inline styles | No consistency | Design tokens |
| Magic numbers | Unreadable | Named constants |
| God components | Untestable | Composition |
| Business logic in UI | Coupling | Hooks/services |

### Validation Checklist
- [ ] Components use design tokens (no hardcoded colors/sizes)
- [ ] All interactive elements keyboard accessible
- [ ] Loading and error states handled
- [ ] Responsive at 320px, 768px, 1024px, 1440px
- [ ] Component documentation exists
- [ ] No console errors/warnings in dev mode

### Framework-Agnostic Patterns

When building composable components (per Phase 6 research):

| Approach | Portability | Complexity |
|----------|-------------|------------|
| **Web Components** | Any framework | Medium |
| **A2UI JSON** | Any renderer | Low (declarative) |
| **Headless UI** | Bring your styles | Medium |
| **Design Tokens** | CSS/JS export | Low |

---

*Per RULE-001: Session Evidence Logging*
