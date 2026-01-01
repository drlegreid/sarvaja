# Sim.ai Rules Directives - Index

**Status:** Active | **Updated:** 2024-12-28 | **Rules:** 30 (27 ACTIVE, 3 DRAFT)

---

## Quick Links

| Document | Content | Rules |
|----------|---------|-------|
| [RULES-GOVERNANCE](rules/RULES-GOVERNANCE.md) | Process, documentation, collaboration, reporting | 001, 003, 006, 011, 013, 018, 019, 026, 029 |
| [RULES-TECHNICAL](rules/RULES-TECHNICAL.md) | Architecture, technology, infrastructure | 002, 007, 008, 009, 010, 016, 017 |
| [RULES-OPERATIONAL](rules/RULES-OPERATIONAL.md) | Testing, stability, maintenance, execution, security | 004, 005, 012, 014, 015, 020, 021, 022, 023, 024, 027, 028, 030 |

---

## Rules Summary

| Rule | Name | Category | Priority | Status |
|------|------|----------|----------|--------|
| RULE-001 | Session Evidence Logging | governance | CRITICAL | ACTIVE |
| RULE-002 | Architectural Best Practices | architecture | HIGH | ACTIVE |
| RULE-003 | Sync Protocol | governance | HIGH | DRAFT |
| RULE-004 | Exploratory Testing, Executable Spec & Insight Capture | testing | HIGH | ACTIVE |
| RULE-005 | Memory & MCP Stability | stability | HIGH | ACTIVE |
| RULE-006 | Decision Logging | governance | MEDIUM | ACTIVE |
| RULE-007 | MCP Usage Protocol | productivity | HIGH | ACTIVE |
| RULE-008 | In-House Rewrite Principle | strategic | CRITICAL | ACTIVE |
| RULE-009 | Version Compatibility | devops | CRITICAL | ACTIVE |
| RULE-010 | Evidence-Based Wisdom | strategic | CRITICAL | ACTIVE |
| RULE-011 | Multi-Agent Governance | governance | CRITICAL | ACTIVE |
| RULE-012 | Deep Sleep Protocol (DSP) | maintenance | HIGH | ACTIVE |
| RULE-013 | Rules Applicability Convention | governance | HIGH | ACTIVE |
| RULE-014 | Autonomous Task Sequencing | autonomy | CRITICAL | ACTIVE |
| RULE-015 | R&D Workflow Human Gate | autonomy | CRITICAL | ACTIVE |
| RULE-016 | Infrastructure Identity & Hardware | devops | CRITICAL | ACTIVE |
| RULE-017 | Cross-Workspace Pattern Reuse | strategic | HIGH | ACTIVE |
| RULE-018 | Objective Reporting | reporting | HIGH | ACTIVE |
| RULE-019 | UI/UX Design Standards | reporting | HIGH | ACTIVE |
| RULE-020 | LLM-Driven E2E Test Generation | testing | HIGH | ACTIVE |
| RULE-021 | MCP Healthcheck Protocol | stability | CRITICAL | ACTIVE |
| RULE-022 | Integrity Verification (Frankel Hash) | security | HIGH | DRAFT |
| RULE-023 | Test Before Ship | quality | CRITICAL | ACTIVE |
| RULE-024 | AMNESIA Protocol (Context Recovery) | maintenance | CRITICAL | ACTIVE |
| RULE-025 | Test Data Integrity Requirements | testing | HIGH | DRAFT |
| RULE-026 | Decision Context Communication | governance | HIGH | ACTIVE |
| RULE-027 | API Server Restart Protocol | testing | HIGH | ACTIVE |
| RULE-028 | Change Validation Protocol | testing | HIGH | ACTIVE |
| RULE-029 | Executive Reporting Pattern | reporting | HIGH | ACTIVE |
| RULE-030 | Docker Dev Container Workflow | development | HIGH | ACTIVE |

---

## Categories

