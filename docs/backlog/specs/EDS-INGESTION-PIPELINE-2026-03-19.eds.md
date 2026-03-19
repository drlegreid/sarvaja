# EDS: Ingestion Pipeline Data Integrity — 2026-03-19

> Per TEST-EXPLSPEC-01-v1: Exploratory Dynamic Specification

## Discovery Context
- URL: http://localhost:8081, http://localhost:8082
- Browser: chromium (headless)
- Tool: MCP Playwright + httpx API client + CCJsonlFactory
- Views explored: Sessions list, Session detail, Transcript
- Date: 2026-03-19

## Exploratory Findings

### Sessions View
- 695 total sessions, 7 active
- Table columns: Session ID, Name, Source, Project, Start, End, Duration, Status, Agent, Description
- CC sessions show metadata in Description: "(N user, M assistant, K tools)"
- "Hide test" toggle filters test artifacts
- Pagination: "Page 1 of 35 (695 total)"

### Transcript API
- `GET /api/sessions/{id}/transcript?per_page=3` returns JSONL-sourced entries
- Entry types observed: user_prompt, assistant_text, tool_use, tool_result
- Fields: index, timestamp, entry_type, content, content_length, is_truncated, model, tool_name, tool_use_id
- Source field: "jsonl" for CC sessions

### Ingestion Flow
- `POST /api/ingestion/scan` triggers immediate CC project discovery
- Scanner reads `~/.claude/projects/` for JSONL files
- `scan_jsonl_metadata()` extracts: session_uuid, timestamps, user/assistant/tool counts, custom_title
- Session ID format: `SESSION-{date}-CC-{SLUG}`
- Duplicate detection: skips if session_id already exists

---

## Layer 1: Business Scenarios

### Feature: Ingestion Pipeline Data Integrity
```gherkin
Feature: JSONL Ingestion Pipeline
  As a platform operator
  I want CC session JSONL files to be automatically discovered and ingested
  So that session data is queryable via API and visible in the dashboard

  Scenario: Trigger ingestion scan creates session from JSONL
    Given a CC JSONL file exists with known metadata
    When I trigger an ingestion scan via POST /api/ingestion/scan
    Then a session entity should be created in the API
    And the session metadata should match the JSONL content

  Scenario: Ingested session has correct CC metadata
    Given a session was ingested from a JSONL file
    When I GET /api/sessions/{session_id}
    Then cc_session_uuid should match the JSONL sessionId
    And cc_tool_count should match the JSONL tool_use count
    And start_time should match the first JSONL timestamp
    And end_time should match the last JSONL timestamp

  Scenario: Transcript returns JSONL entries
    Given a session was ingested from a JSONL file
    When I GET /api/sessions/{session_id}/transcript
    Then the source should be "jsonl"
    And entries should include user_prompt, assistant_text, tool_use types
    And entry timestamps should be monotonically increasing
    And tool_use entries should have tool_name set

  Scenario: Dashboard renders ingested session
    Given a session was ingested from a JSONL file
    When I navigate to the Sessions view in the dashboard
    And I search for the session ID
    Then the session should appear in the table
    And the Source column should show "CC"
    And the Description should contain tool count

  Scenario: Duplicate JSONL does not create duplicate session
    Given a session was already ingested from a JSONL file
    When I trigger another ingestion scan
    Then the session count should not increase
    And the existing session should be unchanged

  Scenario: Session with custom title shows name
    Given a CC JSONL file contains a custom-title entry
    When the session is ingested
    Then the session cc_external_name should match the custom title
    And the dashboard Name column should show the custom title
```

## Layer 2: Reusable Actions Catalog

| Action | Parameters | Maps To |
|--------|-----------|---------|
| Create Test JSONL | turns, session_id | CCJsonlFactory.write_session_file() |
| Place JSONL In Discovery Path | jsonl_path, target_dir | shutil.copy to CC projects dir |
| Trigger Ingestion Scan | — | POST /api/ingestion/scan |
| Get Session By ID | session_id | GET /api/sessions/{id} |
| Get Session Transcript | session_id, per_page | GET /api/sessions/{id}/transcript |
| List Sessions With Search | search_term | GET /api/sessions?search={term} |
| Delete Test Session | session_id | DELETE /api/sessions/{id} |
| Navigate To Sessions View | — | Playwright click nav-sessions |
| Search Sessions In Dashboard | query | Playwright fill search input |
| Verify Table Contains Row | text | Playwright assert row visible |

## Layer 3: Page Objects & API Contracts

### API Contracts

```yaml
POST /api/ingestion/scan:
  Response:
    Status: 200
    Body:
      status: "completed"
      result:
        projects_created: int
        sessions_ingested: int
        errors: list
        duration_ms: float
        timestamp: str

GET /api/sessions/{session_id}:
  Response:
    Status: 200
    Body:
      session_id: str
      start_time: str (ISO 8601)
      end_time: str | null
      status: "ACTIVE" | "COMPLETED"
      cc_session_uuid: str | null
      cc_tool_count: int | null
      cc_thinking_chars: int | null
      cc_compaction_count: int | null
      cc_external_name: str | null
      duration: str | null
      description: str | null

GET /api/sessions/{session_id}/transcript:
  Params:
    page: int (default 1)
    per_page: int (default 50)
    include_thinking: bool (default true)
  Response:
    Status: 200
    Body:
      entries: list[TranscriptEntry]
      total: int
      page: int
      per_page: int
      has_more: bool
      session_id: str
      source: "jsonl" | "synthetic" | "evidence" | "none"
```

### UI Locators

```yaml
Page: Sessions List
  Elements:
    sessions_nav: "[data-testid='nav-sessions']"
    search_input: "input[placeholder*='Search']"
    data_table: "table, .v-data-table"
    table_rows: "tbody tr"
    hide_test_toggle: "text=Hide test"
    stats_total: "text=/\\d+ Total Sessions/"
    pagination: "text=/Page \\d+ of \\d+/"
```

## Screenshots
- [Sessions list](evidence/test-results/P2-10f-sessions-list-exploratory.png)
- [Session detail](evidence/test-results/P2-10f-session-detail-exploratory.png)

## Test Decomposition Plan

| Test File | Scenarios | Framework |
|-----------|-----------|-----------|
| `tests/e2e/test_ingestion_pipeline_e2e.py` | All 6 scenarios above | pytest + httpx + Playwright |
