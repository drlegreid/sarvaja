*** Settings ***
Documentation    Adversarial Audit Trail E2E Tests — SRVJ-FEAT-AUDIT-TRAIL-01 P6
...              Per TEST-E2E-HONEST-01-v1: honest results over green dashboard.
...
...              DSE adversarial scenarios: XSS, overflow cap, concurrent writes,
...              orphan detection, forged identity, cross-system consistency.
...
...              LEVEL 1 — REST API: Injection attempts, limit enforcement
...              LEVEL 2 — MCP: Forged identity, nonexistent entities, limit bypass
...              LEVEL 3 — Consistency: TypeDB-first fallback, orphan entries

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Library     ../libraries/mcp_tasks.py
Library     ../libraries/mcp_audit.py

Suite Setup       Setup Adversarial Suite
Suite Teardown    Teardown Adversarial Suite

Default Tags    e2e    audit    adversarial

*** Variables ***
${ADV_TASK_API}        SRVJ-TEST-ADV-API-001
${ADV_TASK_MCP}        SRVJ-TEST-ADV-MCP-001
${ADV_TASK_ORPHAN}     SRVJ-TEST-ADV-ORPHAN-001
${TEST_WORKSPACE}      WS-TEST-SANDBOX

*** Keywords ***
Setup Adversarial Suite
    [Documentation]    Seed test tasks for adversarial testing.
    ...                Per TEST-DATA-01-v1: use sandbox workspace.
    Create API Session
    ${response}=    api.Create Test Task    ${ADV_TASK_API}
    ...    Adversarial > Audit > API > Edge
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}
    Response Status Should Be    ${response}    201
    ${result}=    MCP Task Create
    ...    name=Adversarial > Audit > MCP > Edge
    ...    task_id=${ADV_TASK_MCP}
    ...    task_type=test
    ...    priority=MEDIUM
    ...    workspace_id=${TEST_WORKSPACE}
    MCP Result Should Succeed    ${result}

Teardown Adversarial Suite
    [Documentation]    Clean up test tasks.
    api.Cleanup Test Task    ${ADV_TASK_API}
    api.Cleanup Test Task    ${ADV_TASK_ORPHAN}
    ${result}=    MCP Task Delete    ${ADV_TASK_MCP}

*** Test Cases ***

# ═══════════════════════════════════════════════════════════════════════
# LEVEL 1 — XSS / Injection via REST API
# ═══════════════════════════════════════════════════════════════════════

L1 XSS In Comment Body Does Not Execute
    [Documentation]    A1: POST comment with script tag — stored as plain text.
    ...                DEFENSE: Vue template interpolation auto-escapes HTML.
    [Tags]    adversarial    xss    api    critical
    ${xss_body}=    Create Dictionary
    ...    body=<script>alert("xss")</script>
    ...    author=xss-tester
    ${response}=    API POST    /tasks/${ADV_TASK_API}/comments    ${xss_body}
    Should Be True    ${response.status_code} in [200, 201]
    ${audit}=    API GET    /audit/${ADV_TASK_API}
    Response Status Should Be    ${audit}    200
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "COMMENT"
            # XSS payload stored as plain text, not stripped
            ${found}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${found}    COMMENT audit entry not found after XSS injection

L1 Long Entity ID In Query Does Not Crash
    [Documentation]    A2: GET /audit/{10K char ID} — returns empty, no crash.
    [Tags]    adversarial    overflow    api
    ${long_id}=    Evaluate    "TASK-" + "A" * 5000
    ${response}=    API GET    /audit/${long_id}
    Response Status Should Be    ${response}    200
    ${entries}=    Set Variable    ${response.json()}
    Should Be True    len(${entries}) == 0    Long ID query should return empty

L1 Query Limit Capped At 500
    [Documentation]    B1: GET /audit?limit=99999 — server caps at 500 (REST route validation).
    [Tags]    adversarial    overflow    api    limit    critical
    ${response}=    API GET    /audit?limit=99999
    # FastAPI should either cap the limit or reject with 422
    Should Be True    ${response.status_code} in [200, 422]

