*** Settings ***
Documentation    Task Data Integrity E2E Tests — EPIC-TASK-QUALITY-V3 Phase 11B
...              Per TEST-E2E-01-v1: Tier 3 API-level BDD verification.
...              Proves: agent_id persistence, created_at non-null, rule link idempotency.
...
...              Bugs under test:
...              - SRVJ-BUG-018: agent_id not persisted through update_task()
...              - SRVJ-BUG-019: created_at reads null on GET
...              - SRVJ-BUG-020: link_task_to_rule creates duplicates

Resource    ../resources/api.resource

Suite Setup       Setup Data Integrity Suite
Suite Teardown    Teardown Data Integrity Suite

Default Tags    e2e    api    data-integrity    p11b

*** Variables ***
${DI_TASK_018}     RF-DI-BUG-018
${DI_TASK_019}     RF-DI-BUG-019
${DI_TASK_020}     RF-DI-BUG-020
${DI_TASK_CRUD}    RF-DI-CRUD-001
${TEST_RULE}       TEST-E2E-01-v1
${ALT_RULE}        ARCH-INFRA-01-v1

*** Keywords ***
Setup Data Integrity Suite
    [Documentation]    Create API session + fresh test tasks.
    Create API Session
    Cleanup Test Task    ${DI_TASK_018}
    Cleanup Test Task    ${DI_TASK_019}
    Cleanup Test Task    ${DI_TASK_020}
    Cleanup Test Task    ${DI_TASK_CRUD}
    Sleep    300ms    reason=Wait for cleanup to settle
    Create Test Task    ${DI_TASK_018}    BUG-018 agent_id persistence    task_type=test    priority=HIGH
    Create Test Task    ${DI_TASK_019}    BUG-019 created_at non-null    task_type=test    priority=HIGH
    Create Test Task    ${DI_TASK_020}    BUG-020 idempotent rule link    task_type=test    priority=MEDIUM
    Create Test Task    ${DI_TASK_CRUD}    Full CRUD round-trip    task_type=test    priority=HIGH

Teardown Data Integrity Suite
    [Documentation]    Clean up test data.
    Cleanup Test Task    ${DI_TASK_018}
    Cleanup Test Task    ${DI_TASK_019}
    Cleanup Test Task    ${DI_TASK_020}
    Cleanup Test Task    ${DI_TASK_CRUD}

Task GET Should Have Field
    [Documentation]    GET task and assert field is non-null.
    [Arguments]    ${task_id}    ${field}
    ${response}=    API GET    /tasks/${task_id}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    ${value}=    Get From Dictionary    ${json}    ${field}
    Should Not Be Equal    ${value}    ${None}    msg=${field} is null on GET ${task_id}
    RETURN    ${value}

Task GET Should Have Field Value
    [Documentation]    GET task and assert field equals expected value.
    [Arguments]    ${task_id}    ${field}    ${expected}
    ${value}=    Task GET Should Have Field    ${task_id}    ${field}
    Should Be Equal As Strings    ${value}    ${expected}    msg=${field} expected '${expected}', got '${value}'

Link Task To Rule
    [Documentation]    POST to link a task to a rule.
    [Arguments]    ${task_id}    ${rule_id}
    ${response}=    API POST    /tasks/${task_id}/rules/${rule_id}
    RETURN    ${response}

Count Linked Rules
    [Documentation]    GET task and return count of linked_rules.
    [Arguments]    ${task_id}
    ${response}=    API GET    /tasks/${task_id}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    ${rules}=    Get From Dictionary    ${json}    linked_rules
    ${count}=    Get Length    ${rules}
    RETURN    ${count}

*** Test Cases ***
# ── SRVJ-BUG-018: agent_id persistence ──

Agent ID Auto-Assigned On IN_PROGRESS Transition
    [Documentation]    Given task exists with status OPEN,
    ...                When status is updated to IN_PROGRESS,
    ...                Then GET returns agent_id "code-agent".
    [Tags]    SRVJ-BUG-018    data-integrity    agent-id
    ${payload}=    Create Dictionary    status=IN_PROGRESS
    ${response}=    API PUT    /tasks/${DI_TASK_018}    ${payload}
    Response Status Should Be    ${response}    200
    Sleep    500ms    reason=Wait for TypeDB write
    Task GET Should Have Field Value    ${DI_TASK_018}    agent_id    ${DEFAULT_AGENT}

Agent ID Explicit Update Persists
    [Documentation]    Given task exists,
    ...                When agent_id is explicitly set to "custom-agent",
    ...                Then GET returns agent_id "custom-agent".
    [Tags]    SRVJ-BUG-018    data-integrity    agent-id
    ${payload}=    Create Dictionary    agent_id=research-agent    status=IN_PROGRESS
    ${response}=    API PUT    /tasks/${DI_TASK_018}    ${payload}
    Response Status Should Be    ${response}    200
    Sleep    500ms    reason=Wait for TypeDB write
    Task GET Should Have Field Value    ${DI_TASK_018}    agent_id    research-agent

Agent ID Replacement Overwrites Previous
    [Documentation]    Given task has agent_id "custom-agent",
    ...                When agent_id is updated to "replacement-agent",
    ...                Then GET returns agent_id "replacement-agent".
    [Tags]    SRVJ-BUG-018    data-integrity    agent-id
    ${payload}=    Create Dictionary    agent_id=task-orchestrator    status=IN_PROGRESS
    ${response}=    API PUT    /tasks/${DI_TASK_018}    ${payload}
    Response Status Should Be    ${response}    200
    Sleep    500ms    reason=Wait for TypeDB write
    Task GET Should Have Field Value    ${DI_TASK_018}    agent_id    task-orchestrator

