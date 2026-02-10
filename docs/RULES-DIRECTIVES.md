# Rules Directives - Index

**Status:** Active | **Updated:** 2026-02-11 | **Rules:** 59 (56 ACTIVE, 3 DRAFT/DISABLED)

> **Taxonomy:** [META-TAXON-01-v1](rules/leaf/META-TAXON-01-v1.md) | **Migration:** [RULE-MIGRATION.md](rules/RULE-MIGRATION.md)

---

## Quick Links

| Document | Content | Domains |
|----------|---------|---------|
| [RULES-GOVERNANCE](rules/RULES-GOVERNANCE.md) | Process, documentation, collaboration, reporting | SESSION, REPORT, GOV |
| [RULES-TECHNICAL](rules/RULES-TECHNICAL.md) | Architecture, technology, infrastructure | ARCH, UI |
| [RULES-OPERATIONAL](rules/RULES-OPERATIONAL.md) | Testing, stability, maintenance, execution | WORKFLOW, RECOVER, TEST, SAFETY, CONTAINER, DOC |

---

## Rules Summary (Semantic IDs)

| Semantic ID | Legacy | Name | Priority | Status |
|-------------|--------|------|----------|--------|
| SESSION-EVID-01-v1 | RULE-001 | Session Evidence Logging | CRITICAL | ACTIVE |
| SESSION-DSM-01-v1 | RULE-012 | Deep Sleep Protocol (DSP) | HIGH | ACTIVE |
| REPORT-DEC-01-v1 | RULE-003 | Decision Logging & Rationale | HIGH | ACTIVE |
| REPORT-DEC-02-v1 | RULE-004 | Incremental Reporting | HIGH | ACTIVE |
| GOV-TRUST-01-v1 | RULE-006 | Governance Audit & Review | MEDIUM | ACTIVE |
| GOV-TRUST-02-v1 | RULE-018 | Agent Trust Scoring | HIGH | ACTIVE |
| GOV-BICAM-01-v1 | RULE-011 | Bicameral Governance Model | CRITICAL | ACTIVE |
| GOV-PROP-01-v1 | RULE-013 | GAP Resolution Workflow | HIGH | ACTIVE |
| GOV-PROP-02-v1 | RULE-019 | Proposal Review Process | HIGH | ACTIVE |
| GOV-PROP-03-v1 | RULE-025 | Handoff Protocol | HIGH | DRAFT |
| GOV-RULE-01-v1 | RULE-010 | Agent Wisdom Transmission | CRITICAL | ACTIVE |
| GOV-RULE-02-v1 | RULE-026 | Rule Compliance Verification | HIGH | ACTIVE |
| GOV-RULE-03-v1 | RULE-029 | Rule Deprecation Protocol | HIGH | ACTIVE |
| GOV-BIND-01-v1 | (new) | Rule-to-Tool Binding | HIGH | ACTIVE |
| ARCH-BEST-01-v1 | RULE-002 | Architectural Best Practices | HIGH | ACTIVE |
| ARCH-MCP-01-v1 | RULE-007 | MCP Usage Protocol | HIGH | ACTIVE |
| ARCH-MCP-02-v1 | RULE-036 | MCP Server Separation Pattern | HIGH | ACTIVE |
| ARCH-INFRA-01-v1 | RULE-016 | Infrastructure Identity & Hardware | CRITICAL | ACTIVE |
| ARCH-INFRA-02-v1 | RULE-040 | Portable Configuration Patterns | HIGH | ACTIVE |
| ARCH-YAGNI-01-v1 | (new) | Service Proliferation Guard | HIGH | ACTIVE |
| UI-TRAME-01-v1 | RULE-017 | Trame UI Patterns | HIGH | ACTIVE |
| WORKFLOW-AUTO-01-v1 | RULE-014 | Autonomous Task Sequencing | CRITICAL | ACTIVE |
| WORKFLOW-AUTO-02-v1 | RULE-031 | Autonomous Task Continuation | CRITICAL | ACTIVE |
| WORKFLOW-RD-01-v1 | RULE-015 | R&D Workflow with Human Approval | CRITICAL | ACTIVE |
| WORKFLOW-SEQ-01-v1 | RULE-028 | Multi-Session Task Continuity | HIGH | ACTIVE |
| RECOVER-MEM-01-v1 | RULE-005 | Memory & MCP Stability | HIGH | ACTIVE |
| RECOVER-AMNES-01-v1 | RULE-024 | AMNESIA Protocol | CRITICAL | ACTIVE |
| RECOVER-CRASH-01-v1 | RULE-041 | Crash Investigation Protocol | CRITICAL | ACTIVE |
| TEST-GUARD-01-v1 | RULE-008 | Rewrite Guardrails | CRITICAL | ACTIVE |
| TEST-COMP-01-v1 | RULE-020 | Comprehensive Testing Protocol | HIGH | ACTIVE |
| TEST-COMP-02-v1 | RULE-023 | Test Before Commit | CRITICAL | ACTIVE |
| TEST-FIX-01-v1 | RULE-037 | Fix Validation Protocol | CRITICAL | ACTIVE |
| SAFETY-HEALTH-01-v1 | RULE-021 | MCP Healthcheck Protocol | CRITICAL | ACTIVE |
| SAFETY-INTEG-01-v1 | RULE-022 | Integrity Verification (Frankel Hash) | HIGH | DRAFT |
| SAFETY-DESTR-01-v1 | RULE-042 | Destructive Command Prevention | CRITICAL | ACTIVE |
| CONTAINER-DEV-01-v1 | RULE-009 | DevOps Version Compatibility | CRITICAL | ACTIVE |
| CONTAINER-DEV-02-v1 | RULE-030 | Docker Dev Container Workflow | HIGH | DISABLED |
| CONTAINER-RESTART-01-v1 | RULE-027 | API Server Restart Protocol | HIGH | ACTIVE |
| CONTAINER-SHELL-01-v1 | RULE-035 | Shell Command Environment Selection | HIGH | ACTIVE |
| DOC-SIZE-01-v1 | RULE-032 | File Size & OOP Standards | HIGH | ACTIVE |
| DOC-PARTIAL-01-v1 | RULE-033 | PARTIAL Task Handling | HIGH | ACTIVE |
| DOC-LINK-01-v1 | RULE-034 | Relative Document Linking | CRITICAL | ACTIVE |
| META-TAXON-01-v1 | RULE-043 | Rule Taxonomy & Management | HIGH | ACTIVE |
| TEST-EXEC-01-v1 | RULE-044 | Session Summary Reporting | HIGH | ACTIVE |
| INTENT-CHECK-01-v1 | RULE-045 | Intent Verification Before Completion | HIGH | ACTIVE |
| REPORT-HUMOR-01-v1 | RULE-046 | Session Wisdom and Humor | LOW | ACTIVE |
| GOV-MODE-01-v1 | RULE-047 | Governance Mode Configuration | HIGH | ACTIVE |
| FEEDBACK-LOGIC-01-v1 | RULE-048 | Evidence-Based Feedback | HIGH | ACTIVE |
| REPORT-ISSUE-01-v1 | RULE-049 | GitHub Certification Issue Protocol | HIGH | ACTIVE |
| SESSION-PROMPT-01-v1 | RULE-050 | Initial Prompt Capture | HIGH | ACTIVE |
| MCP-RESTART-AUTO-01-v1 | RULE-051 | Autonomous MCP Server Restart | HIGH | ACTIVE |
| TEST-UI-VERIFY-01-v1 | RULE-052 | UI Feature Visual Verification | HIGH | ACTIVE |
| WORKFLOW-SHELL-01-v1 | RULE-053 | Shell Wrapper Pattern | HIGH | ACTIVE |
| CONTAINER-MGMT-01-v1 | RULE-054 | Container Management Best Practices | HIGH | ACTIVE |
| CONTAINER-TYPEDB-01-v1 | (new) | TypeDB Container Query Patterns | HIGH | ACTIVE |
| PKG-LATEST-01-v1 | (new) | Latest Stable Package Versions | HIGH | ACTIVE |
| DOC-GAP-ARCHIVE-01-v1 | (new) | Gap Index Archive Structure | MEDIUM | ACTIVE |
| TASK-TECH-01-v1 | (new) | Technology Solution Documentation | MEDIUM | ACTIVE |
| TASK-LIFE-01-v1 | (new) | Task Lifecycle Management | HIGH | ACTIVE |
| UI-LOADER-01-v1 | (new) | UI Loader State Pattern | HIGH | ACTIVE |
| UI-TRACE-01-v1 | (new) | UI Trace Bar Display | MEDIUM | ACTIVE |
| UI-COLOR-01-v1 | (new) | Color Harmony & Palette Standards | HIGH | ACTIVE |
| TEST-BDD-01-v1 | (new) | BDD Testing with Gherkin | HIGH | ACTIVE |
| GAP-DOC-01-v1 | (new) | Gap Documentation Standard | HIGH | ACTIVE |
| WORKFLOW-HOTRELOAD-01-v1 | (new) | Dashboard Hot-Reload via Watcher | HIGH | ACTIVE |
| WORKFLOW-SFDC-01-v1 | (new) | SFDC Development Lifecycle Workflow | HIGH | ACTIVE |
| WORKFLOW-ORCH-01-v1 | (new) | Orchestrator Continuous Workflow | CRITICAL | ACTIVE |
| TEST-SPEC-01-v1 | (new) | 3-Tier Validation Specifications | HIGH | ACTIVE |

