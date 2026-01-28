# GAP-INFRA-HEALTH-UI: Infrastructure Health UI Deep Integration

**Priority:** MEDIUM | **Category:** epic/ui | **Status:** OPEN
**Discovered:** 2026-01-20 | **Source:** Session audit request

---

## Epic Overview

Deep integration of Infrastructure Health UI with healthcheck hooks, MCP servers, and document service for comprehensive observability.

---

## Current State

[agent/governance_ui/views/infra_view.py](../../../agent/governance_ui/views/infra_view.py) (297 lines)

| Feature | Status | Location |
|---------|--------|----------|
| Service cards (5 containers) | ✓ | lines 93-112 |
| System stats (memory, procs, hash) | ✓ | lines 115-173 |
| MCP server status chips | ✓ | lines 176-213 |
| Recovery buttons | ✓ | lines 216-267 |

---

## Requested Enhancements

Per user request (2026-01-20):

### 1. Health Hooks & Services Integration
**Status:** PARTIAL
**Gap:** Hook state (`.healthcheck_state.json`, `.entropy_state.json`) not exposed in UI
**Action:** Add API endpoint + UI cards for hook state

### 2. MCP Server Status for All MCPs
**Status:** PARTIAL
**Gap:** Shows chips but no details (connection attempts, last success, errors)
**Action:** Expand MCP panel with connection history

### 3. MCP Audit Logs via Document Service
**Status:** NOT IMPLEMENTED
**Gap:** No way to view MCP tool call logs in UI
**Action:** Document service subdomain for MCP logs + viewer component

### 4. Container Metadata/Settings/Logs via Document Service
**Status:** NOT IMPLEMENTED
**Gap:** No container log viewer
**Action:** Document service integration for `podman logs` output

### 5. Python Process Tracking
**Status:** PARTIAL (count only)
**Gap:** No process details (PID, command, memory)
**Action:** Process list with kill capability

### 6. Recovery Action Audit Log
**Status:** NOT IMPLEMENTED
**Gap:** Recovery actions not logged persistently
**Action:** TypeDB or file-based audit trail for recovery actions

### 7. Health Hash Decomposition & Audit Log
**Status:** PARTIAL (hash only)
**Gap:** No breakdown of what contributes to hash
**Action:** Show hash components (service status, entropy level, etc.)

---

## Subtasks

| ID | Task | Priority | Complexity |
|----|------|----------|------------|
| INFRA-UI-001 | Hook state API + cards | HIGH | MEDIUM |
| INFRA-UI-002 | MCP connection history details | MEDIUM | LOW |
| INFRA-UI-003 | MCP audit log viewer (document service) | MEDIUM | HIGH |
| INFRA-UI-004 | Container log viewer (document service) | MEDIUM | HIGH |
| INFRA-UI-005 | Process list with details | LOW | LOW |
| INFRA-UI-006 | Recovery audit log | MEDIUM | MEDIUM |
| INFRA-UI-007 | Health hash decomposition | LOW | LOW |

---

## Dependencies

- GAP-MONITOR-IPC-001: Audit file bridge (for MCP logs)
- Document service exists: `doc_get`, `docs_list` MCP tools
- Healthcheck hooks already write state files

---

## Acceptance Criteria

1. [ ] Hook state visible in Infrastructure Health UI
2. [ ] MCP servers show connection history
3. [ ] MCP audit logs viewable via document service
4. [ ] Container logs viewable via document service
5. [ ] Process list shows PID, command, memory
6. [ ] Recovery actions logged and viewable
7. [ ] Health hash shows component breakdown

---

*Per GOV-TRANSP-01-v1: Epic documented with full scope*
