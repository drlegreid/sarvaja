# E2E Tier 3: MCP Task System Verification Specifications

| Field | Value |
|-------|-------|
| **EPIC** | EPIC-GOV-TASKS-V2 |
| **Phase** | Phase 5: MCP E2E Integration Tests |
| **Rule** | TEST-E2E-01-v1 |
| **Format** | Gherkin BDD Scenarios |
| **Created** | 2026-03-20 |
| **Status** | SPEC (ready for execution) |

> Per TEST-E2E-01-v1: Gherkin specs authored first, then executed as integration tests.

---

## Feature: Full CRUD Lifecycle via MCP (E2E-MCP-CRUD)

### Scenario: Create a task via MCP
```gherkin
Given TypeDB is available on localhost:1729
When I call task_create with:
  | Field       | Value                     |
  | name        | E2E Test Task             |
  | task_id     | E2E-CRUD-001              |
  | status      | OPEN                      |
  | priority    | LOW                       |
  | task_type   | test                      |
  | phase       | P10                       |
Then the result contains "message" with "created successfully"
  And the result does not contain "error"
```

### Scenario: Read a task via MCP
```gherkin
Given task "E2E-CRUD-001" exists in TypeDB
When I call task_get with task_id="E2E-CRUD-001"
Then the result contains task_id="E2E-CRUD-001"
  And the result contains status="OPEN"
```

### Scenario: Update a task via MCP
```gherkin
Given task "E2E-CRUD-001" exists with status="OPEN"
When I call task_update with task_id="E2E-CRUD-001", status="IN_PROGRESS"
Then the result contains "message" with "updated successfully"
When I call task_get with task_id="E2E-CRUD-001"
Then the result contains status="IN_PROGRESS"
```

### Scenario: Update priority and type via MCP
```gherkin
Given task "E2E-CRUD-001" exists
When I call task_update with task_id="E2E-CRUD-001", priority="CRITICAL"
Then the result does not contain "error"
When I call task_get with task_id="E2E-CRUD-001"
Then the result contains priority="CRITICAL"
```

### Scenario: Delete a task via MCP (with confirmation)
```gherkin
Given task "E2E-CRUD-001" exists
When I call task_delete with task_id="E2E-CRUD-001", confirm=True
Then the result contains deleted=True
When I call task_get with task_id="E2E-CRUD-001"
Then the result contains "error"
```

### Scenario: Delete without confirmation is rejected
```gherkin
When I call task_delete with task_id="ANY", confirm=False
Then the result contains "error" with "confirmation"
```

---

## Feature: Task-Workspace Linking via MCP (E2E-MCP-WORKSPACE)

### Scenario: Create task with workspace_id
```gherkin
Given TypeDB is available
When I call task_create with:
  | Field        | Value          |
  | name         | Workspace Task |
  | task_id      | E2E-WS-001     |
  | workspace_id | WS-E2E-TEST   |
Then the result does not contain "error"
```

### Scenario: Update task workspace_id
```gherkin
Given task "E2E-WS-002" exists without a workspace
When I call task_update with task_id="E2E-WS-002", workspace_id="WS-E2E-ASSIGN"
Then the result contains "message" with "updated successfully"
```

---

## Feature: Task-Session Linking via MCP (E2E-MCP-SESSION)

### Scenario: Link task to session
```gherkin
Given task "E2E-LINK-001" exists
When I call task_link_session with task_id="E2E-LINK-001", session_id="SESSION-E2E-001"
Then the result contains relation="completed-in" or "error" (session may not exist)
```

### Scenario: Create task with session_id auto-links
```gherkin
Given TypeDB is available
When I call task_create with session_id="SESSION-E2E-AUTOLINK"
Then the result does not contain "error"
  And the task is linked to session "SESSION-E2E-AUTOLINK" (per DATA-LINK-01-v1)
```

---

## Feature: Task Document and Evidence Linking (E2E-MCP-DOCS)

### Scenario: Link document to task
```gherkin
Given task "E2E-DOC-001" exists
When I call task_link_document with task_id="E2E-DOC-001", document_path="docs/test.md"
Then the result contains relation="document-references-task" or "error"
```

### Scenario: Get documents for task
```gherkin
Given task "E2E-DOC-001" exists
When I call task_get_documents with task_id="E2E-DOC-001"
Then the result contains "documents" list
```

### Scenario: Link evidence to task
```gherkin
Given task "E2E-EVID-001" exists
When I call task_link_evidence with task_id="E2E-EVID-001", evidence_path="evidence/e2e.md"
Then the result contains relation="evidence-supports" or "error"
```

---

## Feature: Task Commit Linking (E2E-MCP-COMMITS)

### Scenario: Link valid commit to task
```gherkin
Given task "E2E-COMMIT-001" exists
When I call task_link_commit with task_id="E2E-COMMIT-001", commit_sha="abc1234"
Then the result contains relation="task-commit" or "error"
```

### Scenario: Reject invalid commit SHA
```gherkin
When I call task_link_commit with task_id="ANY", commit_sha="not-hex!!"
Then the result contains "error" with "hex string"
```

---

## Feature: Error Handling for Nonexistent Entities (E2E-MCP-ERRORS)

### Scenario: Get nonexistent task
```gherkin
When I call task_get with task_id="NONEXISTENT-999"
Then the result contains "error" with "not found"
```

### Scenario: Update nonexistent task
```gherkin
When I call task_update with task_id="NONEXISTENT-999", status="DONE"
Then the result contains "error"
```

### Scenario: Update with no fields
```gherkin
When I call task_update with task_id="ANY" and no other fields
Then the result contains "error" with "No update fields"
```

---

## Feature: Task Intent/Outcome and Verification (E2E-MCP-INTENT)

### Scenario: Capture task intent
```gherkin
Given task "E2E-INTENT-001" exists
When I call task_capture_intent with task_id="E2E-INTENT-001", goal="Testing"
Then the result does not contain "error"
```

### Scenario: Capture task outcome
```gherkin
Given task "E2E-OUTCOME-001" exists
When I call task_capture_outcome with task_id="E2E-OUTCOME-001", status="DONE", achieved="Pass"
Then the result does not contain "error"
```

### Scenario: Verify task with evidence
```gherkin
Given task "E2E-VERIFY-001" exists
When I call task_verify with:
  | Field               | Value               |
  | task_id             | E2E-VERIFY-001      |
  | verification_method | e2e-integration     |
  | evidence            | All tests pass      |
  | test_passed         | True                |
Then the result contains "task_id"
```
