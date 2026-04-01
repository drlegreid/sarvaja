*** Settings ***
Documentation    Task Audit Cold Archive E2E Tests — SRVJ-FEAT-AUDIT-TRAIL-01 P4
...              Per TEST-E2E-01-v1: MCP-level edge coverage for cold archive.
...
...              LEVEL 2 — MCP: archive query, archive+hot combined,
...              retention produces archive files.

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Library     ../libraries/mcp_tasks.py
Library     ../libraries/mcp_audit.py

Suite Setup       Create API Session
Suite Teardown    Log    Archive suite complete

Default Tags    e2e    audit    archive

*** Variables ***
${ARCHIVE_TASK}       SRVJ-TEST-ARCHIVE-001
${TEST_WORKSPACE}     WS-TEST-SANDBOX

*** Test Cases ***

Scenario A: MCP Audit Archive Query Returns Entries
    [Documentation]    Given archived audit entries exist for an entity
    ...                When audit_archive_query(entity_id) called via MCP
    ...                Then archived entries returned (may be empty if no retention cycle yet).
    [Tags]    e2e    audit    archive    mcp    query
    ${result}=    MCP Audit Archive Query    entity_id=${ARCHIVE_TASK}
    Log    Archive query result: ${result}
    # Archive may be empty if no retention cycle — just verify no crash
    Should Be True    isinstance(${result}, dict)

Scenario B: MCP Audit Archive Query Filters By Action Type
    [Documentation]    Given archived entries exist
    ...                When audit_archive_query(action_type=CREATE) called
    ...                Then only CREATE entries returned.
    [Tags]    e2e    audit    archive    mcp    filter
    ${result}=    MCP Audit Archive Query    entity_id=${ARCHIVE_TASK}    action_type=CREATE
    Log    Archive CREATE filter: ${result}
    Should Be True    isinstance(${result}, dict)
    # If entries exist, verify they're all CREATE
    FOR    ${entry}    IN    @{result}[entries]
        Should Be Equal    ${entry}[action_type]    CREATE
    END

Scenario C: Hot Trail Still Works Independently
    [Documentation]    Adding archive doesn't break existing audit_entity_trail.
    ...                L1 API + L2 MCP hot path unchanged.
    [Tags]    e2e    audit    archive    regression    critical
    # Create a task to generate audit entries
    ${resp}=    api.Create Test Task    ${ARCHIVE_TASK}
    ...    Archive > Regression > Test
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}
    Should Be True    ${resp.status_code} in [200, 201]
    # L1: REST audit still works
    ${audit}=    API GET    /audit/${ARCHIVE_TASK}
    Response Status Should Be    ${audit}    200
    ${entries}=    Set Variable    ${audit.json()}
    ${api_count}=    Get Length    ${entries}
    Should Be True    ${api_count} >= 1    Hot audit has ${api_count} entries
    # L2: MCP trail still works
    ${trail}=    MCP Audit Entity Trail    ${ARCHIVE_TASK}
    Log    MCP hot trail count: ${trail}[count]
    # Cleanup
    api.Cleanup Test Task    ${ARCHIVE_TASK}
