# Operational Rules Index

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
| **COMM-PROGRESS-01-v1** | Communication & Progress Reporting | MANDATORY |

### Testing Rules (RULES-TESTING.md)

| Rule | Name | Priority |
|------|------|----------|
| **TEST-GUARD-01-v1** | Rewrite Guardrails | CRITICAL |
| **TEST-COMP-01-v1** | Comprehensive Testing Protocol | HIGH |
| **TEST-COMP-02-v1** | Test Before Commit | CRITICAL |
| **TEST-FIX-01-v1** | Fix Validation Protocol | CRITICAL |
| **TEST-E2E-01-v1** | Data Flow Verification Protocol | CRITICAL |

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

### MCP Operational Rules (P18, 2026-03-24)

| Rule | Name | Priority |
|------|------|----------|
| **MCP-DOC-01-v1** | MCP Documentation Standard | MEDIUM |
| **MCP-ERROR-01-v1** | MCP Error Response Format | MEDIUM |
| **MCP-FORMAT-01-v1** | MCP Output Format Standard | MEDIUM |
| **MCP-HEALTH-01-v1** | MCP Health Check Standard | MEDIUM |
| **MCP-LOGGING-01-v1** | MCP Logging Standard | MEDIUM |
| **MCP-NAMING-01-v1** | MCP Tool Naming Convention | MEDIUM |
| **MCP-OUTPUT-01-v1** | MCP Output Consistency | MEDIUM |
| **MCP-PERF-01-v1** | MCP Performance Standard | HIGH |
| **MCP-PERSIST-01-v1** | MCP Write Persistence Requirement | HIGH |

### Testing Expansions (P18)

| Rule | Name | Priority |
|------|------|----------|
| **TEST-CVP-01-v1** | Continuous Validation Pipeline | HIGH |
| **TEST-EDS-HEURISTIC-01-v1** | EDS Heuristic Check Framework | HIGH |
| **TEST-EVID-01-v1** | Test Evidence Collection | HIGH |
| **TEST-HOLO-01-v1** | Holographic Test Approach | MEDIUM |
| **TEST-LIVE-DB-01-v1** | Live Database Testing Protocol | HIGH |
| **TEST-QUAL-01-v1** | Test Quality Metrics | HIGH |
| **TEST-STRUCT-01-v1** | Test Structure Standard | HIGH |
| **TEST-TAXON-01-v1** | Test Taxonomy | MEDIUM |
| **TEST-TDD-01-v1** | Test-Driven Development | HIGH |
| **TEST-TIER-MANDATORY-01-v1** | Mandatory 3-Tier Validation | CRITICAL |

### Delivery & Reliability (P18)

| Rule | Name | Priority |
|------|------|----------|
| **DELIVER-VERIFY-01-v1** | Delivery Verification Protocol | CRITICAL |
| **RELIABILITY-PLAN-01-v1** | Reliability Planning Protocol | HIGH |
| **WORKFLOW-PLAN-01-v1** | Workflow Planning Standard | HIGH |

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