---

## Domain Index

| Domain | Description | Count | Rules |
|--------|-------------|-------|-------|
| **SESSION** | Session management | 3 | EVID-01, DSM-01, PROMPT-01 |
| **REPORT** | Reporting & decisions | 4 | DEC-01, DEC-02, HUMOR-01, ISSUE-01, SUMM-01 |
| **GOV** | Governance & trust | 10 | TRUST-01/02, BICAM-01, PROP-01/02/03, RULE-01/02/03, MODE-01, BIND-01 |
| **ARCH** | Architecture | 6 | BEST-01, MCP-01/02, INFRA-01/02, YAGNI-01 |
| **UI** | User interface | 4 | TRAME-01, LOADER-01, TRACE-01, COLOR-01 |
| **WORKFLOW** | Workflow & autonomy | 8 | AUTO-01/02, RD-01, SEQ-01, SHELL-01, HOTRELOAD-01, SFDC-01, ORCH-01 |
| **RECOVER** | Recovery & resilience | 3 | MEM-01, AMNES-01, CRASH-01 |
| **TEST** | Testing & validation | 8 | GUARD-01, COMP-01/02, FIX-01, EXEC-01, UI-VERIFY-01, BDD-01, SPEC-01 |
| **SAFETY** | Safety & prevention | 3 | HEALTH-01, INTEG-01, DESTR-01 |
| **CONTAINER** | Container operations | 5 | DEV-01/02, RESTART-01, SHELL-01, TYPEDB-01, MGMT-01 |
| **DOC** | Documentation | 4 | SIZE-01, PARTIAL-01, LINK-01, GAP-ARCHIVE-01 |
| **META** | Meta-rules | 1 | TAXON-01 |
| **TASK** | Task management | 2 | TECH-01, LIFE-01 |
| **INTENT** | Intent verification | 1 | CHECK-01 |
| **FEEDBACK** | Feedback rules | 1 | LOGIC-01 |
| **PKG** | Package management | 1 | LATEST-01 |
| **GAP** | Gap documentation | 1 | DOC-01 |
| **MCP** | MCP operations | 1 | RESTART-AUTO-01 |

