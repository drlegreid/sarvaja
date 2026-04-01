*** Settings ***
Documentation    Task Audit Trail E2E Tests — SRVJ-FEAT-AUDIT-TRAIL-01 P2
...              Per TEST-E2E-01-v1: 3-level edge coverage (API + MCP + E2E).
...
...              LEVEL 1 — REST API: CRUD + link/unlink via REST, query audit via REST
...              LEVEL 2 — MCP: Link ops via MCP tools, query audit via MCP tools
...              LEVEL 3 — Playwright: Full UI journey — create, link, comment, verify in Audit view
...
...              NOTE: L1/L2 use separate tasks because MCP library runs in-process
...              (separate audit store from container). L3 uses the container path.

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Library     ../libraries/mcp_tasks.py
Library     ../libraries/mcp_audit.py

Suite Setup       Setup Audit Trail Suite
Suite Teardown    Teardown Audit Trail Suite

Default Tags    e2e    audit    tasks

*** Variables ***
${AUDIT_TASK_API}      SRVJ-TEST-AUDIT-API-001
${AUDIT_TASK_MCP}      SRVJ-TEST-AUDIT-MCP-001
${AUDIT_RULE_ID}       TEST-GUARD-01
${AUDIT_DOC_PATH}      docs/rules/leaf/TEST-GUARD-01-v1.md
${AUDIT_SESSION_ID}    SESSION-2026-03-28-AUDIT-E2E
${AUDIT_COMMIT_SHA}    abc123def456
${TEST_WORKSPACE}      WS-TEST-SANDBOX

*** Keywords ***
Setup Audit Trail Suite
    [Documentation]    Seed two test tasks: one via REST API, one via MCP.
    ...                Per TEST-DATA-01-v1: use sandbox workspace.
    Create API Session
    ${response}=    api.Create Test Task    ${AUDIT_TASK_API}
    ...    Audit > Trail > API > Edge
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}
    Response Status Should Be    ${response}    201
    ${result}=    MCP Task Create
    ...    name=Audit > Trail > MCP > Edge
    ...    task_id=${AUDIT_TASK_MCP}
    ...    task_type=test
    ...    priority=MEDIUM
    ...    workspace_id=${TEST_WORKSPACE}
    MCP Result Should Succeed    ${result}

Teardown Audit Trail Suite
    [Documentation]    Clean up both test tasks.
    api.Cleanup Test Task    ${AUDIT_TASK_API}
    ${result}=    MCP Task Delete    ${AUDIT_TASK_MCP}

*** Test Cases ***

# ═══════════════════════════════════════════════════════════════════════
# LEVEL 1 — REST API edge cases (container audit store)
# ═══════════════════════════════════════════════════════════════════════

L1 Link Rule Produces LINK Audit Entry
    [Documentation]    POST /tasks/{id}/rules/{rule_id} → audit trail has LINK entry
    ...                with linked_entity.type=rule.
    [Tags]    e2e    audit    api    link    rule    critical
    ${response}=    API POST    /tasks/${AUDIT_TASK_API}/rules/${AUDIT_RULE_ID}
    Should Be True    ${response.status_code} in [200, 201]
    ${audit}=    API GET    /audit/${AUDIT_TASK_API}
    Response Status Should Be    ${audit}    200
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "LINK"
            ${le}=    Set Variable    ${entry}[metadata][linked_entity]
            IF    "${le}[type]" == "rule" and "${le}[id]" == "${AUDIT_RULE_ID}"
                ${found}=    Set Variable    ${TRUE}
            END
        END
    END
    Should Be True    ${found}    No LINK audit entry with linked_entity.type=rule found

L1 Re-Link Same Rule Still Audits
    [Documentation]    EDGE: Linking same rule twice → second LINK entry still recorded.
    ...                Idempotent at TypeDB level but audit captures the attempt.
    [Tags]    e2e    audit    api    link    idempotency    edge
    ${response}=    API POST    /tasks/${AUDIT_TASK_API}/rules/${AUDIT_RULE_ID}
    ${audit}=    API GET    /audit/${AUDIT_TASK_API}
    ${entries}=    Set Variable    ${audit.json()}
    ${link_count}=    Set Variable    ${0}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "LINK"
            ${le}=    Set Variable    ${entry}[metadata][linked_entity]
            IF    "${le}[type]" == "rule"
                ${link_count}=    Evaluate    ${link_count} + 1
            END
        END
    END
    Should Be True    ${link_count} >= 2    Expected >=2 rule LINK entries, got ${link_count}

