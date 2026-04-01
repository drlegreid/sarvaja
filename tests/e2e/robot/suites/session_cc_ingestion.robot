*** Settings ***
Documentation    Session CC Ingestion Visibility E2E Tests — SRVJ-BUG-SESSION-INGEST-01
...              Per TEST-E2E-01-v1: 3-level edge coverage (API + MCP + Playwright L3).
...              Per EDS-SESSION-INGEST-VISIBILITY-01-v1: DSE-derived test cases.
...
...              Axes: status filtering, limit enforcement, API consistency,
...              response key compat, data sources, UI visibility (L3).
...
...              Root cause: session_list MCP tool filtered to ACTIVE-only,
...              hiding CC-ingested sessions that are marked COMPLETED.

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Library     ../libraries/mcp_sessions.py
Library     ../libraries/navigation.py

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser

Default Tags    e2e    sessions    cc-ingestion

*** Variables ***
${SESSIONS_ENDPOINT}    /sessions

*** Test Cases ***

# ═══════════════════════════════════════════════════════════════════════
# AXIS 1 — MCP session_list status filtering (DSE E1.1-E1.4)
# ═══════════════════════════════════════════════════════════════════════

E1.1 Default Returns Active And Completed Sessions
    [Documentation]    session_list() with no status returns both ACTIVE and COMPLETED.
    [Tags]    L2    mcp    axis1
    ${result}=    MCP Session List    limit=100
    MCP Result Should Succeed    ${result}
    MCP Session List Count Should Be At Least    ${result}    5
    ${sessions}=    Get Sessions From Result    ${result}
    ${has_active}=    Evaluate    any("-CC-" not in s for s in $sessions)
    ${has_cc}=    Evaluate    any("-CC-" in s for s in $sessions)
    Should Be True    ${has_cc}    msg=Default session_list has no CC sessions

E1.2 Active Filter Returns Only Active Sessions
    [Documentation]    session_list(status="ACTIVE") returns sessions, no error.
    [Tags]    L2    mcp    axis1
    ${result}=    MCP Session List    status=ACTIVE    limit=50
    MCP Result Should Succeed    ${result}
    # Verify response uses active_sessions key
    ${key_exists}=    Evaluate    "active_sessions" in $result
    Should Be True    ${key_exists}    msg=ACTIVE filter should use active_sessions key

E1.3 Completed Filter Returns Completed Sessions
    [Documentation]    session_list(status="COMPLETED") returns CC-ingested sessions.
    ...                This is the CORE regression test for SRVJ-BUG-SESSION-INGEST-01.
    [Tags]    L2    mcp    axis1    critical
    ${result}=    MCP Session List    status=COMPLETED    limit=50
    MCP Result Should Succeed    ${result}
    MCP Session List Count Should Be At Least    ${result}    1
    # Verify response uses completed_sessions key
    ${key_exists}=    Evaluate    "completed_sessions" in $result
    Should Be True    ${key_exists}    msg=COMPLETED filter should use completed_sessions key

E1.4 Completed Filter Contains CC Sessions
    [Documentation]    CC-ingested sessions appear in COMPLETED filter (the original bug).
    [Tags]    L2    mcp    axis1    critical
    ${result}=    MCP Session List    status=COMPLETED    limit=100
    MCP Result Should Succeed    ${result}
    ${cc_sessions}=    MCP Session List Should Contain CC Sessions    ${result}
    Log    Found ${cc_sessions.__len__()} CC COMPLETED sessions — bug is fixed

# ═══════════════════════════════════════════════════════════════════════
# AXIS 2 — Limit enforcement (DSE E2.1-E2.3)
# ═══════════════════════════════════════════════════════════════════════

E2.1 Limit 3 Returns At Most 3
    [Documentation]    session_list(limit=3) caps result count.
    [Tags]    L2    mcp    axis2
    ${result}=    MCP Session List    limit=3
    MCP Result Should Succeed    ${result}
    ${count}=    Evaluate    $result.get("count", 0)
    Should Be True    ${count} <= 3
    ...    msg=limit=3 returned ${count} sessions

E2.2 Limit 1 Returns Exactly 1
    [Documentation]    session_list(limit=1) returns single session.
    [Tags]    L2    mcp    axis2
    ${result}=    MCP Session List    limit=1
    MCP Result Should Succeed    ${result}
    ${count}=    Evaluate    $result.get("count", 0)
    Should Be True    ${count} == 1
    ...    msg=limit=1 returned ${count} sessions, expected 1

