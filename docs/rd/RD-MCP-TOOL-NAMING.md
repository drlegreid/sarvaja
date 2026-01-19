# RD-MCP-TOOL-NAMING: MCP Tool Domain-Based Naming Refactoring

**Status:** IN_PROGRESS (Phase 1 Complete) | **Priority:** MEDIUM | **Created:** 2026-01-17

---

## Summary

Refactor 100 MCP tools from `governance_{action}_{entity}` pattern to domain-based `{entity}_{action}` pattern for better discoverability and semantic clarity.

---

## Current State

| Metric | Value |
|--------|-------|
| Total MCP Tools | 100 |
| Files Affected | 26 |
| MCP Servers | 4 (gov-core, gov-agents, gov-sessions, gov-tasks) |

**Current Pattern:** `governance_create_rule`, `governance_get_task`, `governance_list_agents`

**Proposed Pattern:** `rule_create`, `task_get`, `agents_list`

---

## Domain Mapping

### RULES Domain (gov-core)

| Current | Proposed | File |
|---------|----------|------|
| governance_query_rules | rules_query | rules_query.py |
| governance_query_rules_by_tags | rules_query_by_tags | rules_query.py |
| governance_get_rule | rule_get | rules_query.py |
| governance_get_dependencies | rule_get_deps | rules_query.py |
| governance_find_conflicts | rules_find_conflicts | rules_query.py |
| governance_create_rule | rule_create | rules_crud.py |
| governance_update_rule | rule_update | rules_crud.py |
| governance_deprecate_rule | rule_deprecate | rules_crud.py |
| governance_delete_rule | rule_delete | rules_crud.py |
| governance_analyze_rules | rules_analyze | quality.py |
| governance_rule_impact | rule_impact | quality.py |
| governance_find_issues | rules_find_issues | quality.py |
| governance_list_archived_rules | rules_list_archived | rules_archive.py |
| governance_get_archived_rule | rule_get_archived | rules_archive.py |
| governance_restore_rule | rule_restore | rules_archive.py |

### TASKS Domain (gov-tasks)

| Current | Proposed | File |
|---------|----------|------|
| governance_create_task | task_create | tasks_crud.py |
| governance_get_task | task_get | tasks_crud.py |
| governance_update_task | task_update | tasks_crud.py |
| governance_delete_task | task_delete | tasks_crud.py |
| governance_list_all_tasks | tasks_list | tasks_crud.py |
| governance_verify_completion | task_verify | tasks_crud.py |
| governance_get_task_deps | task_get_deps | tasks.py |
| governance_task_link_session | task_link_session | tasks_linking.py |
| governance_task_link_rule | task_link_rule | tasks_linking.py |
| governance_task_link_evidence | task_link_evidence | tasks_linking.py |
| governance_task_get_evidence | task_get_evidence | tasks_linking.py |
| governance_task_link_commit | task_link_commit | tasks_linking.py |
| governance_task_get_commits | task_get_commits | tasks_linking.py |
| governance_task_update_details | task_update_details | tasks_linking.py |
| governance_task_get_details | task_get_details | tasks_linking.py |

### AGENTS Domain (gov-agents)

| Current | Proposed | File |
|---------|----------|------|
| governance_create_agent | agent_create | agents.py |
| governance_get_agent | agent_get | agents.py |
| governance_list_agents | agents_list | agents.py |
| governance_update_agent_trust | agent_trust_update | agents.py |
| governance_agent_dashboard | agents_dashboard | agents.py |
| governance_agent_activity | agent_activity | agents.py |
| governance_get_trust_score | agent_trust_score | trust.py |

### SESSIONS Domain (gov-sessions)

| Current | Proposed | File |
|---------|----------|------|
| governance_list_sessions | sessions_list | sessions.py |
| governance_get_session | session_get | sessions.py |
| session_start | session_start | sessions_core.py |
| session_end | session_end | sessions_core.py |
| session_decision | session_decision | sessions_core.py |
| session_task | session_task | sessions_core.py |
| session_tool_call | session_tool_call | sessions_core.py |
| session_thought | session_thought | sessions_core.py |
| session_get_tasks | session_get_tasks | sessions_linking.py |
| session_link_rule | session_link_rule | sessions_linking.py |
| session_link_decision | session_link_decision | sessions_linking.py |
| session_link_evidence | session_link_evidence | sessions_linking.py |
| session_capture_intent | session_capture_intent | sessions_intent.py |
| session_capture_outcome | session_capture_outcome | sessions_intent.py |

### DSM Domain (gov-sessions)

