# EDS: Dashboard Views — 2026-03-19

> Per TEST-EXPLSPEC-01-v1: Exploratory Dynamic Specification

## Discovery Context
- URL: http://localhost:8081
- Browser: chromium (headless)
- Tool: MCP Playwright + Robot Framework Browser Library
- Views explored: Chat, Rules, Agents, Tasks, Sessions, Infrastructure, Workspaces, Projects
- Date: 2026-03-19

---

## Layer 1: Business Scenarios

### Feature: Dashboard Navigation
```gherkin
Feature: Dashboard Navigation
  As a governance operator
  I want to navigate between all dashboard views
  So that I can access platform management functions

  Scenario: All 17 navigation tabs are visible
    Given the dashboard is loaded at http://localhost:8081
    Then I should see navigation tabs for Chat, Rules, Agents, Tasks, Sessions,
         Executive, Decisions, Impact, Trust, Workflow, Audit, Monitor,
         Infrastructure, Metrics, Tests, Projects, Workspaces

  Scenario: Navigate to each view
    Given the dashboard is loaded
    When I click the "{view}" navigation tab
    Then the "{view}" content area should load
    Examples:
      | view           | expected_content        |
      | rules          | Governance Rules        |
      | agents         | Registered Agents       |
      | tasks          | tasks-list testid       |
      | sessions       | Session Evidence        |
      | infra          | Infrastructure Health   |
      | workspaces     | workspaces-list testid  |
      | projects       | projects-list testid    |
      | chat           | chat-view testid        |
```

### Feature: Sessions Management
```gherkin
Feature: Sessions Management
  As a governance operator
  I want to view, filter, and inspect session evidence
  So that I can audit agent activity and session quality

  Scenario: Sessions list shows stats and data
    Given I navigate to the Sessions view
    Then I should see stats cards: Total Sessions, Active, Total Duration, Avg Tasks/Session
    And I should see a data table with columns: Session ID, Name, Source, Project, Start, End, Duration, Status, Agent, Description
    And the table should have pagination showing "Page 1 of N"

  Scenario: Session detail opens on row click
    Given I am on the Sessions list with data rows
    When I click the first session row
    Then the session detail view should open
    And I should see a Back button
    And I should see "Completed Tasks" section

  Scenario: Filter sessions by search
    Given I am on the Sessions list
    When I type "sarvaja" in the search input
    Then the table should filter to show matching sessions
```

### Feature: Rules Management
```gherkin
Feature: Rules Management
  As a governance operator
  I want to view and manage governance rules
  So that I can maintain platform compliance

  Scenario: Rules list shows table with data
    Given I navigate to the Rules view
    Then I should see a searchable data table
    And the table should have columns: Rule ID, Name, Status, Category, Priority, Applicability, Tasks, Sessions, Created
    And the table should show pagination "1-25 of N"

  Scenario: Rule detail opens on row click
    Given I am on the Rules list with data rows
    When I click a rule row
    Then I should see rule detail with Edit or Directive content

  Scenario: Add Rule button is accessible
    Given I am on the Rules view
    Then I should see an "Add Rule" button
```

### Feature: Agents & Trust
```gherkin
Feature: Agents & Trust
  As a governance operator
  I want to view agent status and trust scores
  So that I can manage agent capabilities

  Scenario: Agents list shows all registered agents
    Given I navigate to the Agents view
    Then I should see stats: Total Agents, Avg Trust, Pending Proposals, Escalated
    And I should see a list of 9 agents with name, tasks, trust, and status

  Scenario: Trust dashboard shows leaderboard
    Given I navigate to the Trust view
    Then I should see "Agent Trust Dashboard" heading
    And I should see stats: Total Agents, Avg Trust Score
    And I should see a Trust Leaderboard section
```

### Feature: Infrastructure Health
```gherkin
Feature: Infrastructure Health
  As a platform administrator
  I want to monitor service health and MCP status
  So that I can respond to outages

  Scenario: Infrastructure dashboard shows all services
    Given I navigate to the Infrastructure view
    Then I should see service cards for Podman, TypeDB, ChromaDB, LiteLLM, Ollama
    And each card should show status (OK/ERROR), port, and type (Required/Optional)
    And I should see Memory Usage percentage and Health Hash

  Scenario: MCP server status table
    Given I am on the Infrastructure view
    Then I should see MCP Server Status table
    And servers should show: claude-mem, gov-core, gov-agents, gov-sessions, gov-tasks, rest-api, playwright
    And each should show Status, Ready, Tools count, Dependencies

  Scenario: Recovery actions are accessible
    Given I am on the Infrastructure view
    Then I should see buttons: Start All Services, Restart Stack, Cleanup Zombies
```

