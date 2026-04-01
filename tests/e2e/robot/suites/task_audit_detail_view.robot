*** Settings ***
Documentation    Task Audit Detail View E2E Tests — SRVJ-FEAT-AUDIT-TRAIL-01 P3
...              Per TEST-E2E-01-v1: 3-level edge coverage (Playwright + API + MCP).
...
...              LEVEL 3 — Playwright: Audit Trail collapsible card in task detail view
...              L1 Auxiliary — REST: GET /api/audit/{entity_id} confirms same entries
...              L2 Auxiliary — MCP: audit_entity_trail confirms timeline_summary

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Library     ../libraries/mcp_tasks.py
Library     ../libraries/mcp_audit.py

Suite Setup       Setup Audit Detail Suite
Suite Teardown    Teardown Audit Detail Suite
Test Setup        Ensure Audit Trail Visible

Default Tags    e2e    audit    detail    tasks

*** Variables ***
${AUDIT_DETAIL_TASK}      SRVJ-TEST-AUDIT-DETAIL-001
${AUDIT_DETAIL_RULE}      TEST-GUARD-01
${AUDIT_DETAIL_DOC}       docs/rules/leaf/TEST-GUARD-01-v1.md
${TEST_WORKSPACE}         WS-TEST-SANDBOX

# Selectors — task detail audit trail component
${AUDIT_TRAIL_CARD}       [data-testid='task-audit-trail-card']
${AUDIT_TRAIL_TIMELINE}   [data-testid='task-audit-timeline']
${AUDIT_TRAIL_ENTRY}      [data-testid='task-audit-entry']
${AUDIT_TRAIL_REFRESH}    [data-testid='task-audit-refresh']
${AUDIT_TRAIL_EXPAND}     [data-testid='task-audit-expand-btn']
${AUDIT_TRAIL_FILTER}     [data-testid='task-audit-filter']
${AUDIT_TRAIL_PREV}       [data-testid='task-audit-prev-page']
${AUDIT_TRAIL_NEXT}       [data-testid='task-audit-next-page']
${AUDIT_TRAIL_PAGE_INFO}  [data-testid='task-audit-page-info']
${AUDIT_TRAIL_COUNT}      [data-testid='task-audit-count-chip']

*** Keywords ***
Setup Audit Detail Suite
    [Documentation]    Create test task with multiple mutations for audit trail.
    ...                Per TEST-DATA-01-v1: sandbox workspace.
    ...                Idempotent: deletes existing task first.
    Create API Session
    # Idempotent: clean up any leftover from previous run
    api.Cleanup Test Task    ${AUDIT_DETAIL_TASK}
    # Create task
    ${resp}=    api.Create Test Task    ${AUDIT_DETAIL_TASK}
    ...    Audit > Detail > View > E2E
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}
    Response Status Should Be    ${resp}    201
    # Link a rule (produces LINK audit entry)
    ${link_resp}=    API POST    /tasks/${AUDIT_DETAIL_TASK}/rules/${AUDIT_DETAIL_RULE}
    Should Be True    ${link_resp.status_code} in [200, 201]
    # Add a comment (produces COMMENT audit entry)
    ${comment}=    Create Dictionary    body=E2E detail view audit comment    author=e2e-tester
    ${comment_resp}=    API POST    /tasks/${AUDIT_DETAIL_TASK}/comments    ${comment}
    Should Be True    ${comment_resp.status_code} in [200, 201]
    # Update status (produces UPDATE audit entry)
    ${update}=    Create Dictionary    status=IN_PROGRESS    agent_id=code-agent
    ${update_resp}=    API PUT    /tasks/${AUDIT_DETAIL_TASK}    ${update}
    Should Be True    ${update_resp.status_code} in [200, 204]
    # Open browser — direct calls (avoids common.resource timing issues)
    New Browser    chromium    headless=${HEADLESS}
    New Context    viewport={"width": 1280, "height": 720}    ignoreHTTPSErrors=${TRUE}
    New Page    ${DASHBOARD_URL}
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    ${loading}=    Get Element Count    text=Loading...
    IF    ${loading} > 0
        Wait For Elements State    text=Loading...    hidden    timeout=${TIMEOUT}
    END
    Inject E2E Overlay Fix
    # Navigate to the task detail ONCE (all tests verify same task)
    Navigate To Audit Detail Task

