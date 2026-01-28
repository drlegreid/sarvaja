*** Settings ***
Documentation    RF-004: Unit Tests - Trame UI Module
...              Migrated from tests/test_trame_ui.py
...              Per Phase 6: Use Trame for Python-native web UI
Library          Collections
Library          ../../libs/TrameUiLibrary.py
Force Tags        unit    ui    trame    low    validate    UI-TRAME-01-v1

*** Test Cases ***
# =============================================================================
# Import Tests
# =============================================================================

Trame UI Module Importable
    [Documentation]    Trame UI module can be imported
    [Tags]    unit    trame    ui    import
    ${result}=    Trame Ui Importable
    Skip If    not ${result}[importable]    Trame not installed: ${result}[error]
    Should Be True    ${result}[class_exists]    SimAITrameUI should exist

Create Trame App Factory Importable
    [Documentation]    Factory function can be imported
    [Tags]    unit    trame    ui    factory
    ${result}=    Create Trame App Importable
    Skip If    not ${result}[importable]    Trame not installed: ${result}[error]
    Should Be True    ${result}[exists]    create_trame_app should exist
    Should Be True    ${result}[callable]    create_trame_app should be callable

# =============================================================================
# Factory Function Tests
# =============================================================================

Factory Creates App With Default Agents
    [Documentation]    Factory creates app with default agents
    [Tags]    unit    trame    ui    factory    agents
    ${result}=    Create App With Default Agents
    Skip If    '${result.get("skip", False)}' == 'True'    ${result}[reason]
    Should Be True    ${result}[created]    App should be created
    Should Be True    ${result}[has_agents]    App should have agents

Factory Creates App With Custom Agents
    [Documentation]    Factory creates app with custom agents
    [Tags]    unit    trame    ui    factory    custom
    ${result}=    Create App With Custom Agents
    Skip If    '${result.get("skip", False)}' == 'True'    ${result}[reason]
    Should Be True    ${result}[created]    App should be created
    Should Be True    ${result}[agents_match]    Custom agents should match

Factory Accepts Custom API Base URL
    [Documentation]    Factory accepts custom API base URL
    [Tags]    unit    trame    ui    factory    api
    ${result}=    Create App With Custom Api Base
    Skip If    '${result.get("skip", False)}' == 'True'    ${result}[reason]
    Should Be True    ${result}[created]    App should be created
    Should Be True    ${result}[api_base_match]    API base should match

# =============================================================================
# UI Class Tests
# =============================================================================

UI Class Init Stores Agents
    [Documentation]    Initialization stores agents dict
    [Tags]    unit    trame    ui    class    init
    ${result}=    Test Ui Class Init Agents
    Skip If    '${result.get("skip", False)}' == 'True'    ${result}[reason]
    Should Be True    ${result}[created]    UI should be created
    Should Be True    ${result}[agents_stored]    Agents should be stored

UI Class Init Stores API Base
    [Documentation]    Initialization stores API base URL
    [Tags]    unit    trame    ui    class    init
    ${result}=    Test Ui Class Init Api Base
    Skip If    '${result.get("skip", False)}' == 'True'    ${result}[reason]
    Should Be True    ${result}[created]    UI should be created
    Should Be True    ${result}[api_base_stored]    API base should be stored

# =============================================================================
# Import Verification Summary
# =============================================================================

Verify All Trame Imports
    [Documentation]    Verify all Trame imports work
    [Tags]    unit    trame    ui    imports    summary
    ${result}=    Verify Trame Imports
    Log    UI Class Import: ${result}[ui_class]
    Log    Factory Import: ${result}[factory]
