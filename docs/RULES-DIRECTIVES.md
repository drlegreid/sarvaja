# Sim.ai Rules Directives - Index

**Status:** Active | **Updated:** 2024-12-24 | **Rules:** 15 (14 ACTIVE, 1 DRAFT)

---

## Quick Links

| Document | Content | Rules |
|----------|---------|-------|
| [RULES-GOVERNANCE](rules/RULES-GOVERNANCE.md) | Process, documentation, collaboration | 001, 003, 006, 011, 013 |
| [RULES-TECHNICAL](rules/RULES-TECHNICAL.md) | Architecture, technology, tooling | 002, 007, 008, 009, 010 |
| [RULES-OPERATIONAL](rules/RULES-OPERATIONAL.md) | Testing, stability, maintenance, execution | 004, 005, 012, 014, 015 |

---

## Rules Summary

| Rule | Name | Category | Priority | Status |
|------|------|----------|----------|--------|
| RULE-001 | Session Evidence Logging | governance | CRITICAL | ACTIVE |
| RULE-002 | Architectural Best Practices | architecture | HIGH | ACTIVE |
| RULE-003 | Sync Protocol | governance | HIGH | DRAFT |
| RULE-004 | Exploratory Test Automation | testing | HIGH | ACTIVE |
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

---

## Categories

| Category | Priority | Rules |
|----------|----------|-------|
| `governance` | CRITICAL | 001, 003, 006, 011, 013 |
| `strategic` | CRITICAL | 008, 010 |
| `autonomy` | CRITICAL | 014, 015 |
| `architecture` | HIGH | 002 |
| `devops` | CRITICAL | 009 |
| `productivity` | HIGH | 007 |
| `testing` | HIGH | 004 |
| `stability` | HIGH | 005 |
| `maintenance` | HIGH | 012 |

---

## Priority Levels

| Level | Meaning | Rules |
|-------|---------|-------|
| **CRITICAL** | Must enforce always | 001, 008, 009, 010, 011, 014, 015 |
| **HIGH** | Enforce in normal ops | 002, 003, 004, 005, 007, 012, 013 |
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

---

*Per RULE-012: Deep Sleep Protocol - document hygiene*
