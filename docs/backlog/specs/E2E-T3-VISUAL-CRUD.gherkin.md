# E2E Tier 3: Visual CRUD Verification Specifications

| Field | Value |
|-------|-------|
| **EPIC** | EPIC-TESTING-E2E |
| **Phase** | Phase 2: Visual Verification (Tier 3) |
| **Rule** | TEST-E2E-01-v1 |
| **Format** | Gherkin BDD Scenarios |
| **Created** | 2026-02-14 |
| **Status** | SPEC (ready for EPIC task generation) |

> Per TEST-E2E-01-v1: Gherkin specs are authored first, then converted to EPIC tasks for execution.

---

## Feature: Sessions CRUD (E2E-T3-SESSIONS)

### Scenario: Create a new session via UI
```gherkin
Given the dashboard is loaded at http://localhost:8081
  And I navigate to the "Sessions" tab
  And I note the "Total Sessions" count as {before_count}
When I click the "Add Session" button
Then a create form appears with fields:
  | Field        | Type     | Required | Default        |
  | Session ID   | text     | no       | auto-generated |
  | Description  | text     | yes      | empty          |
  | Agent ID     | text     | no       | empty          |
  | Status       | dropdown | yes      | ACTIVE         |
When I fill in:
  | Field       | Value                              |
  | Session ID  | SESSION-2026-02-14-E2E-CRUD-TEST   |
  | Description | Playwright CRUD verification       |
  | Agent ID    | e2e-test-agent                     |
  And I click "Save"
Then the sessions list reloads
  And "Total Sessions" count equals {before_count} + 1
  And a row with Session ID "SESSION-2026-02-14-E2E-CRUD-TEST" is visible
  And that row shows Status "ACTIVE" and Agent "e2e-test-agent"
```

### Scenario: View session detail with drill-down
```gherkin
Given the sessions list is visible
When I click the row for "SESSION-2026-02-14-E2E-CRUD-TEST"
Then the session detail view opens showing:
  | Section              | Contains                                       |
  | Header               | Session ID, Edit button, Delete button           |
  | Session Information  | Session ID, Date, File Path, Agent, Description  |
  | Evidence Files       | Filter input, file list or "No evidence" message |
  | Completed Tasks      | Count badge, task table or "No tasks" message    |
  | Tool Calls           | Count badge, tool list or "No tool data" message |
  And the back button (arrow-left) is visible
```

### Scenario: Edit an existing session
```gherkin
Given the session detail view for "SESSION-2026-02-14-E2E-CRUD-TEST" is open
When I click the "Edit" button
Then the session form opens in edit mode with pre-filled values:
  | Field       | Value                              |
  | Session ID  | SESSION-2026-02-14-E2E-CRUD-TEST   |
  | Description | Playwright CRUD verification       |
When I change the Description to "Updated via Playwright E2E"
  And I click "Save"
Then the detail view reloads
  And the Description field shows "Updated via Playwright E2E"
```

### Scenario: Delete a session
```gherkin
Given the session detail view for "SESSION-2026-02-14-E2E-CRUD-TEST" is open
  And I note the current "Total Sessions" count as {before_count}
When I click the "Delete" button
Then the session is removed
  And I am returned to the sessions list
  And "Total Sessions" count equals {before_count} - 1
  And no row with Session ID "SESSION-2026-02-14-E2E-CRUD-TEST" is visible
```

### Scenario: Filter sessions by status
```gherkin
Given the sessions list is visible with multiple sessions
When I open the "Status" dropdown filter
  And I select "COMPLETED"
Then only sessions with Status "COMPLETED" are shown in the table
  And the pagination reflects the filtered count
When I clear the Status filter
Then all sessions are shown again
```

### Scenario: Filter sessions by agent
```gherkin
Given the sessions list is visible
When I open the "Agent" dropdown filter
  And I select "agent-curator"
Then only sessions with Agent "agent-curator" are shown
When I clear the Agent filter
Then all sessions are shown again
```

### Scenario: Search sessions by text
```gherkin
Given the sessions list is visible
When I type "LIFECYCLE" into the "Search sessions..." field
Then only sessions containing "LIFECYCLE" in their ID or description are shown
When I clear the search field
Then all sessions are shown again
```

