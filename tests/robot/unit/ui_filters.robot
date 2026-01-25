*** Settings ***
Documentation    RF-004: Unit Tests - UI Filter Functions
...              Migrated from tests/unit/ui/test_ui_filters.py
...              Per DOC-SIZE-01-v1: Split from test_governance_ui.py
Library          Collections
Library          ../../libs/UIFiltersLibrary.py

*** Test Cases ***
# =============================================================================
# Rule Filter Function Tests
# =============================================================================

Filter Rules By Status Works
    [Documentation]    GIVEN rules WHEN filter_rules_by_status THEN filters by status
    [Tags]    unit    ui    validate    filters
    ${result}=    Filter Rules By Status Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_count]
    Should Be True    ${result}[all_active]

Filter Rules By Category Works
    [Documentation]    GIVEN rules WHEN filter_rules_by_category THEN filters by category
    [Tags]    unit    ui    validate    filters
    ${result}=    Filter Rules By Category Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_count]
    Should Be True    ${result}[all_governance]

Filter Rules By Search Works
    [Documentation]    GIVEN rules WHEN filter_rules_by_search THEN filters by query
    [Tags]    unit    ui    validate    filters
    ${result}=    Filter Rules By Search Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_count]
    Should Be True    ${result}[correct_match]

Sort Rules Works
    [Documentation]    GIVEN rules WHEN sort_rules THEN sorts by column
    [Tags]    unit    ui    validate    filters
    ${result}=    Sort Rules Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[asc_first_correct]
    Should Be True    ${result}[asc_last_correct]
    Should Be True    ${result}[desc_first_correct]