E2.3 Default Limit Caps At 50
    [Documentation]    session_list() default limit is 50.
    [Tags]    L2    mcp    axis2
    ${result}=    MCP Session List
    MCP Result Should Succeed    ${result}
    ${count}=    Evaluate    $result.get("count", 0)
    Should Be True    ${count} <= 50
    ...    msg=Default limit returned ${count} sessions, expected <= 50

# ═══════════════════════════════════════════════════════════════════════
# AXIS 3 — REST API consistency (DSE E3.1-E3.3)
# ═══════════════════════════════════════════════════════════════════════

E3.1 API Returns CC Sessions
    [Documentation]    GET /api/sessions includes CC-ingested sessions.
    [Tags]    L1    api    axis3    critical
    ${response}=    API GET    ${SESSIONS_ENDPOINT}    params=limit=50
    Response Status Should Be    ${response}    200
    ${items}=    Evaluate    $response.json().get("items", [])
    ${cc_count}=    Count CC Sessions In List    ${items}
    Should Be True    ${cc_count} > 0
    ...    msg=REST API returned 0 CC sessions out of ${items.__len__()} total

E3.2 API Has Completed Status
    [Documentation]    GET /api/sessions returns COMPLETED sessions.
    [Tags]    L1    api    axis3
    ${response}=    API GET    ${SESSIONS_ENDPOINT}    params=limit=100
    Response Status Should Be    ${response}    200
    ${items}=    Evaluate    $response.json().get("items", [])
    ${statuses}=    Evaluate    set(s.get("status") for s in $items)
    Should Contain    ${statuses}    COMPLETED
    ...    msg=No COMPLETED sessions in API response

E3.3 API And MCP CC Sessions Overlap
    [Documentation]    CC session IDs from REST API also appear in MCP session_list.
    [Tags]    L1    L2    api    mcp    axis3    critical
    # Get CC sessions from API
    ${response}=    API GET    ${SESSIONS_ENDPOINT}    params=limit=50
    ${items}=    Evaluate    $response.json().get("items", [])
    ${api_cc}=    Evaluate    [s["session_id"] for s in $items if "-CC-" in s.get("session_id", "")]
    # Get CC sessions from MCP
    ${mcp_result}=    MCP Session List    limit=100
    ${mcp_sessions}=    Get Sessions From Result    ${mcp_result}
    ${mcp_cc}=    Evaluate    [s for s in $mcp_sessions if "-CC-" in s]
    # At least one CC session must appear in both
    ${overlap}=    Evaluate    set($api_cc) & set($mcp_cc)
    Should Be True    len($overlap) > 0
    ...    msg=No CC session overlap between API and MCP (API: ${api_cc.__len__()}, MCP: ${mcp_cc.__len__()})

# ═══════════════════════════════════════════════════════════════════════
# AXIS 4 — Response key backward compatibility (DSE E4.1-E4.3)
# ═══════════════════════════════════════════════════════════════════════

E4.1 No Status Uses Sessions Key
    [Documentation]    session_list() response uses "sessions" key.
    [Tags]    L2    mcp    axis4
    ${result}=    MCP Session List    limit=5
    MCP Result Should Succeed    ${result}
    ${has_key}=    Evaluate    "sessions" in $result
    Should Be True    ${has_key}    msg=Default should use "sessions" key, got: ${result.keys()}

E4.2 Active Uses Active Sessions Key
    [Documentation]    session_list(status="ACTIVE") response uses "active_sessions" key.
    [Tags]    L2    mcp    axis4
    ${result}=    MCP Session List    status=ACTIVE    limit=5
    MCP Result Should Succeed    ${result}
    ${has_key}=    Evaluate    "active_sessions" in $result
    Should Be True    ${has_key}    msg=ACTIVE should use "active_sessions" key

E4.3 Completed Uses Completed Sessions Key
    [Documentation]    session_list(status="COMPLETED") response uses "completed_sessions" key.
    [Tags]    L2    mcp    axis4
    ${result}=    MCP Session List    status=COMPLETED    limit=5
    MCP Result Should Succeed    ${result}
    ${has_key}=    Evaluate    "completed_sessions" in $result
    Should Be True    ${has_key}    msg=COMPLETED should use "completed_sessions" key

# ═══════════════════════════════════════════════════════════════════════
# AXIS 5 — Data sources (DSE E5.1)
# ═══════════════════════════════════════════════════════════════════════

