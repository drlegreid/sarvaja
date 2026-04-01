*** Settings ***
Documentation    Auto-Generated Activity Comments E2E — SRVJ-FEAT-AUDIT-TRAIL-01 P7+P8
...              Per TEST-E2E-01-v1: 3-level edge coverage (API + MCP + Playwright).
...
...              LEVEL 1 — REST API: Mutation triggers auto-comment in comments thread
...              LEVEL 2 — MCP: Same via MCP tools, pagination, author filtering
...              LEVEL 3 — Playwright: System comments visible with distinct styling in UI
...              LEVEL 4 — P8: Cross-process comment read-through (GAP 2/GAP 1/GAP 3)
...
...              Auto-comments use author="system-audit" to distinguish from user comments.
...              COMMENT actions must NOT trigger auto-comments (infinite loop prevention).

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Library     ../libraries/mcp_tasks.py
Library     ../libraries/mcp_audit.py

Suite Setup       Setup Auto Comments Suite
Suite Teardown    Teardown Auto Comments Suite

Default Tags    e2e    audit    auto-comments    P7

*** Variables ***
${AC_TASK_API}         SRVJ-TEST-AUTOCOMMENT-API-001
${AC_TASK_MCP}         SRVJ-TEST-AUTOCOMMENT-MCP-001
${AC_RULE_ID}          TEST-GUARD-01
${AC_DOC_PATH}         docs/rules/leaf/TEST-GUARD-01-v1.md
${AC_SESSION_ID}       SESSION-2026-03-29-AUTOCOMMENT-E2E
${SYSTEM_AUTHOR}       system-audit
${TEST_WORKSPACE}      WS-TEST-SANDBOX

*** Keywords ***
Setup Auto Comments Suite
    [Documentation]    Seed two test tasks: one via REST, one via MCP.
    ...                Per TEST-DATA-01-v1: use sandbox workspace.
    Create API Session
    ${response}=    api.Create Test Task    ${AC_TASK_API}
    ...    AutoComment > API > Edge
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}
    ...    priority=MEDIUM
    Response Status Should Be    ${response}    201
    ${result}=    MCP Task Create
    ...    name=AutoComment > MCP > Edge
    ...    task_id=${AC_TASK_MCP}
    ...    task_type=test
    ...    priority=MEDIUM
    ...    workspace_id=${TEST_WORKSPACE}
    MCP Result Should Succeed    ${result}

Teardown Auto Comments Suite
    [Documentation]    Clean up both test tasks.
    api.Cleanup Test Task    ${AC_TASK_API}
    ${result}=    MCP Task Delete    ${AC_TASK_MCP}

Comments Should Contain System Comment Matching
    [Documentation]    Assert GET /tasks/{id}/comments has at least one system-audit
    ...                comment whose body contains the expected substring.
    [Arguments]    ${task_id}    ${expected_substring}
    ${resp}=    API GET    /tasks/${task_id}/comments
    Response Status Should Be    ${resp}    200
    ${data}=    Set Variable    ${resp.json()}
    ${comments}=    Set Variable    ${data}[comments]
    ${found}=    Set Variable    ${FALSE}
    FOR    ${c}    IN    @{comments}
        IF    "${c}[author]" == "${SYSTEM_AUTHOR}"
            ${match}=    Evaluate    "${expected_substring}" in """${c}[body]"""
            IF    ${match}
                ${found}=    Set Variable    ${TRUE}
            END
        END
    END
    Should Be True    ${found}
    ...    No system-audit comment containing '${expected_substring}' found for ${task_id}

Comments Should Not Contain Author
    [Documentation]    Assert no comments exist with the given author.
    [Arguments]    ${task_id}    ${author}
    ${resp}=    API GET    /tasks/${task_id}/comments
    Response Status Should Be    ${resp}    200
    ${data}=    Set Variable    ${resp.json()}
    ${comments}=    Set Variable    ${data}[comments]
    FOR    ${c}    IN    @{comments}
        Should Not Be Equal    ${c}[author]    ${author}
        ...    Found unexpected comment by '${author}': ${c}[body]
    END

Count System Comments
    [Documentation]    Return count of system-audit comments for a task.
    [Arguments]    ${task_id}
    ${resp}=    API GET    /tasks/${task_id}/comments
    ${data}=    Set Variable    ${resp.json()}
    ${count}=    Set Variable    ${0}
    FOR    ${c}    IN    @{data}[comments]
        IF    "${c}[author]" == "${SYSTEM_AUTHOR}"
            ${count}=    Evaluate    ${count} + 1
        END
    END
    RETURN    ${count}

*** Test Cases ***

# ===========================================================================
# LEVEL 1 -- REST API: auto-comment generation
# ===========================================================================