### Feature: Workspaces Management
```gherkin
Feature: Workspaces Management
  As a governance operator
  I want to manage workspaces for organizing agents and rules
  So that I can scope governance to specific contexts

  Scenario: Workspaces view shows empty state
    Given I navigate to the Workspaces view
    Then I should see stats cards: Total=0, Active=0, Types=0
    And I should see "0 workspaces" text
    And I should see Create Workspace and Refresh buttons
    And I should see search and filter controls (Type, Status)
```

### Feature: Projects
```gherkin
Feature: Projects
  As a governance operator
  I want to view CC session projects
  So that I can organize sessions by project context

  Scenario: Projects view shows table structure
    Given I navigate to the Projects view
    Then I should see stats cards for Projects, Plans, Sessions counts
    And I should see a table with columns: Project ID, Name, Path, Plans, Sessions
    And I should see a "New Project" button
```

---

## Layer 2: Reusable Actions Catalog

| Action | Parameters | Intent | Robot Keyword |
|--------|-----------|--------|---------------|
| Navigate To Tab | tab_name: str | Switch to a dashboard view | `Navigate To Tab` |
| Navigate And Verify Tab | tab_name, expected_text | Navigate + verify content | `Navigate And Verify Tab` |
| Navigation Tab Should Be Visible | tab_name | Assert nav item exists | `Navigation Tab Should Be Visible` |
| Dashboard Should Be Loaded | app_title | Verify dashboard rendered | `Dashboard Should Be Loaded` |
| Open Dashboard | url | Navigate browser to URL | `Open Dashboard` |
| Inject Overlay Fix | - | Disable Vuetify overlay clicks | `Inject Overlay Fix` |
| Click Table Row | index, table_selector | Click a data table row | `Click Table Row` |
| Verify Data Table Has Rows | table_selector, max_attempts | Assert table has data | `Verify Data Table Has Rows` |
| Wait For Element With Backoff | selector, max_attempts, state | Fibonacci wait for element | `Wait For Element With Backoff` |
| Element Should Be Visible With Backoff | selector, max_attempts | Assert visible with retry | `Element Should Be Visible With Backoff` |
| Click Element Safely | selector, timeout | Wait + click | `Click Element Safely` |
| Fill Input Field | selector, value, clear | Type into input | `Fill Input Field` |
| Navigate Back From Detail | back_selector | Click back button to list | `Navigate Back From Detail` |
| Take Evidence Screenshot | name | Capture test evidence | `Take Evidence Screenshot` |

---

## Layer 3: Page Objects & API Contracts

### Navigation Page Object
```yaml
Page: Navigation Sidebar
  Locators:
    nav_chat: "[data-testid='nav-chat']"
    nav_rules: "[data-testid='nav-rules']"
    nav_agents: "[data-testid='nav-agents']"
    nav_tasks: "[data-testid='nav-tasks']"
    nav_sessions: "[data-testid='nav-sessions']"
    nav_executive: "[data-testid='nav-executive']"
    nav_decisions: "[data-testid='nav-decisions']"
    nav_impact: "[data-testid='nav-impact']"
    nav_trust: "[data-testid='nav-trust']"
    nav_workflow: "[data-testid='nav-workflow']"
    nav_audit: "[data-testid='nav-audit']"
    nav_monitor: "[data-testid='nav-monitor']"
    nav_infra: "[data-testid='nav-infra']"
    nav_metrics: "[data-testid='nav-metrics']"
    nav_tests: "[data-testid='nav-tests']"
    nav_projects: "[data-testid='nav-projects']"
    nav_workspaces: "[data-testid='nav-workspaces']"
```

### Toolbar Page Object
```yaml
Page: Top Toolbar
  Locators:
    rules_chip: "[data-testid='toolbar-rules-chip']"
    decisions_chip: "[data-testid='toolbar-decisions-chip']"
    health_chip: "[data-testid='toolbar-health-chip']"
    refresh_btn: "button:has-text('Refresh data from API')"
```

