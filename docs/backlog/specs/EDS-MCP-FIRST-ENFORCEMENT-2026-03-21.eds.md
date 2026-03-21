# EDS: MCP-First Enforcement (EPIC-GOV-TASKS-V2 Phase 8)

**Date:** 2026-03-21
**Rule:** GOV-MCP-FIRST-01-v1 (MANDATORY)
**Status:** PASS — All 9 scenarios validated

---

## Layer 1: Business Intent

**Goal:** Make gov-tasks MCP the exclusive task management interface.
TodoWrite/TODO.md become emergency fallback only when MCP is down.

**User Stories:**
- As a governance agent, I want all tasks managed via MCP so TypeDB is authoritative
- As an operator, I want TODO.md auto-populated from TypeDB for visibility
- As a developer, I want warnings when MCP is available but unused

---

## Layer 2: Actions & Validations

### Scenario 1: Task CRUD via REST API (MCP backend)
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | POST /api/tasks with all metadata | 201, task persisted in TypeDB | PASS |
| 2 | GET /api/tasks/{id} | All fields returned (task_id, status, priority, type, phase, agent_id, workspace_id) | PASS |
| 3 | PUT /api/tasks/{id} status=IN_PROGRESS | Status updated, claimed_at auto-set, workspace_id wired | PASS |
| 4 | PUT /api/tasks/{id} status=DONE | completed_at auto-set | PASS |
| 5 | DELETE /api/tasks/{id} | 204 clean removal | PASS |

### Scenario 2: Workspace-Task Bidirectional Linking
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | PUT /api/tasks/{id} workspace_id=WS-9147535A | workspace_id persisted | PASS |
| 2 | GET /api/workspaces/WS-9147535A/tasks | Task appears in workspace's task list | PASS |

### Scenario 3: Auto-Session Linking
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | POST /api/tasks (no session_id) | linked_sessions auto-populated with active CC session | PASS |

### Scenario 4: Task Listing with Filters
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | GET /api/tasks?status=DONE&limit=5 | Filtered results with pagination (has_more, total) | PASS |

### Scenario 5: Dashboard Tasks View (Playwright)
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | Navigate to Tasks | Table with 213 tasks, 11 columns | PASS |
| 2 | Tab filters visible | All, Available, My Tasks, Completed | PASS |
| 3 | Search + Status + Phase filters | UI controls present and functional | PASS |

### Scenario 6: Task Detail View (Playwright)
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | Click task row | Detail view with Edit/Complete/Delete buttons | PASS |
| 2 | Task Information card | Task ID, Phase, Status displayed | PASS |
| 3 | Assignment card | Agent, Priority displayed | PASS |
| 4 | Execution Log | Timeline with Started/Claimed events | PASS |

### Scenario 7: Health-Aware Enforcement (Unit Tests)
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | MCP healthy + TodoWrite without gov-tasks | MANDATORY warning issued | PASS (18 tests) |
| 2 | MCP down + TodoWrite | No warning (fallback mode) | PASS |
| 3 | Health check cached 60s | No repeated API calls | PASS |

### Scenario 8: TypeDB → TODO.md Sync (Unit Tests)
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | sync_typedb_to_todomd() | Fetches tasks, writes formatted markdown | PASS (16 tests) |
| 2 | sync_fallback_to_typedb() | Imports fallback tasks, marks as synced | PASS |
| 3 | API down gracefully handled | Returns SyncResult with error, no crash | PASS |

### Scenario 9: Server Logs (Log Analyzer)
| Step | Action | Expected | Result |
|------|--------|----------|--------|
| 1 | Check logs during CRUD | Zero task-related errors | PASS |

---

## Layer 3: Locators & Evidence

### API Endpoints
- `POST /api/tasks` — task creation with full metadata
- `GET /api/tasks/{id}` — single task read
- `PUT /api/tasks/{id}` — status transitions, workspace wiring
- `DELETE /api/tasks/{id}` — task removal
- `GET /api/tasks?status=X&limit=N` — filtered listing with pagination
- `GET /api/workspaces/{id}/tasks` — bidirectional workspace query
- `GET /api/tasks/{id}/details` — extended task details
- `GET /api/health` — MCP health check endpoint

