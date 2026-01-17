# Operational Rules Index - Sim.ai

Rules governing testing, stability, maintenance, and task execution.

> **Per DOC-SIZE-01-v1:** Split from 1900 lines to 4 thematic files (2026-01-03)

---

## Rule Files

| File | Domains | Lines | Description |
|------|---------|-------|-------------|
| [RULES-WORKFLOW.md](operational/RULES-WORKFLOW.md) | SESSION, WORKFLOW, RECOVER | ~150 | Task sequencing, autonomy, recovery |
| [RULES-TESTING.md](operational/RULES-TESTING.md) | TEST | ~120 | Testing strategies, validation |
| [RULES-STABILITY.md](operational/RULES-STABILITY.md) | RECOVER, SAFETY | ~100 | Memory, health, integrity |
| [RULES-STANDARDS.md](operational/RULES-STANDARDS.md) | CONTAINER, DOC, TEST, SAFETY | ~150 | DevOps, documentation, safety |

---

## Quick Reference

### Workflow Rules (RULES-WORKFLOW.md)

| Rule | Name | Priority |
|------|------|----------|
| **SESSION-DSM-01-v1** | Deep Sleep Protocol (DSP) | HIGH |
| **WORKFLOW-AUTO-01-v1** | Autonomous Task Sequencing | CRITICAL |
| **WORKFLOW-RD-01-v1** | R&D Workflow with Human Approval | CRITICAL |
| **RECOVER-AMNES-01-v1** | AMNESIA Protocol | CRITICAL |
| **WORKFLOW-AUTO-02-v1** | Autonomous Task Continuation | CRITICAL |
| **WORKFLOW-SEQ-01-v1** | Multi-Session Task Continuity | HIGH |

### Testing Rules (RULES-TESTING.md)

| Rule | Name | Priority |
|------|------|----------|
| **TEST-GUARD-01-v1** | Rewrite Guardrails | CRITICAL |
| **TEST-COMP-01-v1** | Comprehensive Testing Protocol | HIGH |
| **TEST-COMP-02-v1** | Test Before Commit | CRITICAL |
| **TEST-FIX-01-v1** | Fix Validation Protocol | CRITICAL |

### Stability Rules (RULES-STABILITY.md)

| Rule | Name | Priority |
|------|------|----------|
| **RECOVER-MEM-01-v1** | Memory & MCP Stability | HIGH |
| **SAFETY-HEALTH-01-v1** | MCP Healthcheck Protocol | CRITICAL |
| **SAFETY-INTEG-01-v1** | Integrity Verification (Frankel Hash) | HIGH |
| **RECOVER-CRASH-01-v1** | Crash Investigation Protocol | CRITICAL |

### Standards Rules (RULES-STANDARDS.md)

| Rule | Name | Priority |
|------|------|----------|
| **CONTAINER-RESTART-01-v1** | API Server Restart Protocol | HIGH |
| **CONTAINER-DEV-02-v1** | Docker Dev Container Workflow | **DISABLED** |
| **DOC-SIZE-01-v1** | File Size & OOP Standards | HIGH |
| **DOC-PARTIAL-01-v1** | PARTIAL Task Handling | HIGH |
| **DOC-LINK-01-v1** | Relative Document Linking | CRITICAL |
| **CONTAINER-SHELL-01-v1** | Shell Command Environment Selection | HIGH |
| **CONTAINER-TYPEDB-01-v1** | TypeDB Container Query Patterns | HIGH |
| **PKG-LATEST-01-v1** | Latest Stable Package Versions | HIGH |
| **TEST-FIX-01-v1** | Fix Validation Protocol | CRITICAL |
| **SAFETY-DESTR-01-v1** | Destructive Command Prevention | CRITICAL |

---

## Cross-References

| Category | Related |
|----------|---------|
| Governance | [RULES-GOVERNANCE.md](RULES-GOVERNANCE.md) |
| Technical | [RULES-TECHNICAL.md](RULES-TECHNICAL.md) |
| All Rules | [RULES-DIRECTIVES.md](../RULES-DIRECTIVES.md) |
| Migration | [RULE-MIGRATION.md](RULE-MIGRATION.md) |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per DOC-SIZE-01-v1: File Size ≤300 lines*
