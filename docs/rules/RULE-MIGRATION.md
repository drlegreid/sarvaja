# Rule ID Migration Mapping

Migration from legacy `RULE-XXX` to semantic `{DOMAIN}-{SUB}-{NN}-v{N}` format.

> **Per:** META-TAXON-01-v1 | **Date:** 2026-01-13 | **Status:** FILESYSTEM COMPLETE

---

## Migration Status

| Component | Status | Notes |
|-----------|--------|-------|
| Leaf Files | COMPLETE | 40 files renamed in `docs/rules/leaf/` |
| Parent Docs | COMPLETE | 9 parent documents updated |
| Index Docs | COMPLETE | 3 index files (GOVERNANCE, TECHNICAL, OPERATIONAL) updated |
| TypeDB Rules | COMPLETE | 41 rules (legacy IDs + aliasing via SEMANTIC_TO_LEGACY map) |
| TypeDB Relations | COMPLETE | 203 document-rule relations created |
| MCP Tools | COMPLETE | GAP-MCP-008 resolved - dual pattern matching + subdirs |
| CLAUDE.md | COMPLETE | Rule references updated to semantic IDs |
| RULES-DIRECTIVES.md | COMPLETE | Full index with semantic IDs |

---

## Migration Table

| Legacy ID | New Semantic ID | Name | Domain | Sub | File |
|-----------|-----------------|------|--------|-----|------|
| RULE-001 | SESSION-EVID-01-v1 | Session Evidence Logging | SESSION | EVID | DONE |
| RULE-002 | ARCH-BEST-01-v1 | Architectural Best Practices | ARCH | BEST | DONE |
| RULE-003 | REPORT-DEC-01-v1 | Decision Logging & Rationale | REPORT | DEC | DONE |
| RULE-004 | REPORT-DEC-02-v1 | Incremental Reporting | REPORT | DEC | DONE |
| RULE-005 | RECOVER-MEM-01-v1 | Memory & MCP Stability | RECOVER | MEM | DONE |
| RULE-006 | GOV-TRUST-01-v1 | Governance Audit & Review | GOV | TRUST | DONE |
| RULE-007 | ARCH-MCP-01-v1 | MCP Usage Protocol | ARCH | MCP | DONE |
| RULE-008 | TEST-GUARD-01-v1 | Rewrite Guardrails | TEST | GUARD | DONE |
| RULE-009 | CONTAINER-DEV-01-v1 | DevOps Version Compatibility | CONTAINER | DEV | DONE |
| RULE-010 | GOV-RULE-01-v1 | Agent Wisdom Transmission | GOV | RULE | DONE |
| RULE-011 | GOV-BICAM-01-v1 | Bicameral Governance Model | GOV | BICAM | DONE |
| RULE-012 | SESSION-DSM-01-v1 | Deep Sleep Protocol (DSP) | SESSION | DSM | DONE |
| RULE-013 | GOV-PROP-01-v1 | GAP Resolution Workflow | GOV | PROP | DONE |
| RULE-014 | WORKFLOW-AUTO-01-v1 | Autonomous Task Sequencing | WORKFLOW | AUTO | DONE |
| RULE-015 | WORKFLOW-RD-01-v1 | R&D Workflow with Human Approval | WORKFLOW | RD | DONE |
| RULE-016 | ARCH-INFRA-01-v1 | Infrastructure Identity & Hardware | ARCH | INFRA | DONE |
| RULE-017 | UI-TRAME-01-v1 | Trame UI Patterns | UI | TRAME | DONE |
| RULE-018 | GOV-TRUST-02-v1 | Agent Trust Scoring | GOV | TRUST | DONE |
| RULE-019 | GOV-PROP-02-v1 | Proposal Review Process | GOV | PROP | DONE |
| RULE-020 | TEST-COMP-01-v1 | Comprehensive Testing Protocol | TEST | COMP | DONE |
| RULE-021 | SAFETY-HEALTH-01-v1 | MCP Healthcheck Protocol | SAFETY | HEALTH | DONE |
| RULE-022 | SAFETY-INTEG-01-v1 | Integrity Verification (Frankel Hash) | SAFETY | INTEG | DONE |
| RULE-023 | TEST-COMP-02-v1 | Test Before Commit | TEST | COMP | DONE |
| RULE-024 | RECOVER-AMNES-01-v1 | AMNESIA Protocol | RECOVER | AMNES | DONE |
| RULE-025 | GOV-PROP-03-v1 | Handoff Protocol | GOV | PROP | DONE |
| RULE-026 | GOV-RULE-02-v1 | Rule Compliance Verification | GOV | RULE | DONE |
| RULE-027 | CONTAINER-RESTART-01-v1 | API Server Restart Protocol | CONTAINER | RESTART | DONE |
| RULE-028 | WORKFLOW-SEQ-01-v1 | Multi-Session Task Continuity | WORKFLOW | SEQ | DONE |
| RULE-029 | GOV-RULE-03-v1 | Rule Deprecation Protocol | GOV | RULE | DONE |
| RULE-030 | CONTAINER-DEV-02-v1 | Docker Dev Container Workflow | CONTAINER | DEV | DONE |
| RULE-031 | WORKFLOW-AUTO-02-v1 | Autonomous Task Continuation | WORKFLOW | AUTO | DONE |
| RULE-032 | DOC-SIZE-01-v1 | File Size & OOP Standards | DOC | SIZE | DONE |
| RULE-033 | DOC-PARTIAL-01-v1 | PARTIAL Task Handling | DOC | PARTIAL | DONE |
| RULE-034 | DOC-LINK-01-v1 | Relative Document Linking | DOC | LINK | DONE |
| RULE-035 | CONTAINER-SHELL-01-v1 | Shell Command Environment Selection | CONTAINER | SHELL | DONE |
| RULE-036 | ARCH-MCP-02-v1 | MCP Server Separation Pattern | ARCH | MCP | DONE |
| RULE-037 | TEST-FIX-01-v1 | Fix Validation Protocol | TEST | FIX | DONE |
| RULE-040 | ARCH-INFRA-02-v1 | Portable Configuration Patterns | ARCH | INFRA | DONE |
| RULE-041 | RECOVER-CRASH-01-v1 | Crash Investigation Protocol | RECOVER | CRASH | DONE |
| RULE-042 | SAFETY-DESTR-01-v1 | Destructive Command Prevention | SAFETY | DESTR | DONE |
| (new) | META-TAXON-01-v1 | Rule Taxonomy & Management | META | TAXON | DONE |

