# RD-RULE-APPLICABILITY: Rule Enforcement Level Classification

**Status:** ✅ COMPLETE | **Priority:** HIGH | **Author:** Claude | **Date:** 2026-01-24

> **Phase 1 COMPLETE:** Schema extended, 36 rules classified (15 MANDATORY, 4 CONDITIONAL, 17 RECOMMENDED)
> **Phase 2 COMPLETE:** MCP tools updated (`rules_query`, `wisdom_get`, `rule_create` accept applicability)
> **Phase 3 COMPLETE:** Hooks checker + REST API + MCP return applicability (MCP needs restart)

## Problem Statement

Rules currently have `priority` (CRITICAL/HIGH/MEDIUM/LOW) but no **enforcement level** indicating whether compliance is mandatory, recommended, forbidden, or conditional.

Without this, agents cannot:
1. Distinguish must-do from should-do rules
2. Identify forbidden actions vs. discouraged ones
3. Apply context-dependent rules correctly

## Proposed Solution: `applicability` Meta-Parameter

### Schema Addition

```typeql
# TypeDB Schema Extension
applicability sub attribute, value string;

rule owns applicability;

# Valid values: MANDATORY, RECOMMENDED, FORBIDDEN, CONDITIONAL
```

### Applicability Levels

| Level | Description | Enforcement | Example |
|-------|-------------|-------------|---------|
| **MANDATORY** | MUST follow - no exceptions | Blocking | SESSION-EVID-01-v1 (evidence logging) |
| **RECOMMENDED** | SHOULD follow - best practice | Warning | DOC-SOURCE-01-v1 (official docs first) |
| **FORBIDDEN** | MUST NOT do | Blocking | SAFETY-DESTR-01-v1 (no `rm -rf /`) |
| **CONDITIONAL** | Depends on context | Gated | WORKFLOW-RD-02-v1 (human approval for budget) |

### Rule Document Format

```markdown
# SESSION-EVID-01-v1: Session Evidence Logging

**Category:** governance | **Priority:** CRITICAL | **Applicability:** MANDATORY

> Directive: Every session MUST create evidence log...
```

### Classification (Implemented 2026-01-24)

**MANDATORY Rules (15 - must comply):**
- SESSION-EVID-01-v1, GOV-BICAM-01-v1, SAFETY-HEALTH-02-v1, RECOVER-AMNES-02-v1
- ARCH-VERSION-01-v1, GOV-RULE-01-v1, ARCH-INFRA-02-v1
- CONTAINER-TYPEDB-01-v1, CONTAINER-LIFECYCLE-01-v1, WORKFLOW-SHELL-01-v1
- META-TAXON-01-v1, TASK-LIFE-01-v1, TASK-VALID-01-v1
- ARCH-EBMSF-01-v1, ARCH-MCP-02-v1

**CONDITIONAL Rules (4 - context-dependent):**
- WORKFLOW-AUTO-02-v1 - Autonomous sequencing (unless HALT)
- WORKFLOW-RD-02-v1 - R&D human approval (when budget/architecture impacted)
- SESSION-DSP-NOTIFY-01-v1 - DSP prompting (when entropy high)
- SESSION-DSM-01-v1 - Deep sleep protocol (when backlog hygiene needed)

**RECOMMENDED Rules (17 - should comply):**
- DOC-SOURCE-01-v1, CONTEXT-SAVE-01-v1, GAP-DOC-01-v1, PKG-LATEST-01-v1
- UI-NAV-01-v1, RECOVER-MEM-01-v1, GOV-TRUST-01-v1, GOV-PROP-01-v1
- UI-TRAME-01-v1, UI-LOADER-01-v1, UI-TRACE-01-v1, TASK-TECH-01-v1
- REPORT-OBJ-01-v1, UI-DESIGN-02-v1, DOC-GAP-ARCHIVE-01-v1
- GOV-AUDIT-01-v1, REPORT-EXEC-01-v1

**FORBIDDEN Rules (0 - to be added):**
- *No FORBIDDEN rules implemented yet - consider adding SAFETY-DESTR-01-v1*

## Implementation Plan

### Phase 1: Schema & Data (1 session) ✅ COMPLETE
- [x] Add `applicability` attribute to TypeDB schema
- [x] Update 36 existing rules with applicability values
- [ ] Update rule markdown documents (deferred to Phase 2)

### Phase 2: MCP Integration (1 session) ✅ COMPLETE
- [x] Add `applicability` filter to `rules_query`
- [x] Add `wisdom_get` to filter rules by applicability
- [x] Add validation in `rule_create` for applicability

### Phase 3: Agent Enforcement (1 session) ✅ COMPLETE
- [x] Create `checkers/rule_applicability.py` module
- [x] Hook into `healthcheck.py` (SessionStart event)
- [x] Check MANDATORY rules (service health, python3 usage)
- [x] Block FORBIDDEN actions (destructive commands, secret exposure)
- [x] Context gates for CONDITIONAL rules (halt, entropy, budget)
- [x] Add applicability to RuleResponse model and REST API routes
- [x] Fix TypeDB query to return applicability from get_all_rules/get_active_rules
- [ ] Add warnings for RECOMMENDED violations (future enhancement)

**Note:** MCP servers need restart to pick up the code changes. Verified REST API returns applicability for all 36 rules.

## Holographic Memory Integration

This aligns with the holographic memory principle:

```
L0: CLAUDE.md
    └── Core directives (MANDATORY only, ~10 rules)

L1: TypeDB (via MCP)
    └── Full rule catalog with applicability filter

L2: docs/rules/*.md
    └── Detailed rule documentation with examples
```

CLAUDE.md should only list MANDATORY rules to keep it concise.

## Decision Required

1. Approve `applicability` schema addition?
2. Approve proposed rule classifications?
3. Priority vs. other work?

---
*Per META-TAXON-01-v1: Rule taxonomy management*
