*** Settings ***
Documentation    RF-004: Unit Tests - UI Factory Functions
...              Migrated from tests/unit/ui/test_ui_factory.py
...              Per DOC-SIZE-01-v1: Split from test_governance_ui.py
Library          Collections
Library          ../../libs/UIFactoryLibrary.py

*** Test Cases ***
# =============================================================================
# Factory Function Tests
# =============================================================================

Create Governance Dashboard Works
    [Documentation]    GIVEN factory WHEN calling THEN creates dashboard
    [Tags]    unit    ui    validate    factory
    ${result}=    Create Governance Dashboard Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Factory not available
    Should Be True    ${result}[created]

Factory With Custom Port
    [Documentation]    GIVEN factory WHEN port=9090 THEN dashboard has correct port
    [Tags]    unit    ui    validate    factory
    ${result}=    Factory With Custom Port
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Factory not available
    Should Be True    ${result}[created]
    Should Be True    ${result}[port_correct]

Default Port Is 8081
    [Documentation]    GIVEN factory WHEN no port THEN default is 8081
    [Tags]    unit    ui    validate    factory
    ${result}=    Default Port Is 8081
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Factory not available
    Should Be True    ${result}[created]
    Should Be True    ${result}[port_is_8081]