L1 Add Comment Preserves Author As Actor
    [Documentation]    POST comment → COMMENT audit entry has author as actor_id.
    ...                EDGE: actor_id must be the comment author, not "system".
    [Tags]    e2e    audit    api    comment    critical
    ${body}=    Create Dictionary    body=E2E audit trail comment    author=e2e-auditor
    ${response}=    API POST    /tasks/${AUDIT_TASK_API}/comments    ${body}
    Should Be True    ${response.status_code} in [200, 201]
    ${audit}=    API GET    /audit/${AUDIT_TASK_API}
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "COMMENT"
            Should Be Equal    ${entry}[actor_id]    e2e-auditor
            Should Be Equal    ${entry}[metadata][action]    add
            ${found}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${found}    No COMMENT audit entry found

L1 Update Priority Shows Field Changes With From And To
    [Documentation]    PUT non-status field → audit metadata.field_changes has exact from/to.
    [Tags]    e2e    audit    api    update    field_changes    edge
    ${body}=    Create Dictionary    priority=HIGH
    ${response}=    API PUT    /tasks/${AUDIT_TASK_API}    ${body}
    Should Be True    ${response.status_code} in [200, 204]
    ${audit}=    API GET    /audit/${AUDIT_TASK_API}
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "UPDATE"
            ${has_fc}=    Evaluate    "field_changes" in ${entry}.get("metadata", {})
            IF    ${has_fc}
                ${fc}=    Set Variable    ${entry}[metadata][field_changes]
                ${has_p}=    Evaluate    "priority" in ${fc}
                IF    ${has_p}
                    Should Be Equal    ${fc}[priority][to]    HIGH
                    ${found}=    Set Variable    ${TRUE}
                END
            END
        END
    END
    Should Be True    ${found}    No UPDATE with field_changes.priority found

L1 Status Update Has Non-Null New Value
    [Documentation]    PUT status change → old_value AND new_value both populated.
    ...                REGRESSION: P1 found new_value=null on some UPDATEs.
    [Tags]    e2e    audit    api    update    null_fix    critical
    ${body}=    Create Dictionary    status=IN_PROGRESS    agent_id=code-agent
    ${response}=    API PUT    /tasks/${AUDIT_TASK_API}    ${body}
    Should Be True    ${response.status_code} in [200, 204]
    ${audit}=    API GET    /audit/${AUDIT_TASK_API}
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "UPDATE" and "${entry}[new_value]" != "None"
            ${found}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${found}    All UPDATE entries have null new_value

L1 Link Then Unlink Document Produces Both LINK And UNLINK
    [Documentation]    POST link doc → DELETE unlink doc → audit has both LINK and UNLINK.
    ...                Proves TypeDB 3.x links-syntax unlink works end-to-end.
    [Tags]    e2e    audit    api    link    unlink    document    critical
    # Link
    ${link_body}=    Create Dictionary    document_path=${AUDIT_DOC_PATH}
    ${link_resp}=    API POST    /tasks/${AUDIT_TASK_API}/documents    ${link_body}
    Should Be True    ${link_resp.status_code} in [200, 201]
    # Unlink
    ${unlink_resp}=    API DELETE    /tasks/${AUDIT_TASK_API}/documents/${AUDIT_DOC_PATH}
    Should Be True    ${unlink_resp.status_code} in [200, 204]
    # Verify audit
    ${audit}=    API GET    /audit/${AUDIT_TASK_API}
    ${entries}=    Set Variable    ${audit.json()}
    ${has_link}=    Set Variable    ${FALSE}
    ${has_unlink}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "LINK"
            ${le}=    Set Variable    ${entry}[metadata][linked_entity]
            IF    "${le}[type]" == "document"
                ${has_link}=    Set Variable    ${TRUE}
            END
        END
        IF    "${entry}[action_type]" == "UNLINK"
            ${le}=    Set Variable    ${entry}[metadata][linked_entity]
            IF    "${le}[type]" == "document" and "${le}[action]" == "unlink"
                ${has_unlink}=    Set Variable    ${TRUE}
            END
        END
    END
    Should Be True    ${has_link}    No document LINK audit entry found
    Should Be True    ${has_unlink}    No document UNLINK audit entry found

L1 Full Lifecycle Journey
    [Documentation]    JOURNEY: After all L1 ops, audit trail has complete lifecycle.
    ...                CREATE → LINK(rule)x2 → COMMENT → UPDATE(priority) →
    ...                UPDATE(status) → LINK(document) → UNLINK(document)
    [Tags]    e2e    audit    api    journey    lifecycle    critical
    ${audit}=    API GET    /audit/${AUDIT_TASK_API}
    Response Status Should Be    ${audit}    200
    ${entries}=    Set Variable    ${audit.json()}
    ${actions}=    Create List
    FOR    ${entry}    IN    @{entries}
        Append To List    ${actions}    ${entry}[action_type]
    END
    Should Contain    ${actions}    CREATE
    Should Contain    ${actions}    LINK
    Should Contain    ${actions}    COMMENT
    Should Contain    ${actions}    UPDATE
    Should Contain    ${actions}    UNLINK