---

## Priority Levels

| Level | Meaning | Count | Key Rules |
|-------|---------|-------|-----------|
| **CRITICAL** | Must enforce always | 16 | SESSION-EVID, GOV-BICAM, WORKFLOW-AUTO, RECOVER-AMNES, TEST-COMP-02, SAFETY-HEALTH |
| **HIGH** | Enforce in normal ops | 26 | ARCH-*, GOV-BIND-01, TEST-COMP-01, CONTAINER-*, DOC-* |
| **MEDIUM** | Advisory | 1 | GOV-TRUST-01 |

---

## Halt Commands (WORKFLOW-AUTO-01-v1)

| Command | Action |
|---------|--------|
| `STOP` | Immediate halt, save state |
| `HALT` | Immediate halt, save state |
| `STAI` | Immediate halt, save state |
| `RED ALERT` | Emergency stop |

---

## Enforcement

Rules are enforced via:
1. **Pre-commit hooks** - Static validation
2. **CI/CD checks** - Test suite compliance
3. **Runtime guards** - Agent checks before execution
4. **DSP audits** - Periodic hygiene checks (SESSION-DSM-01-v1)

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 5.0.0 | 2026-01-17 | **Sarvaja Rename** - Project renamed from Sim.ai per DECISION-008. Semantic IDs now primary identifiers |
| 4.0.0 | 2026-01-13 | **Semantic Rule ID Migration** - All rules migrated to `{DOMAIN}-{SUB}-{NN}-v{N}` format per META-TAXON-01-v1 |
| 3.1.0 | 2026-01-11 | Added RULE-041: Crash Investigation, RULE-042: Destructive Command Prevention |
| 3.0.0 | 2026-01-03 | Added RULE-035: Shell Command Environment Selection |
| 2.9.0 | 2026-01-02 | Added RULE-034: Relative Document Linking |
| 2.8.0 | 2026-01-02 | Added RULE-033: PARTIAL Task Handling |
| 2.7.0 | 2026-01-02 | Added RULE-032: File Size & OOP Standards |
| 2.6.0 | 2026-01-01 | Added RULE-031: Autonomous Task Continuation |
| 2.0.0 | 2024-12-25 | Added RULE-024: AMNESIA Protocol |
| 1.0.0 | 2024-12-24 | Initial split into modular files |

---

*Per SESSION-DSM-01-v1: Deep Sleep Protocol - document hygiene*
