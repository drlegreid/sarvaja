# Technical Rules Index

Rules governing architecture, technology selection, and tooling.

> **Per DOC-SIZE-01-v1:** Split from 457 lines to 3 thematic files (2026-01-03)

---

## Rule Files

| File | Domains | Lines | Description |
|------|---------|-------|-------------|
| [RULES-STRATEGY.md](technical/RULES-STRATEGY.md) | REPORT, GOV, UI | ~100 | Technology selection, learning, UI patterns |
| [RULES-ARCHITECTURE.md](technical/RULES-ARCHITECTURE.md) | ARCH | ~100 | Architecture, infrastructure, MCP patterns |
| [RULES-TOOLING.md](technical/RULES-TOOLING.md) | ARCH, CONTAINER | ~90 | MCP usage, version compatibility |

---

## Quick Reference

### Strategy Rules (RULES-STRATEGY.md)

| Rule | Name | Priority |
|------|------|----------|
| **REPORT-DEC-02-v1** | Incremental Reporting | HIGH |
| **GOV-RULE-01-v1** | Agent Wisdom Transmission | CRITICAL |
| **UI-TRAME-01-v1** | Trame UI Patterns | HIGH |

### Architecture Rules (RULES-ARCHITECTURE.md)

| Rule | Name | Priority |
|------|------|----------|
| **ARCH-BEST-01-v1** | Architectural Best Practices | HIGH |
| **ARCH-INFRA-01-v1** | Infrastructure Identity & Hardware | CRITICAL |
| **ARCH-MCP-02-v1** | MCP Server Separation Pattern | HIGH |

### Tooling Rules (RULES-TOOLING.md)

| Rule | Name | Priority |
|------|------|----------|
| **ARCH-MCP-01-v1** | MCP Usage Protocol | HIGH |
| **CONTAINER-DEV-01-v1** | DevOps Version Compatibility | CRITICAL |
| **ARCH-INFRA-02-v1** | Portable Configuration Patterns | HIGH |

### IDE Integration Rules

| Rule | Name | Priority |
|------|------|----------|
| **IDE-VSCODE-CC-01-v1** | VSCode Claude Code Permission Bypass Bug & Mitigations | HIGH |

### UI Expansions (P18, 2026-03-24)

| Rule | Name | Priority |
|------|------|----------|
| **UI-RESP-01-v1** | Responsive UI Design | HIGH |
| **UI-CROSS-NAV-01-v1** | Cross-View Navigation Guard | HIGH |
| **HTTP-ERROR-01-v1** | HTTP Exception Handling Protocol | CRITICAL |

### Data & Schema Rules (P18)

| Rule | Name | Priority |
|------|------|----------|
| **DATA-CLASSIFY-01-v1** | Data Classification Protocol | HIGH |
| **DATA-INGEST-01-v1** | Data Ingestion Pipeline Standard | HIGH |
| **DATA-LAZY-01-v1** | Lazy Loading Data Pattern | HIGH |
| **DATA-PERSIST-01-v1** | Data Persistence Standard | HIGH |
| **BACKFILL-OPS-01-v1** | Backfill Operations Protocol | MEDIUM |
| **SCHEMA-VERIFY-01-v1** | Schema Verification Protocol | HIGH |

### Development Environment Rules (P18)

| Rule | Name | Priority |
|------|------|----------|
| **DEV-VENV-01-v1** | Python Virtual Environment | HIGH |
| **DEP-PIN-01-v1** | Dependency Pinning | HIGH |

---

## Cross-References

| Category | Related |
|----------|---------|
| Governance | [RULES-GOVERNANCE.md](RULES-GOVERNANCE.md) |
| Operational | [RULES-OPERATIONAL.md](RULES-OPERATIONAL.md) |
| All Rules | [RULES-DIRECTIVES.md](../RULES-DIRECTIVES.md) |
| Migration | [RULE-MIGRATION.md](RULE-MIGRATION.md) |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per DOC-SIZE-01-v1: File Size ≤300 lines*
