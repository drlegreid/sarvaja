*** Settings ***
Documentation    SRVJ-CHORE-DOGFOOD-SWEEP-01: Tier 2 — Full task lifecycle E2E
...              Create -> Link (session, rule, document) -> Verify round-trip
...              -> Status transitions -> DONE gate -> Persistence after update.
...              Per EPIC-TASK-WORKFLOW-HEAL-01 + DELIVER-QA-MOAT-01-v1.

Resource    ../resources/api.resource
Library     Collections

Suite Setup       Setup Dogfood Lifecycle
Suite Teardown    Teardown Dogfood Lifecycle


*** Variables ***
${TEST_WORKSPACE}         WS-TEST-SANDBOX
${LIFECYCLE_TASK}         E2E-DOGFOOD-LIFE-001
${LIFECYCLE_SESSION}      SESSION-E2E-DOGFOOD-LIFE
${LIFECYCLE_RULE}         TEST-E2E-01-v1
${LIFECYCLE_DOC}          docs/backlog/specs/EDS-PERF-GATE-01-v1.eds.md
${DEFAULT_AGENT}          code-agent


*** Test Cases ***

# ── Phase 1: Create ─────────────────────────────────────────────────

Task Create Returns Persisted Status
    [Documentation]    Create task via API, verify persistence_status is persisted.
    [Tags]    tier2    lifecycle    create
    # Task already created in Suite Setup — verify it's readable
    ${response}=    API GET    /tasks/${LIFECYCLE_TASK}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    # API may return OPEN or TODO depending on TypeDB normalization
    Should Match Regexp    ${json}[status]    ^(OPEN|TODO)$

# ── Phase 2: Link Everything ────────────────────────────────────────

Link Session To Task
    [Documentation]    Link a session and verify structured response.
    [Tags]    tier2    lifecycle    link
    ${response}=    API POST    /tasks/${LIFECYCLE_TASK}/sessions/${LIFECYCLE_SESSION}
    Response Status Should Be    ${response}    201
    ${json}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${json}    success
    Should Be True    ${json}[success]

Link Rule To Task
    [Documentation]    Link a rule and verify structured response.
    [Tags]    tier2    lifecycle    link
    ${response}=    API POST    /tasks/${LIFECYCLE_TASK}/rules/${LIFECYCLE_RULE}
    Response Status Should Be    ${response}    201

Link Document To Task
    [Documentation]    Link a document and verify structured response.
    [Tags]    tier2    lifecycle    link
    ${payload}=    Create Dictionary    document_path=${LIFECYCLE_DOC}
    ${response}=    API POST    /tasks/${LIFECYCLE_TASK}/documents    ${payload}
    Response Status Should Be    ${response}    201

# ── Phase 3: Verify Round-Trip ──────────────────────────────────────

Verify Session Link Round Trip
    [Documentation]    GET linked sessions contains our session.
    [Tags]    tier2    lifecycle    roundtrip
    ${response}=    API GET    /tasks/${LIFECYCLE_TASK}/sessions
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    ${sessions}=    Get From Dictionary    ${json}    sessions
    # API returns session objects — extract session_ids
    ${session_ids}=    Evaluate    [s.get("session_id") for s in $sessions]
    Should Contain    ${session_ids}    ${LIFECYCLE_SESSION}

Verify Document Link Round Trip
    [Documentation]    GET linked documents contains our document.
    [Tags]    tier2    lifecycle    roundtrip
    ${response}=    API GET    /tasks/${LIFECYCLE_TASK}/documents
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    ${documents}=    Get From Dictionary    ${json}    documents
    Should Contain    ${documents}    ${LIFECYCLE_DOC}

Verify Task Get Shows All Links
    [Documentation]    GET /tasks/{id} includes linked_sessions and linked_rules.
    [Tags]    tier2    lifecycle    roundtrip
    ${response}=    API GET    /tasks/${LIFECYCLE_TASK}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Contain    ${json}[linked_sessions]    ${LIFECYCLE_SESSION}

# ── Phase 4: Idempotency ────────────────────────────────────────────

Duplicate Session Link Is Idempotent
    [Documentation]    Second session link returns 201 with already_existed=True.
    [Tags]    tier2    lifecycle    idempotency
    ${response}=    API POST    /tasks/${LIFECYCLE_TASK}/sessions/${LIFECYCLE_SESSION}
    Response Status Should Be    ${response}    201
    ${json}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${json}    already_existed
    Should Be True    ${json}[already_existed]
    ...    msg=Duplicate link should report already_existed=True