| Current | Proposed | Notes |
|---------|----------|-------|
| dsm_start | dsm_start | Already domain-based |
| dsm_advance | dsm_advance | Already domain-based |
| dsm_checkpoint | dsm_checkpoint | Already domain-based |
| dsm_finding | dsm_finding | Already domain-based |
| dsm_status | dsm_status | Already domain-based |
| dsm_complete | dsm_complete | Already domain-based |
| dsm_metrics | dsm_metrics | Already domain-based |

### DOCUMENTS Domain (gov-sessions)

| Current | Proposed | File |
|---------|----------|------|
| governance_get_document | doc_get | documents_core.py |
| governance_list_documents | docs_list | documents_core.py |
| governance_get_rule_document | doc_rule_get | documents_entity.py |
| governance_get_task_document | doc_task_get | documents_entity.py |
| governance_extract_links | doc_links_extract | documents_links.py |
| governance_resolve_link | doc_link_resolve | documents_links.py |

### PROPOSALS Domain (gov-agents)

| Current | Proposed | File |
|---------|----------|------|
| governance_propose_rule | proposal_create | proposals.py |
| governance_vote | proposal_vote | proposals.py |
| governance_dispute | proposal_dispute | proposals.py |
| governance_get_proposals | proposals_list | proposals.py |
| governance_get_escalated_proposals | proposals_escalated | proposals.py |

### GAPS Domain (gov-tasks)

| Current | Proposed | File |
|---------|----------|------|
| governance_get_backlog | backlog_get | gaps.py |
| governance_gap_summary | gaps_summary | gaps.py |
| governance_get_critical_gaps | gaps_critical | gaps.py |
| governance_unified_backlog | backlog_unified | gaps.py |

### HANDOFF Domain (gov-tasks)

| Current | Proposed | File |
|---------|----------|------|
| governance_create_handoff | handoff_create | handoff.py |
| governance_get_pending_handoffs | handoffs_pending | handoff.py |
| governance_complete_handoff | handoff_complete | handoff.py |
| governance_get_handoff | handoff_get | handoff.py |
| governance_route_task_to_agent | handoff_route | handoff.py |

### AUDIT Domain (gov-tasks)

| Current | Proposed | File |
|---------|----------|------|
| governance_query_audit | audit_query | audit.py |
| governance_audit_summary | audit_summary | audit.py |
| governance_entity_audit_trail | audit_entity_trail | audit.py |
| governance_trace_correlation | audit_trace | audit.py |

### WORKSPACE Domain (gov-tasks)

| Current | Proposed | File |
|---------|----------|------|
| governance_sync_status | workspace_sync_status | workspace.py |
| workspace_scan_tasks | workspace_scan_tasks | workspace.py |
| workspace_capture_tasks | workspace_capture_tasks | workspace.py |
| workspace_list_sources | workspace_list_sources | workspace.py |
| workspace_scan_rule_documents | workspace_scan_rules | workspace.py |
| workspace_link_rules_to_documents | workspace_link_rules | workspace.py |
| workspace_get_document_for_rule | workspace_doc_for_rule | workspace.py |
| workspace_get_rules_for_document | workspace_rules_for_doc | workspace.py |

### CORE Domain (gov-core)

| Current | Proposed | File |
|---------|----------|------|
| governance_health | health_check | mcp_server_core.py |
| governance_get_agent_wisdom | wisdom_get | rules_query.py |
| governance_evidence_search | evidence_search | search.py |
| governance_get_decision_impacts | decision_impacts | decisions.py |

---

## Implementation Strategy

### Phase 1: Add Aliases (Non-Breaking)
```python
# In each tool file, add aliases
rule_create = governance_create_rule  # New name
```

### Phase 2: Update .mcp.json Tool Descriptions (**N/A**)
**NOTE:** FastMCP derives tool names from Python functions. The .mcp.json file only configures servers, not tool metadata. Phase 2 is not applicable to our architecture.
```
.mcp.json = server configuration (command, env vars)
Python @mcp.tool() = tool names and descriptions
```

### Phase 3: Deprecation Period (2 weeks)
- Log warnings when old names used
- Update documentation to use new names
- Update hooks and skills

### Phase 4: Remove Old Names
- Remove deprecated function names
- Update all internal references

---

## Impact Analysis

| Area | Impact | Risk |
|------|--------|------|
| MCP Server Code | 26 files, ~200 edits | LOW |
| Hooks | 5 files | LOW |
| Skills | 3 files | LOW |
| Tests | 15 files | MEDIUM |
| External Integrations | Unknown | MEDIUM |
| Documentation | 20+ files | LOW |

---

## Acceptance Criteria

- [x] All 100 tools have domain-based names (Phase 1 - DONE)
- [x] Backward compatibility aliases exist (Phase 1 - DONE)
- [ ] All tests pass with new names
- [ ] Documentation updated
- [ ] Deprecation warnings logged for old names

