*** Settings ***
Documentation    RF-004: Unit Tests - UI Helpers
...              Migrated from tests/unit/ui/test_ui_helpers.py
...              Per DOC-SIZE-01-v1: UI helper function tests
Library          Collections
Library          ../../libs/UIHelpersLibrary.py

*** Test Cases ***
# =============================================================================
# Color Mapping Tests
# =============================================================================

Get Status Color
    [Documentation]    GIVEN status WHEN get_status_color THEN correct color
    [Tags]    unit    ui    validate    helpers    colors
    ${result}=    Get Status Color
    Should Be Equal    ${result}[active]    success
    Should Be Equal    ${result}[draft]    grey
    Should Be Equal    ${result}[deprecated]    warning
    Should Be Equal    ${result}[unknown]    grey

Get Priority Color
    [Documentation]    GIVEN priority WHEN get_priority_color THEN correct color
    [Tags]    unit    ui    validate    helpers    colors
    ${result}=    Get Priority Color
    Should Be Equal    ${result}[critical]    error
    Should Be Equal    ${result}[high]    warning
    Should Be Equal    ${result}[medium]    grey
    Should Be Equal    ${result}[low]    grey-lighten-1

# =============================================================================
# Icon Mapping Tests
# =============================================================================

Get Category Icon
    [Documentation]    GIVEN category WHEN get_category_icon THEN mdi icon
    [Tags]    unit    ui    validate    helpers    icons
    ${result}=    Get Category Icon
    Should Contain    ${result}[governance]    mdi-
    Should Contain    ${result}[technical]    mdi-
    Should Contain    ${result}[unknown]    mdi-

# =============================================================================
# Formatting Tests
# =============================================================================

Format Rule Card
    [Documentation]    GIVEN rule WHEN format_rule_card THEN card has required fields
    [Tags]    unit    ui    validate    helpers    format
    ${result}=    Format Rule Card
    Should Be True    ${result}[has_title]
    Should Be True    ${result}[has_subtitle]
    Should Be True    ${result}[has_color]
    Should Be True    ${result}[has_icon]

