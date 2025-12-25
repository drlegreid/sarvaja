# TODO Index - Sim.ai PoC

**Status:** Active | **Updated:** 2024-12-25 (P10 GitHub Actions + Templates)

---

## Quick Links

| Document | Content | Lines |
|----------|---------|-------|
| [GAP-INDEX](docs/gaps/GAP-INDEX.md) | Gap tracking (12 open, 9 resolved) | ~60 |
| [R&D-BACKLOG](docs/backlog/R&D-BACKLOG.md) | Strategic R&D, TypeDB phases | ~900 |
| [TASKS-COMPLETED](docs/tasks/TASKS-COMPLETED.md) | Archived completed tasks | ~120 |
| [RULES-DIRECTIVES](docs/RULES-DIRECTIVES.md) | 24 rules (22 ACTIVE, 2 DRAFT) | ~140 |

---

## Current Sprint: P10 - UI-First Sprint

### High Priority (P0)

| # | Task | Status | Phase | Description |
|---|------|--------|-------|-------------|
| 1 | GitHub Actions workflow | ✅ DONE | P10 | E2E certification runs |
| 2 | Certification issue template | ✅ DONE | P10 | `.github/ISSUE_TEMPLATE/certification.md` |

### Medium Priority (P1)

| # | Task | Status | Effort | GAP |
|---|------|--------|--------|-----|
| 6 | Agent Task Backlog UI | 📋 TODO | 3h | GAP-005 |
| 7 | Sync Agent Implementation | 📋 TODO | 4h | GAP-006 |
| 8 | MCP usage documentation | 📋 TODO | 1h | GAP-019 |
| 9 | Opik Dashboard startup | 📋 TODO | 30min | - |

### Low Priority (P2)

| # | Task | Status | Effort | GAP |
|---|------|--------|--------|-----|
| 10 | ChromaDB v2 Test Update | ⏸️ Hold | 2h | GAP-007 |
| 11 | Agent UI Image | 📋 TODO | 30min | GAP-008 |
| 12 | CI/CD Pipeline | 📋 TODO | 2h | GAP-010 |
| 13 | Grok/xAI API Key | ⏳ Pending | 15min | GAP-004 |

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | TypeDB Container | ✅ COMPLETE |
| **Phase 2** | Governance MCP | ✅ COMPLETE |
| **Phase 3** | Stabilization & v1.0 | ✅ COMPLETE |
| **Phase 4** | Cross-Workspace Integration | ✅ COMPLETE |
| **Phase 5** | External MCP Integration | ✅ COMPLETE |
| **Phase 6** | Agent UI Framework | ✅ COMPLETE |
| **Phase 7** | TypeDB-First Migration | ✅ COMPLETE |
| **Phase 8** | E2E Testing Framework | ✅ COMPLETE |
| **Phase 9** | Agentic Platform UI/MCP | ✅ COMPLETE |

> Details: [R&D-BACKLOG.md](docs/backlog/R&D-BACKLOG.md)

---

## Recently Completed (This Session)

| Task | Completed | Description |
|------|-----------|-------------|
| P10.1 | 2024-12-25 | GitHub Actions E2E workflow (e2e-certification.yml) |
| P10.2 | 2024-12-25 | CI workflow (ci.yml) |
| P10.3 | 2024-12-25 | Certification issue template |
| P7.3 | 2024-12-25 | TypeDB data routing (DataRouter) |
| P7.4 | 2024-12-25 | ChromaDB migration tool (ChromaMigration) |
| P7.5 | 2024-12-25 | ChromaDB sunset (ChromaReadOnly) |
| P9.6 | 2024-12-25 | Real-time Rule Monitoring (RuleMonitor + UI) |
| P9.7 | 2024-12-25 | Journey Pattern Analyzer (recurring questions) |
| P9.8 | 2024-12-25 | Capability Journey Certification (E2E tests) |
| RULE-024 | 2024-12-25 | AMNESIA Protocol (context recovery) |

---

## Gap Summary

| Priority | Count | Top Items |
|----------|-------|-----------|
| HIGH | 1 | GAP-020 Cross-project queries |
| Medium | 9 | GAP-004, GAP-005, GAP-006, GAP-009, GAP-014, GAP-015, GAP-019, GAP-021 |
| Low | 2 | GAP-007, GAP-008, GAP-010 |

> Details: [GAP-INDEX.md](docs/gaps/GAP-INDEX.md)

---

## Test Summary

| Suite | Tests | Status |
|-------|-------|--------|
| data_router | 22 | ✅ |
| chroma_migration | 19 | ✅ |
| chroma_readonly | 17 | ✅ |
| governance_ui | 36 | ✅ |
| rule_monitor | 20 | ✅ |
| journey_analyzer | 24 | ✅ |
| **Total (P7+P9)** | **138** | ✅ |

---

## Task Status Legend

| Symbol | Status |
|--------|--------|
| ✅ | Completed |
| 🚧 | In Progress |
| ⏳ | Pending |
| 📋 | Not Started |
| ⏸️ | On Hold |

---

## Maintenance

- Update this index when adding new tasks
- Archive completed tasks to [TASKS-COMPLETED.md](docs/tasks/TASKS-COMPLETED.md)
- Track gaps in [GAP-INDEX.md](docs/gaps/GAP-INDEX.md)
- R&D items go to [R&D-BACKLOG.md](docs/backlog/R&D-BACKLOG.md)

---

*Per RULE-012: Deep Sleep Protocol - document hygiene*
*Per RULE-024: AMNESIA Protocol - recovery-friendly documents*
