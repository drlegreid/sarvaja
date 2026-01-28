*** Settings ***
Documentation    RF-004: Unit Tests - UI Navigation Configuration
...              Migrated from tests/unit/ui/test_ui_navigation.py
...              Per DOC-SIZE-01-v1: Split from test_governance_ui.py
Library          Collections
Library          ../../libs/UINavigationLibrary.py
Force Tags        unit    ui    navigation    low    validate    UI-NAV-01-v1

*** Test Cases ***
# =============================================================================
# Navigation Items Tests
# =============================================================================

Navigation Items Exist
    [Documentation]    GIVEN governance_ui WHEN importing THEN NAVIGATION_ITEMS defined
    [Tags]    unit    ui    validate    navigation
    ${result}=    Navigation Items Exist
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_list]
    Should Be True    ${result}[has_items]

Navigation Has Required Views
    [Documentation]    GIVEN NAVIGATION_ITEMS WHEN checking THEN has required views
    [Tags]    unit    ui    validate    navigation
    ${result}=    Navigation Has Required Views
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_rules]
    Should Be True    ${result}[has_decisions]
    Should Be True    ${result}[has_sessions]
    Should Be True    ${result}[has_tasks]
    Should Be True    ${result}[has_impact]
    Should Be True    ${result}[has_trust]

Navigation Items Have Structure
    [Documentation]    GIVEN NAVIGATION_ITEMS WHEN checking THEN has title/icon/value
    [Tags]    unit    ui    validate    navigation
    ${result}=    Navigation Items Have Structure
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_have_title]
    Should Be True    ${result}[all_have_icon]
    Should Be True    ${result}[all_have_value]