### Scenario: Toggle session view mode
```gherkin
Given the sessions list is in table view (default)
When I click the pivot/chart view toggle button
Then the view switches to pivot mode with a "Group by" dropdown
  And sessions are grouped by the selected field (agent_id or status)
When I click the table view toggle button
Then the list returns to table mode
```

---

## Feature: Rules Browse & Filter (E2E-T3-RULES)

### Scenario: Browse rules with pagination
```gherkin
Given the dashboard is loaded
When I navigate to the "Rules" tab
Then the rules table shows columns: Rule ID, Name, Status, Category, Priority, Applicability, Tasks, Sessions, Created
  And "1-25 of 50" pagination is visible
  And "Items per page" dropdown shows "25"
When I click the "Next page" button
Then the table shows rows 26-50
  And "Previous page" button is now enabled
```

### Scenario: Create a new rule via UI
```gherkin
Given the rules table is visible
When I click the "Add Rule" button
Then a create form appears with fields:
  | Field          | Type     | Required |
  | Rule ID        | text     | yes      |
  | Name           | text     | yes      |
  | Directive      | textarea | yes      |
  | Category       | dropdown | yes      |
  | Priority       | dropdown | yes      |
  | Applicability  | dropdown | yes      |
When I fill in:
  | Field         | Value                        |
  | Rule ID       | E2E-TEST-RULE-01-v1          |
  | Name          | Playwright Test Rule         |
  | Directive     | Test rule for E2E validation  |
  | Category      | testing                      |
  | Priority      | LOW                          |
  | Applicability | RECOMMENDED                  |
  And I click "Save"
Then the rules table reloads
  And a row with Rule ID "E2E-TEST-RULE-01-v1" is visible
```

### Scenario: Filter rules by status
```gherkin
Given the rules table is visible
When I open the "Status" dropdown
  And I select "ACTIVE"
Then only rules with Status "ACTIVE" are shown
  And no DEPRECATED or DRAFT rules are visible
When I clear the Status filter
Then all rules (ACTIVE, DEPRECATED, DRAFT) are shown
```

### Scenario: Filter rules by category
```gherkin
Given the rules table is visible
When I open the "Category" dropdown
  And I select "governance"
Then only rules with Category "governance" are shown
When I clear the Category filter
Then all rules are shown
```

### Scenario: Search rules by text
```gherkin
Given the rules table is visible
When I type "MCP" into the "Search rules..." field
Then only rules containing "MCP" in their ID or Name are shown
  And results include "ARCH-MCP-02-v1" and "GOV-MCP-FIRST-01-v1"
When I clear the search field
Then all rules are shown
```

### Scenario: View rule detail
```gherkin
Given the rules table is visible
When I click the row for "SESSION-EVID-01-v1"
Then the rule detail view opens showing:
  | Field          | Value                              |
  | Rule ID        | SESSION-EVID-01-v1                 |
  | Status         | ACTIVE                             |
  | Priority       | CRITICAL                           |
  And the Directive text is visible
  And linked Tasks count is displayed
  And linked Sessions count is displayed
  And a back button is available
```

---

## Feature: Tasks CRUD (E2E-T3-TASKS)

### Scenario: Create a new task via UI
```gherkin
Given the dashboard is loaded
  And I navigate to the "Tasks" tab
When I click the "Add Task" button
Then a create form appears with fields:
  | Field       | Type     | Required |
  | Task ID     | text     | yes      |
  | Description | text     | yes      |
  | Phase       | dropdown | yes      |
  | Agent ID    | text     | no       |
When I fill in:
  | Field       | Value                   |
  | Task ID     | E2E-TASK-CRUD-001       |
  | Description | Task created via E2E UI |
  | Phase       | SESSION                 |
  And I click "Create"
Then the task list reloads
  And a row with Task ID "E2E-TASK-CRUD-001" is visible
```

### Scenario: View task detail with linked items
```gherkin
Given the task "E2E-TASK-CRUD-001" is visible in the list
When I click the row for "E2E-TASK-CRUD-001"
Then the task detail view opens showing:
  | Section       | Contains                                          |
  | Header        | Task ID, Edit button, Back button                  |
  | Content       | Description, Phase, Status badges                  |
  | Linked Items  | Gap ID, Rules chips, Sessions chips, Commits chips  |
  | Agent Info    | Primary agent, Involved agents                      |
```