### Sessions Page Object
```yaml
Page: Sessions List
  Locators:
    list_container: "[data-testid='sessions-list']"
    data_table: "[data-testid='sessions-table']"
    search_input: "[data-testid='sessions-search']"
    filter_status: "[data-testid='sessions-filter-status']"
    filter_agent: "[data-testid='sessions-filter-agent']"
    add_btn: "[data-testid='sessions-add-btn']"
    first_row: "[data-testid='sessions-table'] tbody tr:has(td) >> nth=0"

Page: Session Detail
  Locators:
    container: "[data-testid='session-detail']"
    back_btn: "[data-testid='session-detail-back-btn']"
    session_id: "[data-testid='session-detail-id']"
    edit_btn: "[data-testid='session-detail-edit-btn']"
    delete_btn: "[data-testid='session-detail-delete-btn']"
    completed_tasks: "[data-testid='session-completed-tasks']"
    transcript_card: "[data-testid='session-transcript-card']"
```

### Rules Page Object
```yaml
Page: Rules List
  Locators:
    list_container: "[data-testid='rules-list']"
    data_table: "[data-testid='rules-table']"
    search_input: "[data-testid='rules-search']"
    filter_status: "[data-testid='rules-filter-status']"
    filter_category: "[data-testid='rules-filter-category']"
    add_btn: "[data-testid='rules-add-btn']"
    first_row: "[data-testid='rules-table'] tbody tr:has(td) >> nth=0"

Page: Rule Detail
  Locators:
    container: "[data-testid='rule-detail']"
    back_btn: "[data-testid='rule-detail-back-btn']"
    rule_id: "[data-testid='rule-detail-id']"
    edit_btn: "[data-testid='rule-detail-edit-btn']"
    delete_btn: "[data-testid='rule-detail-delete-btn']"
    directive_text: "[data-testid='rule-directive-text']"
```

### Tasks Page Object
```yaml
Page: Tasks List
  Locators:
    list_container: "[data-testid='tasks-list']"
    data_table: "[data-testid='tasks-table']"
    search_input: "[data-testid='tasks-search']"
    filter_status: "[data-testid='tasks-filter-status']"
    filter_phase: "[data-testid='tasks-filter-phase']"
    add_btn: "[data-testid='tasks-add-btn']"
    filter_tabs: "[data-testid='tasks-filter-tabs']"
    agent_id_input: "[data-testid='tasks-agent-id']"

Page: Task Detail
  Locators:
    container: "[data-testid='task-detail']"
    back_btn: "[data-testid='task-detail-back-btn']"
    task_id: "[data-testid='task-detail-id']"
    status: "[data-testid='task-detail-status']"
    edit_btn: "[data-testid='task-detail-edit-btn']"
    delete_btn: "[data-testid='task-detail-delete-btn']"
```

### Agents Page Object
```yaml
Page: Agents List
  Locators:
    list_container: "[data-testid='agents-list']"
    register_btn: "[data-testid='agents-register-btn']"
    refresh_btn: "[data-testid='agents-refresh-btn']"
    agent_item: "[data-testid='agent-item']"

Page: Agent Detail
  Locators:
    container: "[data-testid='agent-detail']"
    back_btn: "[data-testid='agent-detail-back-btn']"
    name: "[data-testid='agent-detail-name']"
    status: "[data-testid='agent-detail-status']"
    capabilities: "[data-testid='agent-capabilities-card']"
```

### Infrastructure Page Object
```yaml
Page: Infrastructure Health
  Locators:
    dashboard: "[data-testid='infra-dashboard']"
    refresh_btn: "[data-testid='infra-refresh-btn']"
    card_podman: "[data-testid='infra-card-podman']"
    card_typedb: "[data-testid='infra-card-typedb']"
    card_chromadb: "[data-testid='infra-card-chromadb']"
    card_litellm: "[data-testid='infra-card-litellm']"
    card_ollama: "[data-testid='infra-card-ollama']"
    stat_memory: "[data-testid='infra-stat-memory']"
    stat_hash: "[data-testid='infra-stat-hash']"
    stat_procs: "[data-testid='infra-stat-procs']"
    mcp_status: "[data-testid='infra-mcp-status']"
    start_all: "[data-testid='infra-start-all']"
    restart: "[data-testid='infra-restart']"
    cleanup: "[data-testid='infra-cleanup']"
    dsp_alert: "[data-testid='infra-dsp-alert']"
```