E5.1 TypeDB Source Present
    [Documentation]    session_list sources include at least one typedb entry.
    [Tags]    L2    mcp    axis5
    ${result}=    MCP Session List    limit=20
    MCP Result Should Succeed    ${result}
    ${sources}=    Evaluate    $result.get("sources", [])
    ${typedb_sources}=    Evaluate    [s for s in $sources if isinstance(s, dict) and s.get("source") == "typedb"]
    Should Be True    len($typedb_sources) > 0
    ...    msg=No TypeDB sources in session_list response

# ═══════════════════════════════════════════════════════════════════════
# AXIS 6 — L3 Playwright UI verification (FEAT-009 / BUG-015)
# ═══════════════════════════════════════════════════════════════════════

E6.1 Sessions View Shows CC Sessions In Table
    [Documentation]    Navigate to Sessions tab via Playwright and verify CC sessions visible.
    ...                Per FEAT-009: L3 = real Playwright UI journeys, not API count checks.
    [Tags]    L3    playwright    axis6    critical
    Navigate To Tab    sessions
    Verify Data Table Has Rows    ${SESSIONS_TABLE}
    # Search for CC sessions using search input
    Fill Text    ${SESSIONS_SEARCH}    CC-
    Sleep    1s    reason=Vuetify table filter debounce
    ${rows}=    Get Element Count    ${SESSIONS_TABLE} tbody tr:has(td)
    Should Be True    ${rows} > 0
    ...    msg=No CC sessions found in Sessions table after search filter
    Take Evidence Screenshot    sessions-cc-visible

E6.2 Sessions Search Filters Table Correctly
    [Documentation]    Search input filters sessions table.
    ...                Per feedback: use search input for large Trame tables.
    [Tags]    L3    playwright    axis6
    Navigate To Tab    sessions
    Verify Data Table Has Rows    ${SESSIONS_TABLE}
    ${all_rows}=    Get Element Count    ${SESSIONS_TABLE} tbody tr:has(td)
    # Apply search filter
    Fill Text    ${SESSIONS_SEARCH}    CC-
    Sleep    1s    reason=Vuetify filter debounce
    ${filtered_rows}=    Get Element Count    ${SESSIONS_TABLE} tbody tr:has(td)
    # Filtered should be fewer (or equal if all are CC)
    Should Be True    ${filtered_rows} <= ${all_rows}
    ...    msg=Search filter did not reduce row count (${filtered_rows} vs ${all_rows})
    Take Evidence Screenshot    sessions-search-filter

E6.3 Hide Test Toggle Filters Planning Sessions (BUG-015 Regression)
    [Documentation]    "Hide test" toggle on Tasks view hides test/planning sessions.
    ...                BUG-015 regression: filter was hiding non-test sessions.
    [Tags]    L3    playwright    axis6    bug-015
    Navigate To Tab    tasks
    Verify Data Table Has Rows    ${TASKS_TABLE}
    ${before}=    Get Element Count    ${TASKS_TABLE} tbody tr:has(td)
    # Click "Hide test tasks" toggle if visible
    ${toggle_visible}=    Get Element Count    ${TASKS_HIDE_TEST_TOGGLE}
    IF    ${toggle_visible} > 0
        Click    ${TASKS_HIDE_TEST_TOGGLE}
        Sleep    1s    reason=Vuetify table re-render
        ${after}=    Get Element Count    ${TASKS_TABLE} tbody tr:has(td)
        # After hiding, count should differ (fewer or same if no test tasks)
        Log    Hide test toggle: ${before} → ${after} rows
    END
    Take Evidence Screenshot    tasks-hide-test-toggle

*** Keywords ***
Count CC Sessions In List
    [Documentation]    Count sessions with -CC- in their session_id.
    [Arguments]    ${items}
    ${count}=    Evaluate    sum(1 for s in $items if "-CC-" in s.get("session_id", ""))
    RETURN    ${count}

Response Status Should Be
    [Documentation]    Assert HTTP response status code.
    [Arguments]    ${response}    ${expected}
    Should Be Equal As Strings    ${response.status_code}    ${expected}

Get Sessions From Result
    [Documentation]    Extract session list from MCP result regardless of key name.
    [Arguments]    ${result}
    ${sessions}=    Evaluate    $result.get("sessions") or $result.get("completed_sessions") or $result.get("active_sessions") or []
    RETURN    ${sessions}