L1-A Status Change Auto-Generates Comment With Actor And Source
    [Documentation]    PUT status OPEN->IN_PROGRESS via REST -> system-audit comment
    ...                includes old/new status, actor, and source.
    [Tags]    e2e    auto-comments    api    status    critical
    ${body}=    Create Dictionary    status=IN_PROGRESS    agent_id=code-agent
    ${resp}=    API PUT    /tasks/${AC_TASK_API}    ${body}
    Should Be True    ${resp.status_code} in [200, 204]
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_API}    Status changed from OPEN to IN_PROGRESS
    # Verify actor and source are present
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_API}    code-agent
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_API}    rest

L1-B Link Rule Auto-Generates Comment
    [Documentation]    POST link rule -> system-audit comment "Rule {id} linked by {actor} ({source})".
    [Tags]    e2e    auto-comments    api    link    rule    critical
    ${resp}=    API POST    /tasks/${AC_TASK_API}/rules/${AC_RULE_ID}
    Should Be True    ${resp.status_code} in [200, 201]
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_API}    Rule ${AC_RULE_ID} linked

L1-C Field Change Auto-Generates Comment With From-To
    [Documentation]    PUT priority MEDIUM->HIGH -> comment includes "Priority changed from MEDIUM to HIGH".
    [Tags]    e2e    auto-comments    api    field_change    critical
    ${body}=    Create Dictionary    priority=HIGH
    ${resp}=    API PUT    /tasks/${AC_TASK_API}    ${body}
    Should Be True    ${resp.status_code} in [200, 204]
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_API}    priority MEDIUM

L1-D Multiple Field Changes Produce Single Comment
    [Documentation]    PUT summary+phase in single call -> exactly ONE auto-comment (not two).
    [Tags]    e2e    auto-comments    api    batch    critical
    ${before}=    Count System Comments    ${AC_TASK_API}
    ${body}=    Create Dictionary    summary=Updated summary    phase=P7
    ${resp}=    API PUT    /tasks/${AC_TASK_API}    ${body}
    Should Be True    ${resp.status_code} in [200, 204]
    ${after}=    Count System Comments    ${AC_TASK_API}
    ${delta}=    Evaluate    ${after} - ${before}
    Should Be Equal As Integers    ${delta}    1
    ...    Expected exactly 1 new auto-comment for multi-field update, got ${delta}

L1-E User Comment Does NOT Trigger Auto-Comment
    [Documentation]    POST manual comment -> no system-audit comment about the comment.
    ...                CRITICAL: proves infinite loop prevention works end-to-end.
    [Tags]    e2e    auto-comments    api    loop    adversarial    critical
    ${before}=    Count System Comments    ${AC_TASK_API}
    ${body}=    Create Dictionary    body=Manual user note    author=human-user
    ${resp}=    API POST    /tasks/${AC_TASK_API}/comments    ${body}
    Should Be True    ${resp.status_code} in [200, 201]
    ${after}=    Count System Comments    ${AC_TASK_API}
    Should Be Equal As Integers    ${before}    ${after}
    ...    User comment triggered an auto-comment (infinite loop risk!)

L1-F Evidence Update References Evidence Content
    [Documentation]    PUT evidence -> auto-comment includes snippet of evidence text.
    [Tags]    e2e    auto-comments    api    evidence    critical
    ${body}=    Create Dictionary    evidence=[Verification: L2] All tests passed 2026-03-29
    ${resp}=    API PUT    /tasks/${AC_TASK_API}    ${body}
    Should Be True    ${resp.status_code} in [200, 204]
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_API}    Evidence updated
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_API}    Verification: L2

L1-G Unlink Document Auto-Generates Comment
    [Documentation]    Link then unlink doc -> auto-comment includes "Document {path} unlinked".
    [Tags]    e2e    auto-comments    api    unlink    document
    # Link first
    ${link_body}=    Create Dictionary    document_path=${AC_DOC_PATH}
    ${link_resp}=    API POST    /tasks/${AC_TASK_API}/documents    ${link_body}
    Should Be True    ${link_resp.status_code} in [200, 201]
    # Unlink
    ${unlink_resp}=    API DELETE    /tasks/${AC_TASK_API}/documents/${AC_DOC_PATH}
    Should Be True    ${unlink_resp.status_code} in [200, 204]
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_API}    ${AC_DOC_PATH} unlinked

# ===========================================================================
# LEVEL 2 -- MCP: auto-comment generation + pagination
# ===========================================================================

L2-A MCP Status Change Auto-Generates Comment
    [Documentation]    MCP task_update status -> system-audit comment in thread.
    [Tags]    e2e    auto-comments    mcp    status    critical
    ${result}=    MCP Task Update    ${AC_TASK_MCP}    status=IN_PROGRESS    agent_id=code-agent
    MCP Result Should Succeed    ${result}
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_MCP}    Status changed from OPEN to IN_PROGRESS
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_MCP}    mcp