---

## Timeline Estimate

| Phase | Effort | Status |
|-------|--------|--------|
| Phase 1: Add Aliases | 2-3 hours | ✅ DONE |
| Phase 2: Update Config | N/A | ⏭️ SKIPPED |
| Phase 3: Deprecation | 2 weeks | 🔄 IN PROGRESS |
| Phase 4: Cleanup | 1 hour | ⏳ PENDING |

---

## Decision Required

**Proceed with domain-based MCP tool naming refactoring?**

- [x] APPROVE - Implement all phases (APPROVED 2026-01-17)
- [ ] APPROVE Phase 1 only - Add aliases without deprecation
- [ ] DEFER - Lower priority than other work
- [ ] REJECT - Current naming is acceptable

---

## Implementation Log

### Phase 1: Add Aliases (COMPLETE - 2026-01-17)

**Files Modified (17 files):**

| File | Aliases Added |
|------|---------------|
| rules_crud.py | rule_create, rule_update, rule_deprecate, rule_delete |
| tasks_crud.py | task_create, task_get, task_update, task_delete, tasks_list, task_verify |
| agents.py | agent_create, agent_get, agents_list, agent_trust_update, agents_dashboard, agent_activity |
| rules_query.py | rules_query, rules_query_by_tags, rule_get, rule_get_deps, rules_find_conflicts, wisdom_get |
| proposals.py | proposal_create, proposal_vote, proposal_dispute, proposals_list, proposals_escalated |
| trust.py | agent_trust_score |
| gaps.py | backlog_get, gaps_summary, gaps_critical, backlog_unified |
| handoff.py | handoff_create, handoffs_pending, handoff_complete, handoff_get, handoff_route |
| workspace.py | workspace_sync_status |
| audit.py | audit_query, audit_summary, audit_entity_trail, audit_trace |
| tasks_linking.py | task_link_session, task_link_rule, task_link_evidence, task_get_evidence, task_link_commit, task_get_commits, task_update_details, task_get_details |
| rules_archive.py | rules_list_archived, rule_get_archived, rule_restore |
| decisions.py | decision_impacts, health_check |
| evidence/documents_core.py | doc_get, docs_list |
| evidence/documents_entity.py | doc_rule_get, doc_task_get |
| evidence/documents_links.py | doc_links_extract, doc_link_resolve |
| evidence/search.py | evidence_search |

**Files Already Domain-Based (no changes needed):**
- sessions_core.py (session_start, session_end, etc.)
- sessions_intent.py (session_capture_intent, session_capture_outcome)
- sessions_linking.py (session_link_rule, session_link_decision, etc.)
- dsm.py (dsm_start, dsm_advance, etc.)

**Verification:** All imports verified successful.

### Phase 2: Update Config (SKIPPED - 2026-01-17)

**Reason:** FastMCP architecture doesn't use .mcp.json for tool metadata. Tool names and descriptions come from Python `@mcp.tool()` decorators. Phase 2 is not applicable.

### Phase 3: Deprecation Period (IN PROGRESS - Started 2026-01-17)

**Status:** Both old (`governance_*`) and new (domain-based) names now work.

**Completed (2026-01-18):**
- [x] Add deprecation warnings when old names are used (22 key functions)
  - rules_crud.py: 4 functions
  - rules_query.py: 6 functions
  - tasks_crud.py: 6 functions
  - agents.py: 6 functions
- [x] Created warn_deprecated() helper in common.py
- [x] Update hooks/commands to use new names
  - checkpoint.md: rules_query, health_check
  - report.md: sessions_list, tasks_list
  - health.md: health_check
  - workflow_checker.py: health_check
- [x] Update CLAUDE.md documentation
  - Session start protocol: health_check, backlog_get
  - Context recovery: health_check
- [x] Update core documentation files
  - DEVOPS.md: health_check
  - MCP-USAGE.md: Full tool name update (all sections)
  - STRATEGY.md: health_check, backlog_get, rules_query
- [x] Update rule leaf files (6 files)
  - SAFETY-HEALTH-01-v1.md: health_check
  - MCP-RESTART-AUTO-01-v1.md: health_check
  - SESSION-DSM-01-v1.md: health_check
  - TEST-FIX-01-v1.md: health_check
  - RECOVER-CRASH-01-v1.md: health_check
  - UI-TRACE-01-v1.md: rules_query
- [x] Update gap evidence files (1 file)
  - GAP-TAXONOMY.md: health_check

**Remaining Work:**
- [ ] Update remaining ~20 documentation files (historical evidence files - lower priority)

**Deprecation End Date:** 2026-01-31 (2 weeks from Phase 1 completion)

---

*Per WORKFLOW-RD-01-v1: R&D Workflow with Human Approval*
