*** Settings ***
Documentation    RF-004: Unit Tests - UI Navigation Context
...              Migrated from tests/unit/test_ui_nav_context.py
...              Per UI-NAV-01-v1: Entity Navigation Context
Library          Collections
Library          ../../libs/UINavContextLibrary.py

*** Test Cases ***
# =============================================================================
# Navigation Context State Tests
# =============================================================================

Nav Source View In Initial State
    [Documentation]    GIVEN initial state WHEN checking nav_source_view THEN key exists and is None
    [Tags]    unit    ui    validate    navigation
    ${exists}=    State Contains Key    nav_source_view
    Should Be True    ${exists}
    ${is_none}=    State Key Value Is None    nav_source_view
    Should Be True    ${is_none}

Nav Source Id In Initial State
    [Documentation]    GIVEN initial state WHEN checking nav_source_id THEN key exists and is None
    [Tags]    unit    ui    validate    navigation
    ${exists}=    State Contains Key    nav_source_id
    Should Be True    ${exists}
    ${is_none}=    State Key Value Is None    nav_source_id
    Should Be True    ${is_none}

Nav Source Label In Initial State
    [Documentation]    GIVEN initial state WHEN checking nav_source_label THEN key exists and is None
    [Tags]    unit    ui    validate    navigation
    ${exists}=    State Contains Key    nav_source_label
    Should Be True    ${exists}
    ${is_none}=    State Key Value Is None    nav_source_label
    Should Be True    ${is_none}

# =============================================================================
# Navigation Triggers Tests
# =============================================================================

Navigate To Task Trigger Registered
    [Documentation]    GIVEN task controllers WHEN registering THEN navigate_to_task trigger exists
    [Tags]    unit    ui    validate    navigation
    ${registered}=    Trigger Is Registered    navigate_to_task
    Should Be True    ${registered}

Navigate Back To Source Trigger Registered
    [Documentation]    GIVEN task controllers WHEN registering THEN navigate_back_to_source trigger exists
    [Tags]    unit    ui    validate    navigation
    ${registered}=    Trigger Is Registered    navigate_back_to_source
    Should Be True    ${registered}

# =============================================================================
# Session Tasks View Tests
# =============================================================================

Session Tasks Click Has Sessions Source
    [Documentation]    GIVEN session tasks view WHEN clicking task THEN passes 'sessions' as source_view
    [Tags]    unit    ui    validate    navigation
    ${has_source}=    Tasks View Has Sessions Source
    Should Be True    ${has_source}

Session Tasks Click Has Session Id Source
    [Documentation]    GIVEN session tasks view WHEN clicking task THEN passes session_id as source_id
    [Tags]    unit    ui    validate    navigation
    ${has_id}=    Tasks View Has Session Id Source
    Should Be True    ${has_id}

# =============================================================================
# Task Detail View Tests
# =============================================================================

Task Detail Has Back To Source Button
    [Documentation]    GIVEN task detail view WHEN rendered THEN has back-to-source button testid
    [Tags]    unit    ui    validate    navigation
    ${has_button}=    Task Detail Has Back To Source Button
    Should Be True    ${has_button}

Task Detail Triggers Back To Source
    [Documentation]    GIVEN task detail view WHEN back button clicked THEN triggers navigate_back_to_source
    [Tags]    unit    ui    validate    navigation
    ${has_trigger}=    Task Detail Has Back To Source Trigger
    Should Be True    ${has_trigger}

Task Detail Has Nav Source Conditionals
    [Documentation]    GIVEN task detail view WHEN rendered THEN has both nav_source_view conditionals
    [Tags]    unit    ui    validate    navigation
    ${has_both}=    Task Detail Has Nav Source Conditionals
    Should Be True    ${has_both}

# =============================================================================
# Rules View Navigation Tests
# =============================================================================

Rules View Has Rules Source
    [Documentation]    GIVEN rules view WHEN clicking implementing task THEN passes 'rules' as source_view
    [Tags]    unit    ui    validate    navigation
    ${has_source}=    Rules View Has Rules Source
    Should Be True    ${has_source}

Rules View Has Rule Id Source
    [Documentation]    GIVEN rules view WHEN clicking implementing task THEN passes rule_id as source_id
    [Tags]    unit    ui    validate    navigation
    ${has_id}=    Rules View Has Rule Id Source
    Should Be True    ${has_id}

