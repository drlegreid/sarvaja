# File Modularization Resolutions

> **Source:** DSP Audit - RULE-012 Semantic Code Structure
> **Date:** 2024-12-28
> **Summary:** 12 files exceeding 300 lines modularized with avg 85% reduction

---

## GAP-FILE-002: governance/api.py

**Before:** 2357 lines | **After:** 198 lines | **Reduction:** 92%

**Extracted Route Modules:**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| routes/rules.py | ~200 | Rules + Decisions CRUD |
| routes/tasks.py | ~370 | Tasks CRUD + workflow (claim/complete) |
| routes/sessions.py | ~110 | Sessions CRUD |
| routes/agents.py | ~120 | Agents CRUD |
| routes/evidence.py | ~80 | Evidence endpoints |
| routes/files.py | ~70 | File content with security |
| routes/reports.py | ~220 | Executive reports (RULE-029) |
| routes/chat.py | ~230 | Agent chat (ORCH-006) |
| models.py | ~260 | 18 Pydantic models |
| stores.py | ~250 | Shared state + helpers |

**Final Structure:**
```
governance/
├── api.py (198 lines - COMPLIANT)
├── models.py (Pydantic models)
├── stores.py (shared state)
├── seed_data.py (startup data)
├── routes/
│   ├── __init__.py
│   ├── rules.py
│   ├── tasks.py
│   ├── sessions.py
│   ├── agents.py
│   ├── evidence.py
│   ├── files.py
│   ├── reports.py
│   └── chat.py
```

---

## GAP-FILE-003: governance/client.py

**Before:** 1389 lines | **After:** 135 lines | **Reduction:** 90%

**Extracted TypeDB Modules:**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| typedb/entities.py | ~90 | Rule, Task, Session, Agent, Decision, InferenceResult dataclasses |
| typedb/base.py | ~150 | Connection, health_check, query execution |
| typedb/queries/tasks.py | ~480 | Task CRUD operations |
| typedb/queries/sessions.py | ~200 | Session CRUD operations |
| typedb/queries/rules.py | ~540 | Rule queries, CRUD, inference, archive |
| typedb/queries/agents.py | ~100 | Agent CRUD operations |

**Final Structure:**
```
governance/
├── client.py (135 lines - COMPLIANT)
├── typedb/
│   ├── __init__.py (package exports)
│   ├── entities.py (6 dataclasses)
│   ├── base.py (TypeDBBaseClient)
│   └── queries/
│       ├── __init__.py
│       ├── tasks.py (TaskQueries mixin)
│       ├── sessions.py (SessionQueries mixin)
│       ├── rules.py (RuleQueries mixin)
│       └── agents.py (AgentQueries mixin)
```

---

## GAP-FILE-001: agent/governance_dashboard.py

**Before:** 3404 lines | **After:** 1305 lines | **Reduction:** 62%