### Workspaces Page Object
```yaml
Page: Workspaces List
  Locators:
    list_container: "[data-testid='workspaces-list']"
    create_btn: "[data-testid='workspace-create-btn']"
    refresh_btn: "[data-testid='workspace-refresh-btn']"
    workspace_item: "[data-testid='workspace-item']"

Page: Workspace Detail
  Locators:
    container: "[data-testid='workspace-detail']"
    back_btn: "[data-testid='workspace-detail-back-btn']"
    name: "[data-testid='workspace-detail-name']"
    edit_btn: "[data-testid='workspace-edit-btn']"
    delete_btn: "[data-testid='workspace-delete-btn']"
    delete_dialog: "[data-testid='workspace-delete-dialog']"

Page: Workspace Form
  Locators:
    form: "[data-testid='workspace-form']"
    name_input: "[data-testid='workspace-form-name']"
    description_input: "[data-testid='workspace-form-description']"
    type_select: "[data-testid='workspace-form-type']"
    submit_btn: "[data-testid='workspace-form-submit-btn']"
    cancel_btn: "[data-testid='workspace-form-cancel-btn']"
```

### Projects Page Object
```yaml
Page: Projects List
  Locators:
    list_container: "[data-testid='projects-list']"
    data_table: "[data-testid='projects-table']"
    add_btn: "[data-testid='projects-add-btn']"
```

### API Contracts
```yaml
GET /api/health:
  Response: { status: 200 }

GET /api/rules:
  Response:
    Status: 200
    Body: [ { rule_id: str, name: str, status: str, category: str, priority: str } ]

GET /api/tasks:
  Response:
    Status: 200
    Body: [ { task_id: str, description: str, status: str, phase: str } ]

GET /api/agents:
  Response:
    Status: 200
    Body: [ { agent_id: str, name: str, status: str, trust_score: float, task_count: int } ]

GET /api/sessions:
  Response:
    Status: 200
    Body: [ { session_id: str, status: str, start_time: str, end_time: str, duration: str } ]

GET /api/sessions/{id}:
  Response:
    Status: 200
    Body: { session_id: str, tools: list, thoughts: list, transcript: object }

GET /api/workspaces:
  Response:
    Status: 200
    Body: [ { workspace_id: str, name: str, type: str, status: str } ]

GET /api/projects:
  Response:
    Status: 200
    Body: [ { project_id: str, name: str, path: str } ]
```

---

## Screenshots

| View | Evidence File |
|------|--------------|
| Sessions | `evidence/test-results/P1-5-sessions-view.png` |
| Rules | `evidence/test-results/P1-5-rules-view.png` |
| Agents | `evidence/test-results/P1-5-agents-view.png` |
| Tasks | `evidence/test-results/P1-5-tasks-view.png` |
| Infrastructure | `evidence/test-results/P1-5-infra-view.png` |
| Workspaces | `evidence/test-results/P1-5-workspaces-view.png` |
| Projects | `evidence/test-results/P1-5-projects-view.png` |
| Chat | `evidence/test-results/P1-5-chat-view.png` |

---

## Test Decomposition Plan

From this EDS, the following static test suites can be generated:

| Suite | Source Scenarios | Priority | Status |
|-------|-----------------|----------|--------|
| smoke.robot | API Health, Dashboard Loads | CRITICAL | DONE (5 tests) |
| dashboard_navigation.robot | All 17 tabs, Navigate each view | CRITICAL | DONE (13 tests) |
| rules_view.robot | Rules list, table, search, detail | HIGH | DONE (5 tests) |
| sessions_view.robot | Sessions list, columns, detail | HIGH | DONE (3 tests) |
| tasks_view.robot | Tasks list, status, detail | HIGH | DONE (4 tests) |
| trust_agents_view.robot | Trust stats, leaderboard, agents | HIGH | DONE (5 tests) |
| infra_view.robot | Services, stats, recovery actions | HIGH | DONE (5 tests) |
| workspaces_view.robot | List, create, stats, filters | HIGH | DONE (5 tests) |
| projects_view.robot | List, table, stats | HIGH | DONE (4 tests) |
| sessions_crud.robot | Create, edit, delete sessions | MEDIUM | TODO |
| rules_crud.robot | Create, edit, delete rules | MEDIUM | TODO |
| tasks_crud.robot | Create, claim, complete, delete | MEDIUM | TODO |
| workspaces_crud.robot | Create, edit, delete workspaces | MEDIUM | TODO |