# ═══════════════════════════════════════════════════════════════════════
# LEVEL 2 — MCP tool edge cases (in-process audit store)
# ═══════════════════════════════════════════════════════════════════════

L2 MCP Link Session Has Session Correlation
    [Documentation]    MCP link_session → audit metadata.session_id equals linked session.
    [Tags]    e2e    audit    mcp    link    session    correlation    edge
    ${link}=    MCP Task Link Session    ${AUDIT_TASK_MCP}    ${AUDIT_SESSION_ID}
    MCP Result Should Succeed    ${link}
    ${trail}=    MCP Audit Entity Trail    ${AUDIT_TASK_MCP}
    Audit Trail Should Contain Action    ${trail}    LINK
    ${entries}=    Set Variable    ${trail}[entries]
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "LINK"
            ${le}=    Set Variable    ${entry}[metadata][linked_entity]
            IF    "${le}[type]" == "session"
                Should Be Equal    ${entry}[metadata][session_id]    ${AUDIT_SESSION_ID}
                Audit Entry Linked Entity Should Be    ${entry}    session    ${AUDIT_SESSION_ID}
                ${found}=    Set Variable    ${TRUE}
            END
        END
    END
    Should Be True    ${found}    No session LINK with session_id correlation found

L2 MCP Link Document Via Entity Trail
    [Documentation]    MCP link_document → audit_entity_trail has LINK with document metadata.
    [Tags]    e2e    audit    mcp    link    document
    ${link}=    MCP Task Link Document    ${AUDIT_TASK_MCP}    ${AUDIT_DOC_PATH}
    MCP Result Should Succeed    ${link}
    ${trail}=    MCP Audit Entity Trail    ${AUDIT_TASK_MCP}
    ${entries}=    Set Variable    ${trail}[entries]
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "LINK"
            ${le}=    Set Variable    ${entry}[metadata][linked_entity]
            IF    "${le}[type]" == "document"
                Should Be Equal    ${le}[id]    ${AUDIT_DOC_PATH}
                ${found}=    Set Variable    ${TRUE}
            END
        END
    END
    Should Be True    ${found}    No document LINK in MCP audit trail

L2 MCP Link Commit Via Entity Trail
    [Documentation]    MCP link_commit → audit_entity_trail has LINK with commit SHA.
    [Tags]    e2e    audit    mcp    link    commit
    ${link}=    MCP Task Link Commit    ${AUDIT_TASK_MCP}    ${AUDIT_COMMIT_SHA}    fix: audit trail
    MCP Result Should Succeed    ${link}
    ${trail}=    MCP Audit Entity Trail    ${AUDIT_TASK_MCP}
    ${entries}=    Set Variable    ${trail}[entries]
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "LINK"
            ${le}=    Set Variable    ${entry}[metadata][linked_entity]
            IF    "${le}[type]" == "commit"
                Should Be Equal    ${le}[id]    ${AUDIT_COMMIT_SHA}
                ${found}=    Set Variable    ${TRUE}
            END
        END
    END
    Should Be True    ${found}    No commit LINK in MCP audit trail

L2 MCP Audit Query Filters By LINK
    [Documentation]    MCP audit_query(action_type=LINK) returns only LINK entries.
    ...                Proves new action types are filterable via MCP.
    [Tags]    e2e    audit    mcp    query    filter    critical
    ${result}=    MCP Audit Query
    ...    entity_id=${AUDIT_TASK_MCP}
    ...    action_type=LINK
    ...    limit=50
    ${count}=    Set Variable    ${result}[count]
    Should Be True    ${count} >= 1    LINK filter returned 0 results
    FOR    ${entry}    IN    @{result}[entries]
        Should Be Equal    ${entry}[action_type]    LINK
    END

L2 MCP Timeline Summary Includes New Actions
    [Documentation]    audit_entity_trail timeline_summary.actions includes LINK.
    [Tags]    e2e    audit    mcp    timeline    summary    edge
    ${trail}=    MCP Audit Entity Trail    ${AUDIT_TASK_MCP}
    ${actions}=    Set Variable    ${trail}[timeline_summary][actions]
    Should Contain    ${actions}    LINK
    Should Contain    ${actions}    CREATE

L2 MCP Full Lifecycle Journey
    [Documentation]    JOURNEY: MCP-originated ops produce complete audit trail.
    ...                CREATE → LINK(session) → LINK(document) → LINK(commit)
    [Tags]    e2e    audit    mcp    journey    lifecycle    critical
    ${trail}=    MCP Audit Entity Trail    ${AUDIT_TASK_MCP}
    ${count}=    Set Variable    ${trail}[count]
    Should Be True    ${count} >= 4    Expected >=4 entries, got ${count}
    ${actions}=    Set Variable    ${trail}[timeline_summary][actions]
    Should Contain    ${actions}    CREATE
    Should Contain    ${actions}    LINK