| Category | Priority | Rules |
|----------|----------|-------|
| `governance` | CRITICAL | 001, 003, 006, 011, 013 |
| `strategic` | CRITICAL | 008, 010, 017 |
| `autonomy` | CRITICAL | 014, 015 |
| `architecture` | HIGH | 002 |
| `devops` | CRITICAL | 009, 016 |
| `productivity` | HIGH | 007 |
| `testing` | HIGH | 004, 020, 025, 027, 028 |
| `stability` | CRITICAL | 005, 021 |
| `maintenance` | CRITICAL | 012, 024 |
| `reporting` | HIGH | 018, 019, 029 |
| `security` | HIGH | 022 |
| `quality` | CRITICAL | 023 |
| `development` | HIGH | 030 |

---

## Priority Levels

| Level | Meaning | Rules |
|-------|---------|-------|
| **CRITICAL** | Must enforce always | 001, 008, 009, 010, 011, 014, 015, 016, 021, 023, 024 |
| **HIGH** | Enforce in normal ops | 002, 003, 004, 005, 007, 012, 013, 017, 018, 019, 020, 022 |
| **MEDIUM** | Advisory | 006 |

---

## Enforcement

Rules are enforced via:
1. **Pre-commit hooks** - Static validation
2. **CI/CD checks** - Test suite compliance
3. **Runtime guards** - Agent checks before execution
4. **DSP audits** - Periodic hygiene checks

---

## Halt Commands (RULE-014)

| Command | Action |
|---------|--------|
| `STOP` | Immediate halt, save state |
| `HALT` | Immediate halt, save state |
| `STAI` | Immediate halt, save state |
| `RED ALERT` | Emergency stop |
| `ALERT` | Pause and await |

---

## ChromaDB Index

```json
{
  "collection": "sim_ai_rules",
  "schema": {
    "id": "rule_{number}",
    "document": "Full rule text",
    "metadata": {
      "category": "string",
      "priority": "CRITICAL|HIGH|MEDIUM",
      "status": "ACTIVE|DRAFT|DEPRECATED"
    }
  }
}
```

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2024-12-24 | Initial: RULE-001, RULE-002 |
| 0.5.0 | 2024-12-24 | Added RULE-003 to RULE-007 |
| 0.9.0 | 2024-12-24 | Added RULE-008 to RULE-011 |
| 0.12.0 | 2024-12-24 | Added RULE-012 to RULE-014 |
| 1.0.0 | 2024-12-24 | Split into modular files |
| 1.1.0 | 2024-12-24 | Added RULE-015: R&D Workflow, Enhanced RULE-012 with MCP checks |
| 1.2.0 | 2024-12-24 | Added RULE-016: Infrastructure Identity, RULE-017: Cross-Workspace Patterns |
| 1.3.0 | 2024-12-24 | Added RULE-018: Objective Reporting, RULE-019: UI/UX Standards |
| 1.4.0 | 2024-12-25 | Added RULE-020: LLM-Driven E2E Test Generation |
| 1.5.0 | 2024-12-25 | Added RULE-021: MCP Healthcheck Protocol, RULE-022: Integrity Verification |
| 1.6.0 | 2024-12-25 | Added RULE-023: Test Before Ship |
| 1.7.0 | 2024-12-25 | Enhanced RULE-004: Added Insight Capture Protocol, Spec-First TDD workflow mode |
| 1.8.0 | 2024-12-25 | Enhanced RULE-012: Added Semantic Code Structure (DSP Hygiene) - FP + Digital Twin paradigm |
| 1.9.0 | 2024-12-25 | Enhanced RULE-011: Added R&D Rule Quality & Decomposition (Category/Group Theory patterns) |
| 2.0.0 | 2024-12-25 | Added RULE-024: AMNESIA Protocol (Autonomous Context Recovery) |
| 2.1.0 | 2024-12-26 | Added RULE-025: Test Data Integrity Requirements |
| 2.2.0 | 2024-12-26 | Added RULE-027: API Server Restart Protocol (TODO-6 discovery) |
| 2.3.0 | 2024-12-27 | Added RULE-028: Change Validation Protocol (exploratory heuristics) |
| 2.4.0 | 2024-12-27 | Added RULE-029: Executive Reporting Pattern (enterprise reporting) |
| 2.5.0 | 2024-12-28 | Added RULE-030: Docker Dev Container Workflow (autonomous validation) |

---

*Per RULE-012: Deep Sleep Protocol - document hygiene*