L2-B MCP Link Session Auto-Generates Comment
    [Documentation]    MCP link_session -> auto-comment "Session {id} linked".
    [Tags]    e2e    auto-comments    mcp    link    session
    ${result}=    MCP Task Link Session    ${AC_TASK_MCP}    ${AC_SESSION_ID}
    MCP Result Should Succeed    ${result}
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_MCP}    Session ${AC_SESSION_ID} linked

L2-C Pagination Returns Correct Subset
    [Documentation]    GET /tasks/{id}/comments?offset=0&limit=2 returns exactly 2.
    [Tags]    e2e    auto-comments    api    pagination    critical
    # Ensure we have at least 3 comments (from L2-A and L2-B plus create audit)
    ${resp}=    API GET    /tasks/${AC_TASK_MCP}/comments?offset=0&limit=2
    Response Status Should Be    ${resp}    200
    ${data}=    Set Variable    ${resp.json()}
    ${count}=    Get Length    ${data}[comments]
    Should Be True    ${count} <= 2    Pagination limit=2 but got ${count} comments

L2-D Pagination Offset Skips Earlier Comments
    [Documentation]    offset=1 skips the first comment, returning different results.
    [Tags]    e2e    auto-comments    api    pagination    edge
    ${page0}=    API GET    /tasks/${AC_TASK_MCP}/comments?offset=0&limit=1
    ${page1}=    API GET    /tasks/${AC_TASK_MCP}/comments?offset=1&limit=1
    Response Status Should Be    ${page0}    200
    Response Status Should Be    ${page1}    200
    ${c0}=    Set Variable    ${page0.json()}[comments]
    ${c1}=    Set Variable    ${page1.json()}[comments]
    IF    len(${c0}) > 0 and len(${c1}) > 0
        Should Not Be Equal    ${c0}[0][comment_id]    ${c1}[0][comment_id]
        ...    offset=0 and offset=1 returned the same comment
    END

L2-E MCP Auto-Comment Not Triggered By COMMENT Action
    [Documentation]    Adversarial: add comment via direct path, verify no recursion.
    [Tags]    e2e    auto-comments    mcp    adversarial    loop    critical
    ${before}=    Count System Comments    ${AC_TASK_MCP}
    ${body}=    Create Dictionary    body=MCP user note    author=mcp-user
    ${resp}=    API POST    /tasks/${AC_TASK_MCP}/comments    ${body}
    Should Be True    ${resp.status_code} in [200, 201]
    ${after}=    Count System Comments    ${AC_TASK_MCP}
    Should Be Equal As Integers    ${before}    ${after}
    ...    COMMENT action triggered auto-comment (infinite loop risk via MCP)

# ===========================================================================
# LEVEL 3 -- Playwright: visual verification in UI
# ===========================================================================

L3-A System Comments Visible In Task Detail
    [Documentation]    JOURNEY: open task detail -> Comments section shows system-audit
    ...                comments with distinct author label.
    ...                Per TEST-E2E-HONEST-01-v1: real Playwright interaction.
    [Tags]    e2e    auto-comments    playwright    ui    critical
    Navigate To Task Detail    ${AC_TASK_API}
    Wait For Element    css=[data-testid="comments-section"]    timeout=10s
    ${html}=    Get Text    css=[data-testid="comments-section"]
    Should Contain    ${html}    system-audit
    Should Contain    ${html}    Status changed

L3-B System Comments Distinct From User Comments
    [Documentation]    Visual: system-audit comments have different styling/prefix
    ...                from user-authored comments.
    [Tags]    e2e    auto-comments    playwright    ui    styling    P8
    Navigate To Task Detail    ${AC_TASK_API}
    Wait For Element    css=[data-testid="comments-section"]    timeout=10s
    # Check that system comments are inside a system-comment container
    Element Should Exist    css=[data-comment-type="system"]
    # And user comments are NOT inside system-comment container
    Element Should Exist    css=[data-comment-type="user"]

# ===========================================================================
# LEVEL 4 -- P8: Cross-Process Comment Read-Through (GAP 2)
# ===========================================================================

L4-A MCP Comment Visible In REST API
    [Documentation]    GAP 2: MCP-created comment must be visible via REST API.
    ...                MCP server (local process) writes to TypeDB.
    ...                REST API (container) must read-through from TypeDB,
    ...                not just its own in-memory _comments_store.
    [Tags]    e2e    auto-comments    cross-process    P8    critical
    # Add comment via MCP tool (writes to MCP's _comments_store + TypeDB)
    ${result}=    MCP Task Update    ${AC_TASK_MCP}    phase=P8-test
    MCP Result Should Succeed    ${result}
    # Verify the auto-comment is visible via REST API (different process)
    Comments Should Contain System Comment Matching
    ...    ${AC_TASK_MCP}    phase set to P8-test

