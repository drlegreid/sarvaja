*** Settings ***
Documentation    RF-004: Unit Tests - UI State Management
...              Migrated from tests/unit/ui/test_ui_state.py
...              Per DOC-SIZE-01-v1: State management tests
Library          Collections
Library          ../../libs/UIStateLibrary.py
Force Tags        unit    ui    state    low    validate    UI-RESP-01-v1

*** Test Cases ***
# =============================================================================
# State Factory Tests
# =============================================================================

Get Initial State Factory
    [Documentation]    GIVEN get_initial_state WHEN called twice THEN fresh objects
    [Tags]    unit    ui    validate    state
    ${result}=    Get Initial State Factory
    Should Be True    ${result}[different_objects]
    Should Be True    ${result}[state2_unchanged]

Initial State Has Required Keys
    [Documentation]    GIVEN initial state WHEN checking THEN all required keys present
    [Tags]    unit    ui    validate    state
    ${result}=    Initial State Has Required Keys
    Should Be True    ${result}[has_active_view]
    Should Be True    ${result}[has_rules]
    Should Be True    ${result}[has_decisions]
    Should Be True    ${result}[has_sessions]
    Should Be True    ${result}[has_selected_rule]
    Should Be True    ${result}[has_search_query]

# =============================================================================
# State Transform Tests
# =============================================================================

With Loading Transform
    [Documentation]    GIVEN state WHEN with_loading THEN new state with loading flag
    [Tags]    unit    ui    validate    state    transform
    ${result}=    With Loading Transform
    Should Be True    ${result}[different_objects]
    Should Be True    ${result}[new_loading_true]
    Should Be True    ${result}[old_loading_false]

With Error Transform
    [Documentation]    GIVEN state WHEN with_error THEN new state with error
    [Tags]    unit    ui    validate    state    transform
    ${result}=    With Error Transform
    Should Be True    ${result}[has_error]
    Should Be Equal    ${result}[error_message]    Test error

Clear Error Transform
    [Documentation]    GIVEN state with error WHEN clear_error THEN error cleared
    [Tags]    unit    ui    validate    state    transform
    ${result}=    Clear Error Transform
    Should Be Equal    ${result}[has_error]    ${False}
    Should Be True    ${result}[error_message_empty]