### UI Locators (Playwright)
- Nav: `option "Tasks"` → Tasks view
- Search: `textbox "Search tasks..."`
- Tabs: `tab "All"`, `tab "Available"`, `tab "My Tasks"`, `tab "Completed"`
- Filters: `combobox Status`, `combobox Phase`
- Table: `table` with columns: Task ID, Description, Priority, Type, Status, Phase, Agent, Created, Completed, Gap, Docs
- Detail: `button "Edit"`, `button "Complete"`, `button "Delete"`
- Cards: "Task Information" (ID, Phase, Status), "Assignment" (Agent, Priority)
- Timeline: "Execution Log" with event entries

### Evidence Files
- `evidence/test-results/EDS-P8-TASKS-VIEW.png` — Tasks list view
- `evidence/test-results/EDS-P8-TASK-DETAIL.png` — Task detail view

### Test Files
- `tests/unit/test_mcp_usage_enforcer.py` — 18 enforcement tests
- `tests/unit/test_todo_sync_typedb.py` — 16 sync tests

---

## Robot Framework BDD Spec

```robot
*** Settings ***
Library    RequestsLibrary
Library    Browser

*** Variables ***
${API_BASE}    http://localhost:8082
${UI_BASE}     http://localhost:8081

*** Test Cases ***
Task CRUD Create With All Metadata
    [Tags]    api    crud    p8
    ${body}=    Create Dictionary    task_id=RF-TEST-001    name=Robot Test
    ...    status=TODO    priority=HIGH    task_type=test    phase=validation
    ...    agent_id=code-agent    workspace_id=WS-9147535A
    ${resp}=    POST    ${API_BASE}/api/tasks    json=${body}
    Should Be Equal As Integers    ${resp.status_code}    201
    Should Be Equal    ${resp.json()}[task_id]    RF-TEST-001
    Should Be Equal    ${resp.json()}[priority]    HIGH

Task CRUD Read Returns All Fields
    [Tags]    api    crud    p8
    ${resp}=    GET    ${API_BASE}/api/tasks/RF-TEST-001
    Should Be Equal As Integers    ${resp.status_code}    200
    Should Be Equal    ${resp.json()}[status]    TODO
    Should Not Be Empty    ${resp.json()}[linked_sessions]

Task CRUD Update Status Transition
    [Tags]    api    crud    p8
    ${body}=    Create Dictionary    status=IN_PROGRESS    workspace_id=WS-9147535A
    ${resp}=    PUT    ${API_BASE}/api/tasks/RF-TEST-001    json=${body}
    Should Be Equal As Integers    ${resp.status_code}    200
    Should Be Equal    ${resp.json()}[status]    IN_PROGRESS
    Should Be Equal    ${resp.json()}[workspace_id]    WS-9147535A
    Should Not Be Empty    ${resp.json()}[claimed_at]

Workspace Task Bidirectional Query
    [Tags]    api    linking    p8
    ${resp}=    GET    ${API_BASE}/api/workspaces/WS-9147535A/tasks
    Should Be Equal As Integers    ${resp.status_code}    200
    Should Be True    ${resp.json()}[total] >= 1

Task CRUD Delete
    [Tags]    api    crud    p8
    ${resp}=    DELETE    ${API_BASE}/api/tasks/RF-TEST-001
    Should Be Equal As Integers    ${resp.status_code}    204

Task List With Filters And Pagination
    [Tags]    api    listing    p8
    ${resp}=    GET    ${API_BASE}/api/tasks    params=status=DONE&limit=5
    Should Be Equal As Integers    ${resp.status_code}    200
    Should Be True    ${resp.json()}[pagination][total] > 0

Dashboard Tasks View Shows Table
    [Tags]    ui    playwright    p8
    New Browser    chromium    headless=true
    New Page    ${UI_BASE}
    Click    text=Tasks
    Get Text    css=table    contains    Task ID
    Get Element Count    css=tr    >    1

Task Detail View Shows Entity Wiring
    [Tags]    ui    playwright    p8
    New Browser    chromium    headless=true
    New Page    ${UI_BASE}
    Click    text=Tasks
    Click    text=BUG-007
    Get Text    css=h2    contains    Lifecycle test
    Get Text    body    contains    Task Information
    Get Text    body    contains    Assignment
    Get Text    body    contains    Execution Log

MCP Health Check Returns 200
    [Tags]    api    health    p8
    ${resp}=    GET    ${API_BASE}/api/health
    Should Be Equal As Integers    ${resp.status_code}    200
    Should Be Equal    ${resp.json()}[typedb_connected]    ${TRUE}
```

---

*Generated: 2026-03-21 | EPIC-GOV-TASKS-V2 Phase 8 | 3-MCP Triad Validated*
