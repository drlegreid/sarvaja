*** Settings ***
Documentation    RF-004: Unit Tests - UI Constants
...              Migrated from tests/unit/ui/test_ui_constants.py
...              Per DOC-SIZE-01-v1: Constants export tests
Library          Collections
Library          ../../libs/UIConstantsLibrary.py
Force Tags        unit    ui    constants    low    validate    UI-NAV-01-v1

*** Test Cases ***
# =============================================================================
# Constants Export Tests
# =============================================================================

Status Colors Exported
    [Documentation]    GIVEN governance_ui WHEN importing STATUS_COLORS THEN dict
    [Tags]    unit    ui    validate    constants    export
    ${result}=    Status Colors Exported
    Should Be True    ${result}[is_dict]

Priority Colors Exported
    [Documentation]    GIVEN governance_ui WHEN importing PRIORITY_COLORS THEN dict
    [Tags]    unit    ui    validate    constants    export
    ${result}=    Priority Colors Exported
    Should Be True    ${result}[is_dict]

Category Icons Exported
    [Documentation]    GIVEN governance_ui WHEN importing CATEGORY_ICONS THEN dict
    [Tags]    unit    ui    validate    constants    export
    ${result}=    Category Icons Exported
    Should Be True    ${result}[is_dict]

Rule Categories Exported
    [Documentation]    GIVEN governance_ui WHEN importing RULE_CATEGORIES THEN list
    [Tags]    unit    ui    validate    constants    export
    ${result}=    Rule Categories Exported
    Should Be True    ${result}[is_list]

Rule Priorities Exported
    [Documentation]    GIVEN governance_ui WHEN importing RULE_PRIORITIES THEN list
    [Tags]    unit    ui    validate    constants    export
    ${result}=    Rule Priorities Exported
    Should Be True    ${result}[is_list]

Rule Statuses Exported
    [Documentation]    GIVEN governance_ui WHEN importing RULE_STATUSES THEN list
    [Tags]    unit    ui    validate    constants    export
    ${result}=    Rule Statuses Exported
    Should Be True    ${result}[is_list]