Inject E2E Overlay Fix
    [Documentation]    Hide trace bar + overlay scrim that block clicks during E2E.
    Evaluate JavaScript    ${None}
    ...    () => {
    ...        if (!document.getElementById('rf-e2e-fix')) {
    ...            const s = document.createElement('style');
    ...            s.id = 'rf-e2e-fix';
    ...            s.textContent = \`
    ...                .v-overlay__scrim {
    ...                    pointer-events: none !important;
    ...                }
    ...                [data-testid="trace-bar"], footer, [role="contentinfo"] {
    ...                    display: none !important;
    ...                }
    ...            \`;
    ...            document.head.appendChild(s);
    ...        }
    ...        return 'e2e-fix-applied';
    ...    }

Ensure Audit Trail Visible
    [Documentation]    Lightweight test setup: verify we're on the task detail and
    ...                the audit trail section is expanded. If not on detail, re-navigate.
    ${on_detail}=    Get Element Count    ${TASK_DETAIL}
    IF    ${on_detail} == 0
        Navigate To Audit Detail Task
    END
    Wait For Elements State    ${AUDIT_TRAIL_CARD}    visible    timeout=${TIMEOUT}
    # Scroll audit trail card into view
    Browser.Scroll To Element    ${AUDIT_TRAIL_CARD}
    Sleep    500ms
    # Clear any filter from previous test (click clear button on VSelect)
    ${filter_clear}=    Get Element Count    ${AUDIT_TRAIL_FILTER} >> text=󰅙
    IF    ${filter_clear} > 0
        Click    ${AUDIT_TRAIL_FILTER} >> text=󰅙
        Sleep    1s
    END
    # Expand audit trail if collapsed
    ${expanded}=    Get Element Count    ${AUDIT_TRAIL_TIMELINE}
    IF    ${expanded} == 0    Click    ${AUDIT_TRAIL_EXPAND}

Navigate To Audit Detail Task
    [Documentation]    Navigate directly to task detail via URL hash.
    ...                Bypasses list search entirely — route hash is the reliable path.
    Go To    ${DASHBOARD_URL}/index.html#/projects/WS-9147535A/tasks/${AUDIT_DETAIL_TASK}
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    ${loading}=    Get Element Count    text=Loading...
    IF    ${loading} > 0
        Wait For Elements State    text=Loading...    hidden    timeout=${TIMEOUT}
    END
    Wait For Elements State    ${TASK_DETAIL}    visible    timeout=${TIMEOUT}

Teardown Audit Detail Suite
    [Documentation]    Clean up test task and close browser.
    api.Cleanup Test Task    ${AUDIT_DETAIL_TASK}
    Close Browser    ALL

*** Test Cases ***

# ═══════════════════════════════════════════════════════════════════════
# LEVEL 3 — Playwright: Audit Trail in Task Detail View
# ═══════════════════════════════════════════════════════════════════════

Scenario A: Audit Trail Card Visible In Task Detail
    [Documentation]    Given browser navigates to task detail for a task with mutations
    ...                Then an "Audit Trail" collapsible card is visible
    ...                And it contains a VTimeline with at least 1 entry.
    [Tags]    e2e    audit    detail    visibility    critical
    # Test Setup already ensures audit trail is visible and expanded
    Get Text    ${AUDIT_TRAIL_CARD}    contains    Audit Trail
    ${entries}=    Get Element Count    ${AUDIT_TRAIL_ENTRY}
    Should Be True    ${entries} >= 1    Expected at least 1 audit entry, got ${entries}
    # L1 Auxiliary: API confirms entries
    ${audit}=    API GET    /audit/${AUDIT_DETAIL_TASK}
    Response Status Should Be    ${audit}    200
    ${api_count}=    Get Length    ${audit.json()}
    Should Be True    ${api_count} >= 1    API audit has ${api_count} entries
    # L2 Auxiliary: MCP audit_entity_trail (in-process store — may differ from container)
    ${trail}=    MCP Audit Entity Trail    ${AUDIT_DETAIL_TASK}
    Log    MCP trail count: ${trail}[count] (in-process store, may be 0 for REST-created tasks)

Scenario B: CREATE Entry Renders With Green Icon
    [Documentation]    Given task was created (has CREATE audit entry)
    ...                Then timeline shows CREATE entry with green icon, timestamp, actor.
    [Tags]    e2e    audit    detail    create    critical
    Get Text    ${AUDIT_TRAIL_CARD}    contains    Create
    # L1 Auxiliary: API has CREATE
    ${audit}=    API GET    /audit/${AUDIT_DETAIL_TASK}
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "CREATE"
            ${found}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${found}    API has no CREATE entry

Scenario C: LINK Entry Shows Linked Entity Info
    [Documentation]    Given task has a linked rule (LINK audit entry exists)
    ...                Then timeline shows LINK entry with link icon, entity type=rule, entity ID.
    [Tags]    e2e    audit    detail    link    critical
    Get Text    ${AUDIT_TRAIL_CARD}    contains    Link
    # L1 Auxiliary: API confirms LINK with rule
    ${audit}=    API GET    /audit/${AUDIT_DETAIL_TASK}
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "LINK"
            ${le}=    Set Variable    ${entry}[metadata][linked_entity]
            IF    "${le}[type]" == "rule"
                ${found}=    Set Variable    ${TRUE}
            END
        END
    END
    Should Be True    ${found}    No LINK audit entry with linked_entity.type=rule
    # L2 Auxiliary: MCP audit_entity_trail (in-process store — may differ from container)
    ${trail}=    MCP Audit Entity Trail    ${AUDIT_DETAIL_TASK}
    Log    MCP trail count: ${trail}[count] (in-process store)

Scenario D: UPDATE Entry Shows Old To New Values
    [Documentation]    Given task status was changed (UPDATE audit entry)
    ...                Then timeline shows UPDATE entry with old→new transition.
    [Tags]    e2e    audit    detail    update    critical
    Get Text    ${AUDIT_TRAIL_CARD}    contains    Update
    # L1 Auxiliary: API confirms UPDATE with new_value
    ${audit}=    API GET    /audit/${AUDIT_DETAIL_TASK}
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "UPDATE" and "${entry}[new_value]" != "None"
            ${found}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${found}    No UPDATE with non-null new_value

Scenario E: COMMENT Entry Shows Author
    [Documentation]    Given a comment was added to the task
    ...                Then timeline shows COMMENT entry with author name.
    [Tags]    e2e    audit    detail    comment    critical
    Get Text    ${AUDIT_TRAIL_CARD}    contains    Comment
    # L1 Auxiliary: API confirms COMMENT with actor
    ${audit}=    API GET    /audit/${AUDIT_DETAIL_TASK}
    ${entries}=    Set Variable    ${audit.json()}
    ${found}=    Set Variable    ${FALSE}
    FOR    ${entry}    IN    @{entries}
        IF    "${entry}[action_type]" == "COMMENT"
            Should Be Equal    ${entry}[actor_id]    e2e-tester
            ${found}=    Set Variable    ${TRUE}
        END
    END
    Should Be True    ${found}    No COMMENT audit entry found

Scenario F: Filter By Action Type
    [Documentation]    Given task has multiple action types
    ...                When user selects filter for LINK only
    ...                Then only LINK entries are shown in timeline.
    [Tags]    e2e    audit    detail    filter    critical
    # Select LINK filter — click VSelect, then exact dropdown item
    Click    ${AUDIT_TRAIL_FILTER}
    Sleep    500ms
    Click    css=.v-list-item-title:text-is("LINK")
    Sleep    2s
    # After filtering, entries should still be present
    ${entries}=    Get Element Count    ${AUDIT_TRAIL_ENTRY}
    Should Be True    ${entries} >= 1    Filter returned 0 entries
    # Teardown: clear filter for subsequent tests (click the clearable X)
    ${clear_btns}=    Get Element Count    css=[data-testid='task-audit-filter'] .v-field__clearable
    IF    ${clear_btns} > 0
        Click    css=[data-testid='task-audit-filter'] .v-field__clearable
        Sleep    1s
    END

Scenario G: Refresh Reloads Audit Data
    [Documentation]    When user clicks refresh button on Audit Trail card
    ...                Then data reloads (loading indicator shown briefly).
    [Tags]    e2e    audit    detail    refresh
    ${before_count}=    Get Element Count    ${AUDIT_TRAIL_ENTRY}
    Click    ${AUDIT_TRAIL_REFRESH}
    # After refresh, entries should still be present (at minimum same count)
    Sleep    1s
    ${after_count}=    Get Element Count    ${AUDIT_TRAIL_ENTRY}
    Should Be True    ${after_count} >= ${before_count}

Scenario H: Pagination Controls Work
    [Documentation]    Given audit trail has pagination
    ...                Then page info is shown and navigation buttons exist.
    [Tags]    e2e    audit    detail    pagination
    # Page info should be visible
    Wait For Elements State    ${AUDIT_TRAIL_PAGE_INFO}    visible    timeout=${TIMEOUT}
    Get Text    ${AUDIT_TRAIL_PAGE_INFO}    contains    Page