### Scenario: Edit a task
```gherkin
Given the task detail view for "E2E-TASK-CRUD-001" is open
When I click the "Edit" button
Then the edit form opens with pre-filled values
When I change Status to "IN_PROGRESS"
  And I set Agent ID to "e2e-agent"
  And I click "Save"
Then the detail view reloads
  And Status shows "IN_PROGRESS"
  And Agent shows "e2e-agent"
```

### Scenario: Filter tasks by status tab
```gherkin
Given the tasks list is visible
When I click the "Available" tab
Then only tasks with status suitable for claiming are shown
When I click the "Completed" tab
Then only tasks with status "DONE" are shown
When I click the "All" tab
Then all tasks are shown regardless of status
```

### Scenario: Filter tasks by phase
```gherkin
Given the tasks list is visible
When I open the "Phase" dropdown filter
  And I select "SESSION"
Then only tasks in phase "SESSION" are shown
When I clear the Phase filter
Then all tasks are shown
```

### Scenario: Search tasks
```gherkin
Given the tasks list is visible
When I type "CRUD" into the "Search tasks..." field
Then only tasks containing "CRUD" are shown
  And "E2E-TASK-CRUD-001" is visible in results
```

---

## Feature: Agents Interaction (E2E-T3-AGENTS)

### Scenario: Register a new agent
```gherkin
Given the dashboard is loaded
  And I navigate to the "Agents" tab
When I click the "Register Agent" button
Then a registration dialog appears with fields:
  | Field         | Type     | Required |
  | Agent Name    | text     | yes      |
  | Agent ID      | text     | yes      |
  | Agent Type    | dropdown | no       |
  | Model         | dropdown | no       |
  | Rules Bundle  | combobox | no       |
  | Instructions  | textarea | no       |
When I fill in:
  | Field      | Value            |
  | Agent Name | E2E Test Agent   |
  | Agent ID   | e2e-test-agent   |
  And I click "Register"
Then the agent list reloads
  And a card/row for "e2e-test-agent" is visible
```

### Scenario: View agent detail with metrics
```gherkin
Given the agents list is visible
When I click the agent item for "e2e-test-agent"
Then the agent detail view opens showing:
  | Section        | Contains                                |
  | Header         | Agent ID, Name, Back button              |
  | Metrics        | Trust score (0-1.0), Status badge        |
  | Trust History  | Trust score timeline or "No history"     |
  | Configuration  | Agent type, model, rules bundle          |
  | Relations      | Linked sessions, tasks                   |
  | Controls       | Pause/Resume toggle, Stop Task, End Session |
```

### Scenario: Toggle agent pause/resume
```gherkin
Given the agent detail view for "e2e-test-agent" is open
  And the agent status is "PAUSED"
When I click the "Resume Agent" button
Then the agent status changes to "ACTIVE"
  And the button label changes to "Pause Agent"
When I click the "Pause Agent" button
Then the agent status changes to "PAUSED"
```

### Scenario: Verify trust score display
```gherkin
Given the agents list is visible
Then each agent card/row shows:
  | Field       | Constraint              |
  | agent_id    | Non-empty string         |
  | name        | Non-empty string         |
  | status      | One of: ACTIVE, PAUSED   |
  | trust_score | Number between 0 and 1.0 |
```

---

## Feature: Decisions CRUD (E2E-T3-DECISIONS)

### Scenario: Record a new decision
```gherkin
Given the dashboard is loaded
  And I navigate to the "Decisions" tab
When I click the "Record Decision" button
Then a form appears with fields:
  | Field          | Type     | Required |
  | Decision ID    | text     | yes      |
  | Name/Title     | text     | yes      |
  | Context        | textarea | yes      |
  | Rationale      | textarea | yes      |
  | Status         | dropdown | yes      |
When I fill in:
  | Field       | Value                          |
  | Decision ID | E2E-DECISION-001               |
  | Name        | E2E Test Decision              |
  | Context     | Playwright CRUD test context    |
  | Rationale   | Automated visual verification   |
  | Status      | PENDING                        |
  And I click "Add Option"
  And I fill in Option 1: name="Option A", pros="Fast", cons="Limited"
  And I click "Save"
Then the decisions list reloads
  And a decision "E2E-DECISION-001" is visible with Name "E2E Test Decision"
```

