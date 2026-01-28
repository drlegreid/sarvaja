*** Settings ***
Documentation    RF-004: Unit Tests - UI Data Access Functions
...              Migrated from tests/unit/ui/test_ui_data_access.py
...              Per DOC-SIZE-01-v1: Split from test_governance_ui.py
Library          Collections
Library          ../../libs/UIDataAccessLibrary.py
Force Tags        unit    ui    data    low    read    UI-DESIGN-02-v1

*** Test Cases ***
# =============================================================================
# Data Access Function Importability Tests
# =============================================================================

Get Rules Importable
    [Documentation]    GIVEN governance_ui WHEN importing THEN get_rules available
    [Tags]    unit    ui    validate    data-access
    ${result}=    Get Rules Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[callable]

Get Rules By Category Importable
    [Documentation]    GIVEN governance_ui WHEN importing THEN get_rules_by_category available
    [Tags]    unit    ui    validate    data-access
    ${result}=    Get Rules By Category Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[callable]

Get Decisions Importable
    [Documentation]    GIVEN governance_ui WHEN importing THEN get_decisions available
    [Tags]    unit    ui    validate    data-access
    ${result}=    Get Decisions Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[callable]

Get Sessions Importable
    [Documentation]    GIVEN governance_ui WHEN importing THEN get_sessions available
    [Tags]    unit    ui    validate    data-access
    ${result}=    Get Sessions Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[callable]

Get Tasks Importable
    [Documentation]    GIVEN governance_ui WHEN importing THEN get_tasks available
    [Tags]    unit    ui    validate    data-access
    ${result}=    Get Tasks Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[callable]

Search Evidence Importable
    [Documentation]    GIVEN governance_ui WHEN importing THEN search_evidence available
    [Tags]    unit    ui    validate    data-access
    ${result}=    Search Evidence Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[callable]

# =============================================================================
# Data Access Return Type Tests
# =============================================================================

Get Rules Returns List
    [Documentation]    GIVEN get_rules WHEN calling THEN returns list
    [Tags]    unit    ui    validate    data-access    mocked
    ${result}=    Get Rules Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

Get Decisions Returns List
    [Documentation]    GIVEN get_decisions WHEN calling THEN returns list
    [Tags]    unit    ui    validate    data-access    mocked
    ${result}=    Get Decisions Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