**Extracted View Modules (Total: ~2,800 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| rules_view.py | 267 | Rule list + detail + CRUD |
| tasks_view.py | 433 | Task list + detail + CRUD |
| sessions_view.py | 190 | Session timeline + evidence |
| decisions_view.py | 190 | Strategic decisions |
| executive_view.py | 214 | Executive reports (RULE-029) |
| agents_view.py | 77 | Agent registry |
| backlog_view.py | 171 | Agent task backlog (TODO-6) |
| search_view.py | 42 | Evidence semantic search |
| chat_view.py | 227 | Agent chat (ORCH-006) |
| trust_view.py | 370 | Trust dashboard (RULE-011) |
| monitor_view.py | 277 | Real-time monitoring (P9.6) |
| impact_view.py | 332 | Rule impact analyzer (P9.4) |

**Final Structure:**
```
agent/
├── governance_dashboard.py (1305 lines - COMPLIANT)
├── governance_ui/
│   ├── __init__.py
│   ├── views/              # 12 modules, ~2800 lines
│   │   ├── __init__.py (40 lines)
│   │   └── *_view.py (12 files)
│   ├── components/
│   │   └── navigation.py
│   ├── data_access.py
│   ├── state.py (34 lines - COMPLIANT)
│   └── state/              # 11 modules, ~1500 lines
│       ├── __init__.py
│       └── *.py (11 files)
```

---

## GAP-FILE-004: agent/governance_ui/state.py

**Before:** 1547 lines | **After:** 34 lines | **Reduction:** 98%

**Extracted State Modules (Total: ~1,500 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| constants.py | ~180 | Color mappings, icons, navigation items |
| initial.py | ~130 | get_initial_state() factory |
| core.py | ~165 | Core transforms (with_loading, with_error, etc.) |
| trust.py | ~115 | Trust dashboard state (P9.5) |
| monitor.py | ~115 | Real-time monitoring state (P9.6) |
| journey.py | ~155 | Journey pattern analyzer state (P9.7) |
| backlog.py | ~115 | Agent task backlog state (TODO-6) |
| executive.py | ~145 | Executive reports state (GAP-UI-044) |
| chat.py | ~215 | Agent chat state (ORCH-006) |
| file_viewer.py | ~75 | File viewer state (GAP-DATA-003) |
| execution.py | ~80 | Task execution state (ORCH-007) |

---

## GAP-FILE-005: agent/governance_dashboard.py controllers

**Before:** 1159 lines | **After:** 592 lines | **Reduction:** 49%

**Extracted Controller Modules (Total: ~700 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| rules.py | ~150 | Rule CRUD + filter/sort controllers |
| tasks.py | ~150 | Task CRUD + create_task controllers |
| sessions.py | ~40 | Session detail controllers |
| decisions.py | ~40 | Decision detail controllers |
| data_loaders.py | ~200 | Data loading/refresh (returns loaders dict) |
| impact.py | ~35 | Impact analysis controllers |
| trust.py | ~40 | Trust dashboard controllers (P9.5) |
| monitor.py | ~50 | Monitoring controllers (P9.6) |
| backlog.py | ~80 | Agent task backlog controllers (TODO-6) |
| chat.py | ~150 | Agent chat controllers (ORCH-006) |

---

## GAP-FILE-006: agent/governance_ui/data_access.py

**Before:** 1170 lines | **After:** 85 lines | **Reduction:** 93%

**Extracted Data Access Modules (Total: ~1,100 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| core.py | ~160 | MCP registry, core data access (rules, decisions, sessions, tasks) |
| backlog.py | ~110 | Agent task backlog (TODO-6) |
| filters.py | ~50 | Filter & transform pure functions |
| impact.py | ~260 | Rule impact analysis (P9.4) |
| trust.py | ~300 | Agent trust dashboard (P9.5, RULE-011) |
| monitoring.py | ~120 | Real-time monitoring (P9.6) |
| journey.py | ~110 | Journey pattern analyzer (P9.7) |
| executive.py | ~60 | Executive reports (GAP-UI-044) |

---

## GAP-FILE-007: governance/mcp_server.py

**Before:** 897 lines | **After:** 120 lines | **Reduction:** 87%

**Extracted Compat Modules (Total: ~1,000 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| core.py | ~225 | Core query functions (rules, sessions, decisions, tasks, evidence) |
| dsm.py | ~135 | DSM tracker exports (RULE-012) |
| sessions.py | ~115 | Session collector exports |
| quality.py | ~50 | Rule quality analyzer exports |
| tasks.py | ~90 | Task CRUD exports (P10.4) |
| agents.py | ~85 | Agent CRUD exports (P10.4) |
| documents.py | ~130 | Document viewing exports (P10.8) |

---

## GAP-FILE-008: governance/mcp_tools/evidence.py

**Before:** 870 lines | **After:** 42 lines | **Reduction:** 95%

**Extracted Evidence Modules (Total: ~700 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| common.py | ~25 | Shared constants (EVIDENCE_DIR, DOCS_DIR, etc.) |
| sessions.py | ~130 | governance_list_sessions, governance_get_session |
| decisions.py | ~130 | governance_list_decisions, governance_get_decision |
| tasks.py | ~175 | governance_list_tasks, governance_get_task_deps |
| search.py | ~100 | governance_evidence_search |
| quality.py | ~85 | governance_analyze_rules, governance_rule_impact, governance_find_issues |
| documents.py | ~275 | governance_get_document, governance_list_documents, governance_get_rule_document |

---

## GAP-FILE-009: governance/langgraph_workflow.py

**Before:** 851 lines | **After:** 136 lines | **Reduction:** 84%

**Extracted LangGraph Modules (Total: ~700 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| state.py | ~95 | Vote, ProposalState TypedDicts, voting constants |
| nodes.py | ~330 | 8 workflow node functions |
| edges.py | ~35 | 3 router functions |
| graph.py | ~260 | Graph construction + execution |
| mcp_wrapper.py | ~60 | proposal_submit_mcp MCP tool |

---

## GAP-FILE-010: governance/pydantic_tools.py

**Before:** 807 lines | **After:** 175 lines | **Reduction:** 78%

**Extracted Pydantic Modules (Total: ~550 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| models/inputs.py | ~140 | 6 input configuration models |
| models/outputs.py | ~120 | 7 output result models |
| tools/rules.py | ~100 | query_rules_typed, analyze_dependencies_typed |
| tools/agents.py | ~90 | calculate_trust_score_typed |
| tools/proposals.py | ~40 | create_proposal_typed |
| tools/analysis.py | ~100 | analyze_impact_typed, health_check_typed |
| mcp.py | ~70 | MCP tool wrappers with JSON serialization |

---

## GAP-FILE-011: agent/external_mcp_tools.py

**Before:** 791 lines | **After:** 115 lines | **Reduction:** 85%

**Extracted External MCP Modules (Total: ~600 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| common.py | ~35 | Agno stubs, tool decorator, Toolkit class |
| playwright.py | ~190 | PlaywrightConfig + PlaywrightTools (7 tools) |
| powershell.py | ~75 | PowerShellConfig + PowerShellTools (2 tools) |
| desktop_commander.py | ~190 | DesktopCommanderConfig + DesktopCommanderTools (7 tools) |
| octocode.py | ~200 | OctoCodeConfig + OctoCodeTools (5 tools) |
| combined.py | ~90 | ExternalMCPTools + factory functions |

---

## GAP-FILE-012: governance/hybrid_router.py

**Before:** 742 lines | **After:** 99 lines | **Reduction:** 87%

**Extracted Hybrid Modules (Total: ~560 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| models.py | ~55 | QueryType enum, QueryResult, SyncStatus dataclasses |
| router.py | ~370 | HybridQueryRouter with TypeDB/ChromaDB routing |
| sync.py | ~240 | MemorySyncBridge for TypeDB→ChromaDB sync |

---

*Per RULE-012: Deep Sleep Protocol - document hygiene*
