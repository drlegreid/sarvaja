# Rules Governance Audit - 2026-01-17

**Auditor:** Claude Code | **Status:** RESOLVED
**Triggered by:** User feedback - "we always forget some of them along the way"

---

## Executive Summary

| Source | Before | After | Status |
|--------|--------|-------|--------|
| TypeDB | 52 | **58** | +6 synced from markdown |
| RULES-DIRECTIVES.md | 41 | **55** | +14 rules documented |
| Markdown leaf files | 49 | 49 | All synced |

**Resolution:** Rules synchronized between TypeDB, markdown, and index

---

## Actions Completed

1. **RULES-DIRECTIVES.md updated** - Added 21 missing rules to index
2. **TypeDB synced** - Added 6 markdown-only rules:
   - TASK-TECH-01-v1
   - TASK-LIFE-01-v1
   - UI-LOADER-01-v1
   - UI-TRACE-01-v1
   - TEST-BDD-01-v1
   - GAP-DOC-01-v1
3. **Domain index expanded** - 12 → 18 domains
4. **Counts verified** - 58 ACTIVE rules in TypeDB

---

## Original Discrepancy Analysis

---

## Discrepancy Analysis

### Rules in TypeDB but NOT in RULES-DIRECTIVES.md

| TypeDB ID | Semantic ID | Name | Priority |
|-----------|-------------|------|----------|
| RULE-044 | TEST-EXEC-01-v1 | Session Summary Reporting | HIGH |
| RULE-045 | INTENT-CHECK-01-v1 | Intent Verification Before Completion | HIGH |
| RULE-046 | REPORT-HUMOR-01-v1 | Session Wisdom and Humor | LOW |
| RULE-047 | GOV-MODE-01-v1 | Governance Mode Configuration | HIGH |
| RULE-048 | FEEDBACK-LOGIC-01-v1 | Evidence-Based Feedback | HIGH |
| RULE-049 | REPORT-ISSUE-01-v1 | GitHub Certification Issue Protocol | HIGH |
| RULE-050 | SESSION-PROMPT-01-v1 | Initial Prompt Capture | HIGH |
| RULE-051 | MCP-RESTART-AUTO-01-v1 | Autonomous MCP Server Restart | HIGH |
| RULE-052 | TEST-UI-VERIFY-01-v1 | UI Feature Visual Verification | HIGH |
| RULE-053 | WORKFLOW-SHELL-01-v1 | Shell Wrapper Pattern | HIGH |
| RULE-054 | CONTAINER-MGMT-01-v1 | Container Management Best Practices | HIGH |
| CONTAINER-TYPEDB-01-v1 | (none) | TypeDB Container Query Patterns | HIGH |
| PKG-LATEST-01-v1 | (none) | Latest Stable Package Versions | HIGH |
| DOC-GAP-ARCHIVE-01-v1 | (none) | Gap Index Archive Structure | MEDIUM |

**Total new rules not in index: 14**

### Rules with Semantic ID Mismatch

Some rules have `semantic_id` that doesn't match their TypeDB `id`:

| TypeDB ID | semantic_id | Expected Pattern |
|-----------|-------------|------------------|
| RULE-019 | GOV-PROP-02-v1 | RULE-019 → should be UI-UX-01-v1 (per name) |
| RULE-017 | UI-TRAME-01-v1 | Name: "Cross-Workspace Pattern Reuse" - mismatch |

### Rules Missing from TypeDB (in markdown but not TypeDB)

| Markdown File | Status |
|---------------|--------|
| SESSION-EVID-01-v1.md | Present (RULE-001) |
| TASK-TECH-01-v1.md | **MISSING from TypeDB** |
| TASK-LIFE-01-v1.md | **MISSING from TypeDB** |
| UI-LOADER-01-v1.md | **MISSING from TypeDB** |
| UI-TRACE-01-v1.md | **MISSING from TypeDB** |
| TEST-BDD-01-v1.md | **MISSING from TypeDB** |
| GAP-DOC-01-v1.md | **MISSING from TypeDB** |

---

## Root Cause

1. **No sync process** - Rules added to TypeDB without updating markdown index
2. **No sync process** - Markdown leaf rules created without TypeDB sync
3. **Manual maintenance** - RULES-DIRECTIVES.md requires manual updates
4. **No enforcement** - No hook validates rule consistency

---

## Proposed Actions

### Phase 1: Sync (Immediate)
1. Add 14 missing rules to RULES-DIRECTIVES.md
2. Sync 7 markdown-only rules to TypeDB
3. Fix semantic_id mismatches

### Phase 2: Automation
1. Create rule sync script: `scripts/sync_rules.py`
2. Add pre-commit hook to validate rule consistency
3. Add MCP tool: `governance_validate_rules`

### Phase 3: Simplification
1. Single source of truth: TypeDB OR markdown (not both)
2. Generate RULES-DIRECTIVES.md from TypeDB query
3. Remove duplicate markdown index files

---

## Rule Categories (TypeDB Analysis)

| Category | Count | Examples |
|----------|-------|----------|
| governance | 12 | GOV-*, SESSION-EVID |
| operational | 12 | WORKFLOW-*, CONTAINER-* |
| testing | 6 | TEST-* |
| architecture | 4 | ARCH-* |
| devops | 3 | CONTAINER-DEV, PKG-LATEST |
| stability | 2 | SAFETY-* |
| reporting | 2 | REPORT-* |
| autonomy | 2 | WORKFLOW-AUTO |
| strategic | 2 | |
| workflow | 1 | |
| quality | 1 | |
| maintenance | 1 | |
| traceability | 1 | |
| productivity | 1 | |
| documentation | 1 | |
| technical | 1 | |

**Observation:** Categories are inconsistent. Same rule domain has multiple category names.

---

## CRITICAL Priority Rules (Must Enforce)

| Semantic ID | Name | Has Hook? | Has Test? |
|-------------|------|-----------|-----------|
| SESSION-EVID-01-v1 | Session Evidence Logging | NO | NO |
| GOV-BICAM-01-v1 | Bicameral Governance Model | NO | NO |
| WORKFLOW-AUTO-01-v1 | Autonomous Task Sequencing | PARTIAL | NO |
| RECOVER-AMNES-01-v1 | AMNESIA Protocol | YES | PARTIAL |
| TEST-COMP-02-v1 | Test Before Commit | YES (pre-commit) | YES |
| SAFETY-HEALTH-01-v1 | MCP Healthcheck Protocol | YES | YES |
| SAFETY-DESTR-01-v1 | Destructive Command Prevention | YES | YES |
| WORKFLOW-RD-01-v1 | R&D Workflow with Human Approval | NO | NO |
| ARCH-INFRA-01-v1 | Infrastructure Identity | NO | NO |
| TEST-FIX-01-v1 | Fix Validation Protocol | PARTIAL | NO |
| DOC-LINK-01-v1 | Relative Document Linking | NO | NO |
| CONTAINER-DEV-01-v1 | DevOps Version Compatibility | NO | NO |

**Enforcement Gap:** 8 of 12 CRITICAL rules have no automation

---

*Per SESSION-EVID-01-v1: Evidence documentation for governance audit*