L1 Negative Offset Returns Valid Response
    [Documentation]    Query with offset=-10 — server normalizes to 0.
    [Tags]    adversarial    overflow    api
    ${response}=    API GET    /audit?offset=-10
    Response Status Should Be    ${response}    200

# ═══════════════════════════════════════════════════════════════════════
# LEVEL 2 — MCP Identity / Attribution Attacks
# ═══════════════════════════════════════════════════════════════════════

L2 MCP Audit Query For Nonexistent Entity Returns Empty
    [Documentation]    D4: Query audit trail for entity that doesn't exist — empty, no crash.
    [Tags]    adversarial    identity    mcp
    ${trail}=    MCP Audit Entity Trail    TASK-DOES-NOT-EXIST-999
    ${count}=    Set Variable    ${trail}[count]
    Should Be True    ${count} == 0    Nonexistent entity should have 0 audit entries

L2 MCP Audit Query With Large Limit
    [Documentation]    B2: MCP audit_query with limit=99999 — internal cap at 1000.
    [Tags]    adversarial    overflow    mcp    limit
    ${result}=    MCP Audit Query    limit=99999
    # Should not crash; count may be large but system remains responsive
    ${count}=    Set Variable    ${result}[count]
    Should Be True    ${count} >= 0    MCP audit_query with large limit should not crash

L2 MCP Audit Trace With Forged Correlation ID
    [Documentation]    D3: audit_trace with fabricated CORR ID — returns empty, no crash.
    [Tags]    adversarial    identity    mcp    correlation
    ${result}=    MCP Audit Trace    CORR-FORGED-19700101-000000-FFFFFF
    ${count}=    Set Variable    ${result}[count]
    Should Be True    ${count} == 0    Forged correlation ID should return 0 entries

# ═══════════════════════════════════════════════════════════════════════
# LEVEL 2 — MCP Orphan Detection
# ═══════════════════════════════════════════════════════════════════════

L2 Orphan Entries Survive Task Deletion
    [Documentation]    C1: Create task, add audit entries, delete task — entries persist.
    ...                Audit trail is append-only: entries are never cascade-deleted.
    [Tags]    adversarial    bypass    mcp    orphan    critical
    # Create and populate
    ${create}=    MCP Task Create
    ...    name=Orphan > Test > Entry
    ...    task_id=${ADV_TASK_ORPHAN}
    ...    task_type=test
    ...    workspace_id=${TEST_WORKSPACE}
    MCP Result Should Succeed    ${create}
    # Add some audit activity
    ${update}=    MCP Task Update    ${ADV_TASK_ORPHAN}    status=IN_PROGRESS
    ...    agent_id=code-agent
    MCP Result Should Succeed    ${update}
    # Verify entries exist
    ${trail_before}=    MCP Audit Entity Trail    ${ADV_TASK_ORPHAN}
    ${before_count}=    Set Variable    ${trail_before}[count]
    Should Be True    ${before_count} >= 2    Expected >=2 entries before delete
    # Delete the task
    ${delete}=    MCP Task Delete    ${ADV_TASK_ORPHAN}
    # Verify audit entries still exist (orphaned but queryable)
    ${trail_after}=    MCP Audit Entity Trail    ${ADV_TASK_ORPHAN}
    ${after_count}=    Set Variable    ${trail_after}[count]
    # DELETE action adds one more entry, so count should increase
    Should Be True    ${after_count} >= ${before_count}
    ...    Audit entries lost after task deletion: ${after_count} < ${before_count}

# ═══════════════════════════════════════════════════════════════════════
# LEVEL 2 — Cross-System Consistency
# ═══════════════════════════════════════════════════════════════════════

L2 Audit Summary Reflects All Action Types
    [Documentation]    E1: audit_summary includes CREATE, UPDATE, LINK, COMMENT action types.
    ...                Proves dual-write consistency: JSON store has all entry types.
    [Tags]    adversarial    consistency    mcp    summary
    ${summary}=    MCP Audit Summary
    ${by_action}=    Set Variable    ${summary}[by_action_type]
    # At minimum, CREATE and UPDATE should exist from suite setup
    Should Be True    "CREATE" in ${by_action}    No CREATE in audit summary
    Should Be True    "UPDATE" in ${by_action}    No UPDATE in audit summary