### Scenario: Filter decisions by session
```gherkin
Given the decisions list is visible
When I open the "Session" dropdown filter
  And I select a session ID
Then only decisions linked to that session are shown
When I clear the Session filter
Then all decisions are shown
```

### Scenario: View decision detail
```gherkin
Given the decisions list is visible
When I click the decision "E2E-DECISION-001"
Then the decision detail view shows:
  | Field           | Value                          |
  | Decision ID     | E2E-DECISION-001               |
  | Name            | E2E Test Decision              |
  | Context         | Playwright CRUD test context    |
  | Rationale       | Automated visual verification   |
  | Selected Option | (empty or selected)             |
  And evidence references are displayed as chips
```

---

## Feature: Audit Trail (E2E-T3-AUDIT)

### Scenario: Browse audit trail with filters
```gherkin
Given the dashboard is loaded
  And I navigate to the "Audit" tab
Then summary cards are visible:
  | Card          | Shows         |
  | Total Entries | numeric count |
  | Entity Types  | numeric count |
  | Action Types  | numeric count |
  | Actors        | numeric count |
When I open the "Entity Type" dropdown
  And I select "session"
Then only audit entries for entity type "session" are shown
When I open the "Action Type" dropdown
  And I select "created"
Then only "created" actions for "session" entities are shown
When I clear all filters
Then the full audit trail is shown
```

### Scenario: Search audit by entity ID
```gherkin
Given the audit trail is visible
When I type "SESSION-2026" into the "Entity ID" field
Then audit entries matching that entity ID pattern are shown
When I clear the field
Then all entries are shown
```

---

## Feature: Cross-Tab Navigation (E2E-T3-NAVIGATION)

### Scenario: All 16 navigation items load without error
```gherkin
Given the dashboard is loaded at http://localhost:8081
Then the sidebar shows 16 navigation items:
  | Tab            | Expected Content                |
  | Chat           | Chat interface or placeholder    |
  | Rules          | Rules table with 50 rules        |
  | Agents         | Agent list with trust scores     |
  | Tasks          | Task list with status/phase      |
  | Sessions       | Session table with 81 sessions   |
  | Executive      | Executive report view            |
  | Decisions      | Decisions list                   |
  | Impact         | Impact analysis view             |
  | Trust          | Trust overview                   |
  | Workflow        | Workflow/backlog view            |
  | Audit          | Audit trail with filters         |
  | Monitor        | System monitor view              |
  | Infrastructure | Infrastructure status            |
  | Metrics        | Metrics dashboard                |
  | Tests          | Test/CVP results                 |
  | Projects       | Projects list                    |
When I click each navigation item in sequence
Then each view loads without showing an error state
  And each view displays its primary content area
  And no JavaScript console errors are produced
```

---

## Feature: Projects (E2E-T3-PROJECTS)

### Scenario: Create and view a project
```gherkin
Given I navigate to the "Projects" tab
When I click the "New Project" button
Then a project creation form or dialog appears
When I fill in the required fields
  And I click "Save" or "Create"
Then the projects list reloads
  And the new project is visible
When I click the project row
Then the project detail shows:
  | Section          | Contains                    |
  | Header           | Project ID, Name, Path       |
  | Metrics          | Plan count, Session count    |
  | Linked Sessions  | Session table with drill-down |
```

---

## Cleanup Scenarios

### Scenario: Clean up test data
```gherkin
Given all CRUD tests have completed
Then delete the following test artifacts via API:
  | Type     | ID                               |
  | Session  | SESSION-2026-02-14-E2E-CRUD-TEST |
  | Rule     | E2E-TEST-RULE-01-v1              |
  | Task     | E2E-TASK-CRUD-001                |
  | Decision | E2E-DECISION-001                 |
  | Agent    | e2e-test-agent                   |
  And verify each deletion returns HTTP 200 or 204
  And verify the items no longer appear in their respective lists
```

---

*Generated per TEST-E2E-01-v1 Gherkin-first workflow.*
*Each scenario maps to an EPIC task in EPIC-TESTING-E2E Phase 2.*
