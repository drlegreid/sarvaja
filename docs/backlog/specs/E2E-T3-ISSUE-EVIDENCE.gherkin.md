# E2E Tier 3: EPIC-ISSUE-EVIDENCE Verification Specifications

| Field | Value |
|-------|-------|
| **EPIC** | EPIC-ISSUE-EVIDENCE |
| **Phases** | FEAT-009, P18, P19 |
| **Rule** | TEST-E2E-01-v1 |
| **Format** | Gherkin BDD Scenarios |
| **Created** | 2026-03-24 |
| **Status** | SPEC (ready for execution) |

> Per TEST-E2E-01-v1: Gherkin specs authored first, then executed as integration tests.

---

## Feature: Active Session Detection (FEAT-009)

### Scenario: MCP session_list returns CC sessions
```gherkin
Given CC JSONL files exist in ~/.claude/projects/
  And at least one JSONL file was modified less than 2 hours ago
When I call session_list via MCP
Then the result contains "count" greater than 0
  And the result contains "sources" array
  And at least one source has source="cc_jsonl"
```

### Scenario: MCP session_list returns TypeDB active sessions
```gherkin
Given TypeDB has sessions with status="ACTIVE"
When I call session_list via MCP
Then the result contains active sessions from TypeDB
  And at least one source has source="typedb"
```

### Scenario: Session list deduplicates across sources
```gherkin
Given a session exists in both memory and TypeDB
When I call session_list via MCP
Then the session appears only once in active_sessions
  And the source is "memory" (highest priority)
```

### Scenario: REST sessions API returns ACTIVE sessions
```gherkin
When I GET /api/sessions?status=ACTIVE&limit=5
Then the response status is 200
  And the response contains "items" with at least 1 session
  And each session has status="ACTIVE"
```

---

## Feature: Multi-Session Timeline (P18)

### Scenario: Timeline endpoint returns events for task with linked sessions
```gherkin
Given task "SRVJ-TEST-051" has linked_sessions
When I GET /api/tasks/SRVJ-TEST-051/timeline
Then the response status is 200
  And the response contains "entries" array
  And each entry has timestamp, entry_type, session_id, title, icon, color
  And entries are sorted chronologically by timestamp
```

### Scenario: Timeline pagination
```gherkin
When I GET /api/tasks/SRVJ-TEST-051/timeline?page=1&per_page=2
Then the response contains "total" count
  And the response contains "has_more" boolean
  And entries count is at most 2
```

### Scenario: Timeline entry type filter
```gherkin
When I GET /api/tasks/SRVJ-TEST-051/timeline?entry_types=thought
Then all entries have entry_type="thought"
  And no entries have entry_type="tool_call"
```

### Scenario: Timeline returns 404 for unknown task
```gherkin
When I GET /api/tasks/NONEXISTENT-TASK/timeline
Then the response status is 404
```

### Scenario: Timeline UI visible in task detail
```gherkin
Given I navigate to Tasks view in the dashboard
When I click on a task with linked sessions
Then I see a "Session Timeline" card below the Execution Log
  And the card has a Refresh button
  And the card has an expand/collapse toggle
```

### Scenario: Timeline expand shows events
```gherkin
Given I am viewing a task detail with linked sessions
When I expand the Session Timeline card
Then I see timeline entries with icons and timestamps
  And each entry shows a session chip
  And tool_call entries show a wrench icon
  And thought entries show a brain icon
```

---

## Feature: Resolution Comments (P19)

### Scenario: Create a comment via API
```gherkin
Given task "SRVJ-BUG-020" exists
When I POST /api/tasks/SRVJ-BUG-020/comments with:
  | Field  | Value                    |
  | body   | E2E test comment         |
  | author | code-agent               |
Then the response status is 201
  And the response contains comment_id starting with "CMT-"
  And the response contains created_at timestamp
```

### Scenario: List comments via API
```gherkin
Given task "SRVJ-BUG-020" has at least 1 comment
When I GET /api/tasks/SRVJ-BUG-020/comments
Then the response status is 200
  And the response contains "comments" array
  And the response contains "total" matching array length
  And comments are in chronological order
```

### Scenario: Delete a comment via API
```gherkin
Given comment "CMT-{id}" exists on task "SRVJ-BUG-020"
When I DELETE /api/tasks/SRVJ-BUG-020/comments/CMT-{id}
Then the response status is 200
  And the response contains deleted=true
When I GET /api/tasks/SRVJ-BUG-020/comments
Then the comment is no longer in the list
```

### Scenario: Delete non-existent comment returns 404
```gherkin
When I DELETE /api/tasks/SRVJ-BUG-020/comments/CMT-nonexist
Then the response status is 404
```

### Scenario: Comments section visible in task detail UI
```gherkin
Given I navigate to a task detail in the dashboard
Then I see a "Comments" card below the Resolution section
  And the card shows comment count badge
  And the card has an "Add a comment..." textarea
  And the "Post Comment" button is disabled when textarea is empty
```

### Scenario: Post comment via UI
```gherkin
Given I am viewing a task detail in the dashboard
When I type "E2E Playwright comment" in the comment textarea
  And I click "Post Comment"
Then the comment appears in the comment list
  And the comment shows author "code-agent"
  And the comment shows a timestamp
  And the comment count badge increments by 1
  And the textarea is cleared
```

### Scenario: Delete comment via UI
```gherkin
Given a comment exists in the task detail Comments section
When I click the delete button on the comment
Then the comment is removed from the list
  And the comment count badge decrements by 1
```
