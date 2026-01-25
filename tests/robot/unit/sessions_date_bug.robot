*** Settings ***
Documentation    RF-004: Unit Tests - Sessions Date Display Bug
...              Migrated from tests/test_sessions_date_bug.py
...              Per GAP-UI-EXP-005: Sessions view date display fix
Library          Collections
Library          ../../libs/SessionsDateBugLibrary.py

*** Test Cases ***
# =============================================================================
# Sessions Date Display Tests - GAP-UI-EXP-005
# =============================================================================

Sessions List Uses Start Time Field
    [Documentation]    GIVEN sessions/list.py WHEN check THEN uses start_time
    [Tags]    unit    sessions    date    bug
    ${result}=    Sessions List Uses Start Time Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    File not found
    Should Be True    ${result}[no_session_date]
    Should Be True    ${result}[has_start_time]

Sessions Content Uses Start Time Field
    [Documentation]    GIVEN sessions/content.py WHEN check THEN uses start_time
    [Tags]    unit    sessions    date    bug
    ${result}=    Sessions Content Uses Start Time Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    File not found
    Should Be True    ${result}[no_selected_session_date]
    Should Be True    ${result}[has_start_time]

API Returns Start Time Not Date
    [Documentation]    GIVEN API contract WHEN verify THEN has start_time
    [Tags]    unit    sessions    api    contract
    ${result}=    API Returns Start Time Not Date
    Should Be True    ${result}[no_date_field]
    Should Be True    ${result}[has_start_time]
