# EDS: MCP Task System V2 — 2026-03-20

> Per TEST-EXPLSPEC-01-v1: Exploratory Dynamic Specification
> Per EPIC-GOV-TASKS-V2: Task MCP System Rehabilitation

## Discovery Context
- MCP Server: gov-tasks
- TypeDB: localhost:1729
- Tool chain: 25 MCP tools across 4 modules
- Phases covered: P1 (Schema), P2 (Auto-Link), P3 (Workspace), P4 (Task-WS Link)
- Date: 2026-03-20

---

## Layer 1: Business Scenarios

### Feature: Task CRUD via MCP
```gherkin
Feature: Task CRUD via MCP
  As a governance agent
  I want to create, read, update, and delete tasks via MCP tools
  So that TypeDB remains the source of truth for all task state

  Scenario: Full lifecycle
    Given TypeDB is available
    When I create a task via task_create
    Then task_get returns the created task
    When I update the task via task_update with status="IN_PROGRESS"
    Then task_get reflects the new status
    When I delete the task via task_delete with confirm=True
    Then task_get returns an error for that task_id

  Scenario: Create with auto-generated ID
    Given task_type="bug" and no task_id provided
    When I call task_create
    Then task_id follows META-TAXON-01-v1 pattern (e.g., BUG-001)

  Scenario: Pagination
    Given multiple tasks exist in TypeDB
    When I call tasks_list with limit=2, offset=0
    And I call tasks_list with limit=2, offset=2
    Then the two pages contain disjoint task IDs

  Scenario: Filter by status
    Given tasks with status OPEN and IN_PROGRESS exist
    When I call tasks_list with status="OPEN"
    Then all returned tasks have status="OPEN"
```

### Feature: Task Linking via MCP
```gherkin
Feature: Task Linking via MCP
  As a governance agent
  I want to link tasks to sessions, workspaces, documents, and commits
  So that task provenance is fully traceable in TypeDB

  Scenario: Auto-link to session on create
    Given an active session exists
    When I call task_create with session_id
    Then the task is linked to that session (completed-in relation)

  Scenario: Auto-link on status transition
    Given an active session exists and a task is OPEN
    When I call task_update with status="IN_PROGRESS"
    Then the task auto-links to the active session (per DATA-LINK-01-v1)

  Scenario: Link to workspace
    When I call task_create with workspace_id="WS-001"
    Then task is assigned to workspace (workspace-has-task relation)

  Scenario: Link document to task
    When I call task_link_document with document_path
    Then a document-references-task relation is created

  Scenario: Link evidence to task
    When I call task_link_evidence with evidence_path
    Then an evidence-supports relation is created

  Scenario: Link commit to task
    When I call task_link_commit with a valid hex SHA
    Then a task-commit relation is created
```

### Feature: Task Detail Management
```gherkin
Feature: Task Detail Management
  As a governance agent
  I want to capture intent, outcome, and detail sections per task
  So that decision context is preserved

  Scenario: Capture intent
    When I call task_capture_intent with goal and planned_steps
    Then the task records intent metadata

  Scenario: Capture outcome
    When I call task_capture_outcome with status, achieved, deferred
    Then the task records outcome metadata

  Scenario: Update detail sections
    When I call task_update_details with business="context"
    Then task_get_details returns the business section

  Scenario: Verify task
    When I call task_verify with method, evidence, test_passed=True
    Then the task records verification evidence
```

### Feature: Error Handling
```gherkin
Feature: Error Handling
  As a governance agent
  I want clear error messages for invalid operations
  So that I can recover gracefully

  Scenario: Get nonexistent task
    When I call task_get with a nonexistent task_id
    Then the result contains an error with "not found"

  Scenario: Delete without confirmation
    When I call task_delete with confirm=False
    Then the result contains an error requiring confirm=True

  Scenario: Update with no fields
    When I call task_update with only task_id
    Then the result contains "No update fields provided"

  Scenario: Link commit with invalid SHA
    When I call task_link_commit with commit_sha="not-hex"
    Then the result contains an error about hex format
```

---

## Layer 2: Reusable Actions Catalog