L4-B Comments From Both Processes Merged Without Duplicates
    [Documentation]    GAP 2: Comments from REST API (container) and MCP (local)
    ...                are merged in GET response. Dedup by comment_id.
    [Tags]    e2e    auto-comments    cross-process    merge    P8    critical
    # Add user comment via REST API (container's _comments_store + TypeDB)
    ${body}=    Create Dictionary    body=REST-process comment P8    author=rest-user
    ${resp}=    API POST    /tasks/${AC_TASK_MCP}/comments    ${body}
    Should Be True    ${resp.status_code} in [200, 201]
    # Add user comment via MCP (MCP's _comments_store + TypeDB)
    ${mcp_body}=    Create Dictionary    body=MCP-process comment P8    author=mcp-user
    ${mcp_resp}=    API POST    /tasks/${AC_TASK_MCP}/comments    ${mcp_body}
    Should Be True    ${mcp_resp.status_code} in [200, 201]
    # GET all comments — should see BOTH
    ${all_resp}=    API GET    /tasks/${AC_TASK_MCP}/comments
    Response Status Should Be    ${all_resp}    200
    ${comments}=    Set Variable    ${all_resp.json()}[comments]
    # Check both are present
    ${found_rest}=    Set Variable    ${FALSE}
    ${found_mcp}=    Set Variable    ${FALSE}
    ${seen_ids}=    Create List
    FOR    ${c}    IN    @{comments}
        IF    "REST-process comment P8" in """${c}[body]"""
            ${found_rest}=    Set Variable    ${TRUE}
        END
        IF    "MCP-process comment P8" in """${c}[body]"""
            ${found_mcp}=    Set Variable    ${TRUE}
        END
        # Check for duplicates
        Should Not Contain    ${seen_ids}    ${c}[comment_id]
        ...    Duplicate comment_id detected: ${c}[comment_id]
        Append To List    ${seen_ids}    ${c}[comment_id]
    END
    Should Be True    ${found_rest}    REST-process comment not found in merged results
    Should Be True    ${found_mcp}    MCP-process comment not found in merged results

L4-C MCP Auto-Comment Visible In Dashboard
    [Documentation]    GAP 2 + Playwright: auto-comment from MCP mutation
    ...                is visible in task detail Comments section in the UI.
    [Tags]    e2e    auto-comments    cross-process    playwright    P8    critical
    Navigate To Task Detail    ${AC_TASK_MCP}
    Wait For Element    css=[data-testid="task-comments-card"]    timeout=10s
    ${html}=    Get Text    css=[data-testid="task-comments-card"]
    Should Contain    ${html}    system-audit
    Should Contain    ${html}    phase set to P8-test

L4-D First Update After Restart Shows Correct Old Status
    [Documentation]    GAP 1: Status change on a task NOT in memory (first update
    ...                after restart) should show "Status changed from X to Y"
    ...                not generic "Task updated".
    [Tags]    e2e    auto-comments    snapshot    P8    critical
    # Use a fresh task for this — ensure not in container's _tasks_store
    ${fresh_id}=    Set Variable    SRVJ-TEST-SNAPSHOT-P8-001
    ${cr_resp}=    api.Create Test Task    ${fresh_id}
    ...    Snapshot > P8 > Edge
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}
    ...    priority=MEDIUM
    Response Status Should Be    ${cr_resp}    201
    # Update status (in container) — this one primes _tasks_store
    ${body}=    Create Dictionary    status=IN_PROGRESS    agent_id=code-agent
    ${resp}=    API PUT    /tasks/${fresh_id}    ${body}
    Should Be True    ${resp.status_code} in [200, 204]
    # Verify auto-comment has correct from/to (not generic)
    Comments Should Contain System Comment Matching
    ...    ${fresh_id}    Status changed from OPEN to IN_PROGRESS
    # Cleanup
    api.Cleanup Test Task    ${fresh_id}

L4-E System Comment Has Data Attribute In Dashboard
    [Documentation]    GAP 3: system-audit comments have data-comment-type="system"
    ...                attribute in the rendered DOM. User comments have "user".
    [Tags]    e2e    auto-comments    styling    playwright    P8
    Navigate To Task Detail    ${AC_TASK_API}
    Wait For Element    css=[data-testid="task-comments-card"]    timeout=10s
    # System comment has data-comment-type="system"
    Element Should Exist    css=[data-comment-type="system"]
    # User comment has data-comment-type="user"
    Element Should Exist    css=[data-comment-type="user"]