# ── SRVJ-BUG-019: created_at non-null ──

Created At Non-Null On Single GET
    [Documentation]    Given task was just created,
    ...                Then GET /tasks/{id} returns non-null created_at.
    [Tags]    SRVJ-BUG-019    data-integrity    created-at
    ${value}=    Task GET Should Have Field    ${DI_TASK_019}    created_at
    Should Contain    ${value}    2026    msg=created_at should contain year

Created At Non-Null On Batch List
    [Documentation]    Given task exists,
    ...                Then GET /tasks returns created_at non-null for our task.
    [Tags]    SRVJ-BUG-019    data-integrity    created-at
    ${response}=    API GET    /tasks
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    ${items}=    Get From Dictionary    ${json}    items
    ${found}=    Set Variable    ${False}
    FOR    ${item}    IN    @{items}
        ${tid}=    Get From Dictionary    ${item}    task_id
        IF    $tid == $DI_TASK_019
            ${created}=    Get From Dictionary    ${item}    created_at
            Should Not Be Equal    ${created}    ${None}    msg=created_at null in batch list
            ${found}=    Set Variable    ${True}
        END
    END
    Should Be True    ${found}    msg=Task ${DI_TASK_019} not found in batch list

# ── SRVJ-BUG-020: link_task_to_rule idempotency ──

Duplicate Rule Link Produces Single Relation
    [Documentation]    Given task exists,
    ...                When same rule is linked twice,
    ...                Then GET returns exactly 1 linked_rules entry.
    [Tags]    SRVJ-BUG-020    data-integrity    rule-link
    Link Task To Rule    ${DI_TASK_020}    ${TEST_RULE}
    Link Task To Rule    ${DI_TASK_020}    ${TEST_RULE}
    Sleep    500ms    reason=Wait for TypeDB write
    ${count}=    Count Linked Rules    ${DI_TASK_020}
    Should Be Equal As Integers    ${count}    1    msg=Duplicate link created ${count} relations (expected 1)

Different Rules Create Distinct Links
    [Documentation]    Given task exists,
    ...                When two different rules are linked,
    ...                Then GET returns exactly 2 linked_rules entries.
    [Tags]    SRVJ-BUG-020    data-integrity    rule-link
    Link Task To Rule    ${DI_TASK_020}    ${ALT_RULE}
    Sleep    500ms    reason=Wait for TypeDB write
    ${count}=    Count Linked Rules    ${DI_TASK_020}
    Should Be Equal As Integers    ${count}    2    msg=Expected 2 distinct rules, got ${count}

# ── Full CRUD Round-Trip ──

# ── SRVJ-BUG-023: agent_id validation ──

Invalid Agent ID Rejected By API
    [Documentation]    Given task exists,
    ...                When agent_id is set to unregistered value,
    ...                Then API returns error (4xx/5xx).
    [Tags]    SRVJ-BUG-023    data-integrity    agent-validation
    ${payload}=    Create Dictionary    agent_id=banana    status=IN_PROGRESS
    ${response}=    API PUT    /tasks/${DI_TASK_CRUD}    ${payload}
    ${status}=    Set Variable    ${response.status_code}
    Should Be True    ${status} >= 400
    ...    msg=Invalid agent_id 'banana' must be rejected (got ${status})

Valid Agent IDs Accepted By API
    [Documentation]    Given task exists,
    ...                When agent_id is a registered agent,
    ...                Then API accepts the update.
    [Tags]    SRVJ-BUG-023    data-integrity    agent-validation
    FOR    ${agent}    IN    @{VALID_AGENTS}
        ${payload}=    Create Dictionary    agent_id=${agent}    status=IN_PROGRESS
        ${response}=    API PUT    /tasks/${DI_TASK_CRUD}    ${payload}
        Response Status Should Be    ${response}    200
    END
    Sleep    500ms    reason=Wait for TypeDB write
    Task GET Should Have Field Value    ${DI_TASK_CRUD}    agent_id    local-assistant

# ── Full CRUD Round-Trip ──

All Fields Non-Null After Full CRUD Cycle
    [Documentation]    Given task created with priority and summary,
    ...                When status transitions OPEN → IN_PROGRESS with valid agent,
    ...                Then all key fields are non-null on GET.
    [Tags]    data-integrity    crud    full-cycle
    ${payload}=    Create Dictionary    status=IN_PROGRESS    agent_id=${DEFAULT_AGENT}
    ${response}=    API PUT    /tasks/${DI_TASK_CRUD}    ${payload}
    Response Status Should Be    ${response}    200
    Sleep    500ms    reason=Wait for TypeDB write
    Task GET Should Have Field    ${DI_TASK_CRUD}    status
    Task GET Should Have Field    ${DI_TASK_CRUD}    agent_id
    Task GET Should Have Field    ${DI_TASK_CRUD}    created_at
    Task GET Should Have Field    ${DI_TASK_CRUD}    claimed_at
    Task GET Should Have Field    ${DI_TASK_CRUD}    summary
    Task GET Should Have Field    ${DI_TASK_CRUD}    priority
    Task GET Should Have Field    ${DI_TASK_CRUD}    task_type