| Action | MCP Tool | Parameters | Intent |
|--------|----------|-----------|--------|
| Create Task | `task_create` | name, task_id?, status, priority, task_type, phase, session_id?, workspace_id? | Insert task into TypeDB |
| Get Task | `task_get` | task_id | Fetch single task by ID |
| Update Task | `task_update` | task_id, status?, name?, phase?, priority?, task_type?, workspace_id? | Modify task fields |
| Delete Task | `task_delete` | task_id, confirm=True | Remove task from TypeDB |
| List Tasks | `tasks_list` | status?, phase?, limit, offset | Paginated task listing |
| Get Taxonomy | `taxonomy_get` | — | Enum values for validation |
| Link Session | `task_link_session` | task_id, session_id | completed-in relation |
| Link Rule | `task_link_rule` | task_id, rule_id | implements-rule relation |
| Link Evidence | `task_link_evidence` | task_id, evidence_path | evidence-supports relation |
| Get Evidence | `task_get_evidence` | task_id | Query linked evidence |
| Link Commit | `task_link_commit` | task_id, commit_sha, commit_message? | task-commit relation |
| Get Commits | `task_get_commits` | task_id | Query linked commits |
| Link Document | `task_link_document` | task_id, document_path | document-references-task |
| Get Documents | `task_get_documents` | task_id | Query linked documents |
| Update Details | `task_update_details` | task_id, business?, design?, architecture?, test_section? | Detail sections |
| Get Details | `task_get_details` | task_id | Fetch detail sections |
| Capture Intent | `task_capture_intent` | task_id, goal, planned_steps?, context? | Record task intent |
| Capture Outcome | `task_capture_outcome` | task_id, status, achieved, deferred?, discoveries?, files_modified? | Record outcome |
| Verify Task | `task_verify` | task_id, verification_method, evidence, test_passed? | Verification evidence |
| Sync Todos | `session_sync_todos` | session_id, todos_json | Sync TodoWrite to TypeDB |

---

## Layer 3: TypeDB Schema & API Contracts

### Task Entity Schema
```yaml
Entity: governance-task
  Attributes:
    task-id: string (key)
    task-name: string
    task-description: string
    task-status: string (OPEN, IN_PROGRESS, DONE, CLOSED, BLOCKED)
    task-phase: string (P10, P11, RD, etc.)
    task-priority: string (LOW, MEDIUM, HIGH, CRITICAL)  # Phase 1
    task-type: string (bug, feature, chore, research, gap, epic, test)  # Phase 1
  Relations:
    completed-in: task → session
    implements-rule: task → rule
    evidence-supports: evidence → task
    task-commit: task → commit
    document-references-task: document → task
    workspace-has-task: workspace → task  # Phase 4
```

### Workspace Entity Schema
```yaml
Entity: workspace  # Phase 3
  Attributes:
    workspace-id: string (key)
    workspace-name: string
    workspace-type: string
    workspace-status: string
    workspace-description: string
  Relations:
    project-has-workspace: project → workspace
    workspace-has-agent: workspace → agent
    workspace-has-task: workspace → task  # Phase 4
```

### MCP Result Contract
```yaml
Success:
  { "task_id": str, "message": str, ...fields }
Error:
  { "error": str, "hint"?: str }
List:
  { "tasks": [...], "count": int, "total": int, "offset": int, "limit": int, "has_more": bool, "source": "typedb" }
```

### Integration Test Markers
```yaml
pytest.mark.integration: All integration tests
pytest.mark.typedb: Requires live TypeDB
pytest.mark.mcp: Tests MCP tool interface
```

---

## Test Decomposition

| Suite | Test File | Tests | Covers |
|-------|-----------|-------|--------|
| MCP Tasks Integration | `tests/integration/test_mcp_tasks_integration.py` | 13 | CRUD, list, pagination, taxonomy |
| MCP Tasks E2E | `tests/integration/test_mcp_tasks_e2e.py` | ~25 | Full lifecycle, linking, workspace, errors |
| Unit: CRUD | `tests/unit/test_mcp_tasks_crud.py` | 20+ | Mocked CRUD tool logic |
| Unit: Autolink | `tests/unit/test_task_autolink.py` | 19 | Auto-session linking |
| Unit: Workspace | `tests/unit/test_workspace_typedb_crud.py` | 47 | Workspace TypeDB CRUD |
| Unit: Task-WS | `tests/unit/test_task_workspace_linking.py` | 34 | Task-workspace relations |