---

## Domain Summary

| Domain | Count | Sub-categories |
|--------|-------|----------------|
| SESSION | 2 | EVID-01, DSM-01 |
| REPORT | 2 | DEC-01, DEC-02 |
| GOV | 8 | TRUST-01/02, BICAM-01, PROP-01/02/03, RULE-01/02/03 |
| ARCH | 5 | BEST-01, MCP-01/02, INFRA-01/02 |
| WORKFLOW | 4 | AUTO-01/02, RD-01, SEQ-01 |
| RECOVER | 3 | MEM-01, AMNES-01, CRASH-01 |
| TEST | 4 | GUARD-01, COMP-01/02, FIX-01 |
| SAFETY | 3 | HEALTH-01, INTEG-01, DESTR-01 |
| CONTAINER | 4 | DEV-01/02, RESTART-01, SHELL-01 |
| DOC | 3 | SIZE-01, PARTIAL-01, LINK-01 |
| UI | 1 | TRAME-01 |
| META | 1 | TAXON-01 |

**Total: 41 rules** (40 migrated + 1 new META)

---

## Verification Checklist

- [x] All 40 leaf files renamed to semantic format
- [x] All 9 parent documents updated with new IDs
- [x] All 3 index documents updated (GOVERNANCE, TECHNICAL, OPERATIONAL)
- [x] META-TAXON-01-v1 rule created
- [x] TypeDB document relations synced (87 relations)
- [x] RULES-DIRECTIVES.md index updated with semantic IDs
- [x] CLAUDE.md rule references updated
- [ ] TypeDB rule IDs migrated (optional - aliases supported)

---

## TypeDB Migration (Optional)

TypeDB currently uses legacy `RULE-XXX` IDs. Two migration paths:

### Option A: Alias Relations (Recommended)

```typeql
# Add alias relation to schema
define
rule-alias sub relation,
    relates legacy-id,
    relates semantic-id;

governance-rule plays rule-alias:legacy-id;
governance-rule plays rule-alias:semantic-id;

# Migration insert (example)
match
    $old isa governance-rule, has rule-id "RULE-001";
    $new isa governance-rule, has rule-id "SESSION-EVID-01-v1";
insert
    (legacy-id: $old, semantic-id: $new) isa rule-alias;
```

### Option B: Direct ID Update

```typeql
# Update rule ID directly (requires schema change)
match
    $r isa governance-rule, has rule-id "RULE-001";
delete
    $r has rule-id "RULE-001";
insert
    $r has rule-id "SESSION-EVID-01-v1";
```

---

## Rollback Instructions

If rollback is needed:

```bash
# Restore leaf files from git
git checkout HEAD~1 -- docs/rules/leaf/

# Restore parent documents
git checkout HEAD~1 -- docs/rules/governance/
git checkout HEAD~1 -- docs/rules/technical/
git checkout HEAD~1 -- docs/rules/operational/
```

---

*Per META-TAXON-01-v1: Rule Taxonomy & Management*
