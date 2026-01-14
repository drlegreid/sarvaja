# Test Registry - Rule Traceability

**Per TEST-004:** Test restructuring for rules conformity.
**Updated:** 2026-01-14

## Test Categories by Rule

### Governance Rules (SESSION, REPORT, GOV)

| Test File | Rule(s) | Category |
|-----------|---------|----------|
| test_session_collector.py | SESSION-EVID-01-v1 | Evidence |
| test_session_memory.py | SESSION-EVID-01-v1 | Evidence |
| test_session_viewer.py | SESSION-EVID-01-v1 | Evidence |
| test_mcp_evidence.py | SESSION-EVID-01-v1 | Evidence |
| test_rules_governance.py | GOV-RULE-01-v1 | Governance |
| test_rules_crud.py | GOV-RULE-01-v1 | Governance |
| test_rule_impact.py | GOV-RULE-01-v1 | Governance |
| test_rule_quality.py | GOV-RULE-01-v1 | Governance |
| test_agent_trust.py | GOV-BICAM-01-v1 | Trust |
| test_trust_dashboard.py | GOV-BICAM-01-v1 | Trust |
| test_delegation.py | GOV-BICAM-01-v1 | Trust |

### Technical Rules (ARCH, UI)

| Test File | Rule(s) | Category |
|-----------|---------|----------|
| test_mcp_server_split.py | ARCH-MCP-02-v1 | Architecture |
| test_mcp_tools.py | ARCH-MCP-02-v1 | Architecture |
| test_mcp_tasks.py | ARCH-MCP-02-v1 | Architecture |
| test_mcp_agents.py | ARCH-MCP-02-v1 | Architecture |
| test_governance_ui.py | UI-LOADER-01-v1, UI-TRACE-01-v1 | UI |
| test_reactive_loaders.py | UI-LOADER-01-v1 | UI |
| test_trace_bar.py | UI-TRACE-01-v1 | UI |
| test_trame_ui.py | UI-* | UI |
| test_task_ui.py | TASK-LIFE-01-v1 | UI |
| test_task_lifecycle.py | TASK-LIFE-01-v1 | Lifecycle |

### Operational Rules (WORKFLOW, TEST, SAFETY)

| Test File | Rule(s) | Category |
|-----------|---------|----------|
| test_dsm_tracker_*.py | WORKFLOW-DSP-01-v1 | DSP |
| test_destructive_checker.py | SAFETY-DESTR-01-v1 | Safety |
| test_health.py | SAFETY-HEALTH-01-v1 | Health |
| test_claude_hooks.py | SAFETY-* | Safety |
| test_data_integrity.py | TEST-GUARD-01-v1 | Testing |
| test_benchmark.py | TEST-COMP-01-v1 | Testing |

### Infrastructure Rules (CONTAINER, DOC)

| Test File | Rule(s) | Category |
|-----------|---------|----------|
| test_chroma_*.py | CONTAINER-DEV-01-v1 | Container |
| test_vector_store.py | CONTAINER-DEV-01-v1 | Container |
| test_document_service.py | DOC-LINK-01-v1 | Docs |
| test_file_viewer.py | DOC-SIZE-01-v1 | Docs |

## E2E Tests (BDD)

| Feature File | Rule(s) | Category |
|--------------|---------|----------|
| dashboard.feature | TEST-BDD-01-v1 | E2E |
| crud_operations.feature | TEST-BDD-01-v1 | E2E |

## Test Organization

```
tests/
├── shared/              # Shared utilities (TEST-001)
│   ├── factories.py     # Data factories using implementation models
│   └── pages.py         # Page objects for E2E tests
├── e2e/                 # E2E tests (TEST-BDD-01-v1)
│   ├── features/        # Gherkin feature files
│   └── steps/           # Step definitions
├── heuristics/          # Exploratory test heuristics
└── test_*.py            # Unit/Integration tests
```

## Coverage by Rule Priority

| Priority | Rules | Tests | Coverage |
|----------|-------|-------|----------|
| CRITICAL | 16 | ~50 files | High |
| HIGH | 12 | ~30 files | Medium |
| MEDIUM | 15 | ~20 files | Medium |
| LOW | 8 | ~10 files | Low |

---
*Per TEST-004: Align tests with RULE-* structure*
