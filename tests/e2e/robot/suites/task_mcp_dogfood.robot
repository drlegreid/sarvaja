*** Settings ***
Documentation    SRVJ-CHORE-DOGFOOD-SWEEP-01: Tier 2 — Real MCP tool E2E tests.
...              Calls the EXACT same Python functions that Claude Code invokes
...              via the MCP protocol. Tests round-trip through TypeDB.
...              Per DELIVER-QA-MOAT-01-v1 + GOV-MCP-FIRST-01-v1.

Library     ../libraries/mcp_tasks.py
Library     Collections

Suite Setup       Setup MCP Dogfood
Suite Teardown    Teardown MCP Dogfood


*** Variables ***
${MCP_TASK}              E2E-MCP-DOGFOOD-001
${MCP_SESSION}           SESSION-E2E-MCP-TEST
${MCP_RULE}              TEST-E2E-01-v1
${MCP_DOC}               docs/backlog/specs/EDS-PERF-GATE-01-v1.eds.md
${MCP_EVIDENCE}          evidence/test-results/mcp-dogfood.json
${MCP_COMMIT}            ec23661
${NONEXISTENT}           E2E-MCP-NONEXIST-999


*** Test Cases ***

# ── CRUD ─────────────────────────────────────────────────────────────

MCP Task Create Happy Path
    [Documentation]    task_create via MCP creates and persists to TypeDB.
    [Tags]    mcp    crud    create
    # Task already created in Setup — verify via MCP get
    ${result}=    MCP Task Get    ${MCP_TASK}
    MCP Result Should Succeed    ${result}
    Should Be Equal    ${result}[id]    ${MCP_TASK}

MCP Task Create Duplicate Blocked
    [Documentation]    Creating task with existing ID returns validation error.
    [Tags]    mcp    crud    create    error
    ${result}=    MCP Task Create    Duplicate test    task_id=${MCP_TASK}
    Should Contain    ${result}[error]    already exists

MCP Task Get Nonexistent Returns Error
    [Documentation]    Getting nonexistent task returns clear error.
    [Tags]    mcp    crud    get    error
    ${result}=    MCP Task Get    ${NONEXISTENT}
    Should Contain    ${result}[error]    not found

MCP Task Update Status Transition
    [Documentation]    Valid status transition OPEN -> IN_PROGRESS via MCP.
    [Tags]    mcp    crud    update
    ${result}=    MCP Task Update    ${MCP_TASK}    status=IN_PROGRESS    agent_id=code-agent
    MCP Result Should Succeed    ${result}
    Should Be Equal    ${result}[status]    IN_PROGRESS

MCP Task Update Invalid Transition Blocked
    [Documentation]    Invalid status transition IN_PROGRESS -> TODO blocked.
    [Tags]    mcp    crud    update    error
    ${result}=    MCP Task Update    ${MCP_TASK}    status=TODO
    Should Contain    ${result}[error]    Invalid status transition

MCP Task Delete Nonexistent Returns Error
    [Documentation]    Deleting nonexistent task returns error, not success.
    ...                Per SRVJ-BUG-DELETE-GHOST-01: existence check before delete.
    [Tags]    mcp    crud    delete    error
    ${result}=    MCP Task Delete    ${NONEXISTENT}
    Should Contain    ${result}[error]    not found

# ── Linking ──────────────────────────────────────────────────────────

MCP Link Session Happy Path
    [Documentation]    Link session via MCP with structured LinkResult response.
    [Tags]    mcp    link    session
    ${result}=    MCP Task Link Session    ${MCP_TASK}    ${MCP_SESSION}
    MCP Result Should Succeed    ${result}
    Should Be Equal    ${result}[relation]    completed-in
    Dictionary Should Contain Key    ${result}    already_existed

MCP Link Session Idempotent
    [Documentation]    Duplicate link returns already_existed=True.
    [Tags]    mcp    link    session    idempotency
    ${result}=    MCP Task Link Session    ${MCP_TASK}    ${MCP_SESSION}
    MCP Result Should Succeed    ${result}
    Should Be True    ${result}[already_existed]
    ...    msg=Second link should report already_existed=True

MCP Link Session Nonexistent Task Blocked
    [Documentation]    Linking to nonexistent task returns ENTITY_NOT_FOUND.
    ...                Per SRVJ-BUG-LINK-ORPHAN-01: no orphan relations.
    [Tags]    mcp    link    session    error
    ${result}=    MCP Task Link Session    ${NONEXISTENT}    ${MCP_SESSION}
    MCP Result Should Fail    ${result}    ENTITY_NOT_FOUND

