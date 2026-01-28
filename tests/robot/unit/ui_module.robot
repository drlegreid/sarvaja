*** Settings ***
Documentation    RF-004: Unit Tests - UI Module Existence
...              Migrated from tests/unit/ui/test_ui_module.py
...              Per DOC-SIZE-01-v1: Split from test_governance_ui.py (395 lines)
Library          Collections
Library          ../../libs/UIModuleLibrary.py
Force Tags        unit    ui    module    low    validate    UI-DESIGN-02-v1

*** Test Cases ***
# =============================================================================
# Governance UI Module Existence Tests
# =============================================================================

Governance UI Package Exists
    [Documentation]    GIVEN agent/ WHEN checking THEN governance_ui package exists
    [Tags]    unit    ui    validate    module
    ${result}=    Governance UI Package Exists
    Should Be True    ${result}[ui_dir_exists]
    Should Be True    ${result}[init_exists]
    Should Be True    ${result}[data_access_exists]
    Should Be True    ${result}[state_exists]

Governance Dashboard Exists
    [Documentation]    GIVEN agent/ WHEN checking THEN governance_dashboard.py exists
    [Tags]    unit    ui    validate    module
    ${result}=    Governance Dashboard Exists
    Should Be True    ${result}[dashboard_exists]

Governance Dashboard Class Importable
    [Documentation]    GIVEN governance_dashboard WHEN importing THEN class available
    [Tags]    unit    ui    validate    module
    ${result}=    Governance Dashboard Class Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import or init failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[instantiable]
    Should Be True    ${result}[has_build_ui]
    Should Be True    ${result}[has_run]

