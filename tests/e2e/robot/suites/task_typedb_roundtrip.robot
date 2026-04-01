*** Settings ***
Documentation    Task TypeDB Round-Trip Persistence E2E Tests — SRVJ-BUG-TYPEDB-WRITE-01
...              Per TEST-E2E-01-v1: Tier 2 API + DB-level verification.
...              Proves: Tasks created via REST ACTUALLY exist in TypeDB (not just cache).
...              Proves: Taxonomy attributes (layer, concern, method) survive at DB level.
...              Assertions query TypeDB DIRECTLY — bypassing service layer entirely.

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Library     ../libraries/typedb_verify.py

Suite Setup       Setup Roundtrip Suite
Suite Teardown    Teardown Roundtrip Suite

Default Tags    e2e    api    typedb    roundtrip    tasks

*** Variables ***
${RT_TASK_ID}          SRVJ-TEST-RT-E2E-001
${RT_TASK_LAYER}       SRVJ-TEST-RT-LAYER-001
${TEST_WORKSPACE}      WS-TEST-SANDBOX

*** Keywords ***
Setup Roundtrip Suite
    [Documentation]    Create API session. Per TEST-DATA-01-v1: use sandbox workspace.
    Create API Session

Teardown Roundtrip Suite
    [Documentation]    Clean up test tasks from BOTH API and TypeDB.
    api.Cleanup Test Task    ${RT_TASK_ID}
    api.Cleanup Test Task    ${RT_TASK_LAYER}
    Delete Task From TypeDB    ${RT_TASK_ID}
    Delete Task From TypeDB    ${RT_TASK_LAYER}

*** Test Cases ***
Task Created Via REST Exists In TypeDB
    [Documentation]    POST /api/tasks → query TypeDB directly → task entity exists.
    ...                This is the critical assertion: bypasses the service cache entirely.
    ...                Root cause of BUG-MCP-TASK-WRITE-01: service returned 201 but TypeDB had nothing.
    [Tags]    e2e    roundtrip    create    critical
    # Create via REST API
    ${response}=    api.Create Test Task    ${RT_TASK_ID}
    ...    Testing > Roundtrip > TypeDB > DirectVerify
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}
    Response Status Should Be    ${response}    201
    # API claims persisted
    ${json}=    Set Variable    ${response.json()}
    Should Be Equal    ${json}[persistence_status]    persisted
    # NOW VERIFY AT DB LEVEL — the real proof
    ${db_attrs}=    Task Should Exist In TypeDB    ${RT_TASK_ID}
    Should Be Equal    ${db_attrs}[task-id]    ${RT_TASK_ID}
    Should Be Equal    ${db_attrs}[task-status]    OPEN

Task GET Matches TypeDB Data
    [Documentation]    GET /api/tasks/{id} → compare API response against raw TypeDB query.
    ...                Proves service layer returns TypeDB data, not stale cache.
    [Tags]    e2e    roundtrip    read    critical
    ${response}=    API GET    /tasks/${RT_TASK_ID}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    # Cross-reference: API says OPEN, TypeDB says OPEN
    ${db_attrs}=    Query Task In TypeDB    ${RT_TASK_ID}
    Should Be Equal    ${json}[status]    ${db_attrs}[task-status]

Taxonomy Attributes Persist To TypeDB
    [Documentation]    POST task with layer/concern/method → verify all three in TypeDB directly.
    ...                Root cause: schema.tql had these attributes but live TypeDB did not.
    ...                EPIC-TASK-TAXONOMY-V2 schema migration was missing.
    [Tags]    e2e    roundtrip    taxonomy    critical
    ${body}=    Create Dictionary
    ...    task_id=${RT_TASK_LAYER}
    ...    description=Testing > Roundtrip > Taxonomy > LayerConcernMethod
    ...    status=OPEN
    ...    task_type=test
    ...    priority=LOW
    ...    workspace_id=${TEST_WORKSPACE}
    ...    layer=api
    ...    concern=reliability
    ...    method=automated
    ${response}=    API POST    /tasks    ${body}
    Response Status Should Be    ${response}    201
    # DB-level assertions — the REAL proof these attributes are in TypeDB
    TypeDB Task Attribute Should Be    ${RT_TASK_LAYER}    task-layer       api
    TypeDB Task Attribute Should Be    ${RT_TASK_LAYER}    task-concern     reliability
    TypeDB Task Attribute Should Be    ${RT_TASK_LAYER}    task-method      automated

Taxonomy Attributes Survive GET Round-Trip From TypeDB
    [Documentation]    GET → verify API returns same taxonomy values as TypeDB has.
    [Tags]    e2e    roundtrip    taxonomy    read
    ${response}=    API GET    /tasks/${RT_TASK_LAYER}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    # Cross-reference API response against DB
    ${db_attrs}=    Query Task In TypeDB    ${RT_TASK_LAYER}
    Should Be Equal    ${json}[layer]     ${db_attrs}[task-layer]
    Should Be Equal    ${json}[concern]   ${db_attrs}[task-concern]
    Should Be Equal    ${json}[method]    ${db_attrs}[task-method]

Deleted Task Removed From TypeDB
    [Documentation]    DELETE /api/tasks/{id} → task must be gone from TypeDB, not just cache.
    [Tags]    e2e    roundtrip    delete
    # Create a temporary task
    ${tmp_id}=    Set Variable    SRVJ-TEST-RT-DEL-001
    ${body}=    Create Dictionary
    ...    task_id=${tmp_id}
    ...    description=Testing > Roundtrip > Delete > TypeDB
    ...    task_type=test
    ...    workspace_id=${TEST_WORKSPACE}
    ${response}=    API POST    /tasks    ${body}
    Response Status Should Be    ${response}    201
    # Confirm it exists in TypeDB
    Task Should Exist In TypeDB    ${tmp_id}
    # Delete via API
    ${del_response}=    API DELETE    /tasks/${tmp_id}
    Should Be True    ${del_response.status_code} in [200, 204]
    # Confirm it's GONE from TypeDB
    Task Should Not Exist In TypeDB    ${tmp_id}