MCP Link Rule Happy Path
    [Documentation]    Link rule via MCP.
    [Tags]    mcp    link    rule
    ${result}=    MCP Task Link Rule    ${MCP_TASK}    ${MCP_RULE}
    MCP Result Should Succeed    ${result}
    Should Be Equal    ${result}[relation]    implements-rule

MCP Link Rule Nonexistent Task Blocked
    [Documentation]    Rule link to nonexistent task blocked.
    [Tags]    mcp    link    rule    error
    ${result}=    MCP Task Link Rule    ${NONEXISTENT}    ${MCP_RULE}
    MCP Result Should Fail    ${result}    ENTITY_NOT_FOUND

MCP Link Document Happy Path
    [Documentation]    Link document via MCP.
    [Tags]    mcp    link    document
    ${result}=    MCP Task Link Document    ${MCP_TASK}    ${MCP_DOC}
    MCP Result Should Succeed    ${result}
    Should Be Equal    ${result}[relation]    document-references-task

MCP Link Evidence Happy Path
    [Documentation]    Link evidence via MCP.
    [Tags]    mcp    link    evidence
    ${result}=    MCP Task Link Evidence    ${MCP_TASK}    ${MCP_EVIDENCE}
    MCP Result Should Succeed    ${result}
    Should Be Equal    ${result}[relation]    evidence-supports

MCP Link Commit Happy Path
    [Documentation]    Link commit via MCP with SHA validation.
    [Tags]    mcp    link    commit
    ${result}=    MCP Task Link Commit    ${MCP_TASK}    ${MCP_COMMIT}
    MCP Result Should Succeed    ${result}
    Should Be Equal    ${result}[relation]    task-commit

MCP Link Commit Invalid SHA Rejected
    [Documentation]    Invalid commit SHA rejected at MCP boundary.
    [Tags]    mcp    link    commit    error
    ${result}=    MCP Task Link Commit    ${MCP_TASK}    not-a-hex-string
    Should Contain    ${result}[error]    hex string

# ── Round-trip Verification ──────────────────────────────────────────

MCP Task Get Shows All Links After Linking
    [Documentation]    MCP task_get returns all linked entities from TypeDB.
    [Tags]    mcp    roundtrip
    ${result}=    MCP Task Get    ${MCP_TASK}
    MCP Result Should Succeed    ${result}
    Should Be Equal    ${result}[agent_id]    code-agent
    Should Contain    ${result}[linked_sessions]    ${MCP_SESSION}
    Should Contain    ${result}[linked_rules]    ${MCP_RULE}
    Should Contain    ${result}[linked_documents]    ${MCP_DOC}
    Should Contain    ${result}[linked_commits]    ${MCP_COMMIT}

# ── Sync ─────────────────────────────────────────────────────────────

MCP Sync Pending Reports Honest Counts
    [Documentation]    sync_pending returns actual sync/failed/persisted counts.
    [Tags]    mcp    sync
    ${result}=    MCP Task Sync Pending
    MCP Result Should Succeed    ${result}
    Should Be True    ${result}[failed] == 0    msg=Sync should have 0 failures

# ── Cleanup Round-trip ───────────────────────────────────────────────

MCP Task Delete And Verify Gone
    [Documentation]    Delete task via MCP, then verify it's gone from TypeDB.
    [Tags]    mcp    crud    delete    roundtrip
    # Create a temporary task just for deletion test
    ${create}=    MCP Task Create    Delete round-trip test
    ...    task_id=E2E-MCP-DELETE-001    task_type=test
    MCP Result Should Succeed    ${create}
    # Delete it
    ${delete}=    MCP Task Delete    E2E-MCP-DELETE-001
    Should Be True    ${delete}[deleted]
    # Verify gone
    ${get}=    MCP Task Get    E2E-MCP-DELETE-001
    Should Contain    ${get}[error]    not found


*** Keywords ***

Setup MCP Dogfood
    [Documentation]    Create test task via MCP for dogfood tests.
    # Clean up any leftover
    MCP Task Delete    ${MCP_TASK}
    # Create fresh
    ${result}=    MCP Task Create    MCP Dogfood E2E Test Task
    ...    task_id=${MCP_TASK}    task_type=test    priority=LOW
    ...    workspace_id=WS-TEST-SANDBOX
    ...    description=Real MCP tool E2E test — same path as Claude Code
    MCP Result Should Succeed    ${result}

Teardown MCP Dogfood
    [Documentation]    Clean up test task.
    MCP Task Delete    ${MCP_TASK}
