*** Settings ***
Documentation    RF-004: Unit Tests - Executive Dropdown
...              Migrated from tests/unit/test_executive_dropdown.py
...              Per UI-AUDIT-007: Executive Report dropdown fix
Library          Collections
Library          ../../libs/ExecutiveDropdownLibrary.py
Force Tags        unit    ui    executive    low    session    read    UI-NAV-01-v1

*** Test Cases ***
# =============================================================================
# Sessions List Loader Tests
# =============================================================================

Load Sessions List In Loaders
    [Documentation]    GIVEN data_loaders WHEN checking THEN load_sessions_list defined
    [Tags]    unit    ui    validate    executive    loaders
    ${result}=    Load Sessions List In Loaders
    Should Be True    ${result}[has_function]
    Should Be True    ${result}[in_return_dict]

Sessions List Trigger Exists
    [Documentation]    GIVEN data_loaders WHEN checking THEN trigger registered
    [Tags]    unit    ui    validate    executive    loaders
    ${result}=    Sessions List Trigger Exists
    Should Be True    ${result}[trigger_registered]

Governance Dashboard Calls Sessions Loader
    [Documentation]    GIVEN governance_dashboard WHEN checking THEN calls loader
    [Tags]    unit    ui    validate    executive    dashboard
    ${result}=    Governance Dashboard Calls Sessions Loader
    Should Be True    ${result}[calls_loader]
    Should Be True    ${result}[assigns_loader]

# =============================================================================
# Sessions API Integration Tests
# =============================================================================

Sessions API Returns List
    [Documentation]    GIVEN sessions API WHEN calling THEN returns list
    [Tags]    unit    ui    validate    executive    api    integration
    ${result}=    Sessions Api Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    API not available
    Should Be True    ${result}[is_list]

Sessions Have Session Id
    [Documentation]    GIVEN sessions API WHEN calling THEN sessions have session_id
    [Tags]    unit    ui    validate    executive    api    integration
    ${result}=    Sessions Have Session Id
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    API not available
    Should Be True    ${result}[all_have_session_id]