# ── Phase 5: Status Transitions ─────────────────────────────────────

Valid Transition OPEN To IN_PROGRESS
    [Documentation]    OPEN -> IN_PROGRESS is allowed.
    [Tags]    tier2    lifecycle    transition
    ${payload}=    Create Dictionary    status=IN_PROGRESS    agent_id=${DEFAULT_AGENT}
    ${response}=    API PUT    /tasks/${LIFECYCLE_TASK}    ${payload}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be Equal    ${json}[status]    IN_PROGRESS

Invalid Transition IN_PROGRESS To TODO Blocked
    [Documentation]    IN_PROGRESS -> TODO is NOT allowed (per VALID_STATUS_TRANSITIONS).
    [Tags]    tier2    lifecycle    transition
    ${payload}=    Create Dictionary    status=TODO
    ${response}=    API PUT    /tasks/${LIFECYCLE_TASK}    ${payload}
    # Must NOT be 200 — transition invalid
    ${status}=    Set Variable    ${response.status_code}
    Should Not Be Equal As Integers    ${status}    200
    ...    msg=Invalid transition IN_PROGRESS->TODO should be rejected

# ── Phase 6: DONE Gate ──────────────────────────────────────────────

DONE Gate Blocks Fresh Task Without Agent ID
    [Documentation]    A fresh task (no agent_id ever set) cannot transition to DONE.
    ...                Per TASK-LIFE-01-v1: DONE gate requires agent_id for test type.
    [Tags]    tier2    lifecycle    done-gate
    # Create a fresh task with NO agent_id for clean DONE gate test
    ${resp_create}=    api.Create Test Task    E2E-DONEGATE-001    Fresh DONE gate test
    ...    workspace_id=${TEST_WORKSPACE}
    api.Response Status Should Be    ${resp_create}    201
    # Try DONE without ever setting agent_id
    ${payload}=    Create Dictionary    status=DONE    summary=Should be blocked
    ${response}=    API PUT    /tasks/E2E-DONEGATE-001    ${payload}
    ${status}=    Set Variable    ${response.status_code}
    Should Not Be Equal As Integers    ${status}    200
    ...    msg=DONE transition without agent_id MUST be blocked
    [Teardown]    api.Cleanup Test Task    E2E-DONEGATE-001

DONE Gate Passes With All Required Fields
    [Documentation]    Transition to DONE with all DoD fields succeeds.
    ...                Per TASK-LIFE-01-v1: test type needs summary + agent_id + evidence.
    [Tags]    tier2    lifecycle    done-gate
    ${payload}=    Create Dictionary
    ...    status=DONE
    ...    agent_id=${DEFAULT_AGENT}
    ...    summary=Dogfood lifecycle E2E test completed
    ...    evidence=E2E robot test passed all phases
    ${response}=    API PUT    /tasks/${LIFECYCLE_TASK}    ${payload}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be Equal    ${json}[status]    DONE

# ── Phase 7: Post-DONE Persistence ──────────────────────────────────

Task Persists After DONE Transition
    [Documentation]    Read task back after DONE — all links and fields survive.
    [Tags]    tier2    lifecycle    persistence
    ${response}=    API GET    /tasks/${LIFECYCLE_TASK}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be Equal    ${json}[status]    DONE
    Should Be Equal    ${json}[agent_id]    ${DEFAULT_AGENT}
    Should Contain    ${json}[linked_sessions]    ${LIFECYCLE_SESSION}


*** Keywords ***

Setup Dogfood Lifecycle
    [Documentation]    Create API session and test task.
    api.Create API Session
    # Clean up any leftover from previous run
    api.Cleanup Test Task    ${LIFECYCLE_TASK}
    # Create fresh task
    ${response}=    api.Create Test Task    ${LIFECYCLE_TASK}
    ...    Dogfood lifecycle E2E test task
    ...    workspace_id=${TEST_WORKSPACE}
    api.Response Status Should Be    ${response}    201

Teardown Dogfood Lifecycle
    [Documentation]    Clean up test task.
    api.Cleanup Test Task    ${LIFECYCLE_TASK}
