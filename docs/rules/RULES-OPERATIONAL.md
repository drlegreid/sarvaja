# Operational Rules Index - Sim.ai

Rules governing testing, stability, maintenance, and task execution.

> **Per RULE-032:** Split from 1900 lines to 4 thematic files (2026-01-03)

---

## Rule Files

| File | Rules | Lines | Description |
|------|-------|-------|-------------|
| [RULES-TESTING.md](operational/RULES-TESTING.md) | 004, 020, 023, 028 | ~130 | Testing, quality gates, validation |
| [RULES-STABILITY.md](operational/RULES-STABILITY.md) | 005, 021, 022, 041 | ~260 | Memory, MCP health, integrity |
| [RULES-WORKFLOW.md](operational/RULES-WORKFLOW.md) | 012, 014, 015, 024, 031 | ~180 | Autonomy, DSP, context recovery |
| [RULES-STANDARDS.md](operational/RULES-STANDARDS.md) | 027, 030, 032-035, 037, 042 | ~250 | DevOps, file size, fix validation, safety |

---

## Quick Reference

### Testing Rules (RULES-TESTING.md)

| Rule | Name | Priority |
|------|------|----------|
| **RULE-004** | Exploratory Test Automation | HIGH |
| **RULE-020** | LLM-Driven E2E Test Generation | HIGH |
| **RULE-023** | Test Before Ship | CRITICAL |
| **RULE-028** | Change Validation Protocol | HIGH |

### Stability Rules (RULES-STABILITY.md)

| Rule | Name | Priority |
|------|------|----------|
| **RULE-005** | Memory & MCP Stability | HIGH |
| **RULE-021** | MCP Healthcheck Protocol | CRITICAL |
| **RULE-022** | Integrity Verification (Frankel Hash) | HIGH |
| **RULE-041** | Crash Investigation Protocol | CRITICAL |

### Workflow Rules (RULES-WORKFLOW.md)

| Rule | Name | Priority |
|------|------|----------|
| **RULE-012** | Deep Sleep Protocol (DSP) | HIGH |
| **RULE-014** | Autonomous Task Sequencing | CRITICAL |
| **RULE-015** | R&D Workflow with Human Approval | CRITICAL |
| **RULE-024** | AMNESIA Protocol | CRITICAL |
| **RULE-031** | Autonomous Task Continuation | CRITICAL |

### Standards Rules (RULES-STANDARDS.md)

| Rule | Name | Priority |
|------|------|----------|
| **RULE-027** | API Server Restart Protocol | HIGH |
| **RULE-030** | Docker Dev Container Workflow | HIGH |
| **RULE-032** | File Size & OOP Standards | HIGH |
| **RULE-033** | PARTIAL Task Handling | HIGH |
| **RULE-034** | Relative Document Linking | CRITICAL |
| **RULE-035** | Shell Command Environment Selection | HIGH |
| **RULE-037** | Fix Validation Protocol | CRITICAL |
| **RULE-042** | Destructive Command Prevention | CRITICAL |

---

## Cross-References

| Category | Related |
|----------|---------|
| Governance | [RULES-GOVERNANCE.md](RULES-GOVERNANCE.md) |
| Technical | [RULES-TECHNICAL.md](RULES-TECHNICAL.md) |
| All Rules | [RULES-DIRECTIVES.md](../RULES-DIRECTIVES.md) |

---

*Per RULE-012: DSP Semantic Code Structure*
*Per RULE-032: File Size ≤300 lines*
