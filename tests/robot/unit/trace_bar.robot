*** Settings ***
Documentation    RF-004: Unit Tests - Bottom Bar with Technical Traces
...              Migrated from tests/test_trace_bar.py
...              Per GAP-UI-048: Bottom bar with technical traces
Library          Collections
Library          ../../libs/TraceBarLibrary.py

*** Test Cases ***
# =============================================================================
# Trace Event Design Tests
# =============================================================================

Trace Event Has Type
    [Documentation]    GIVEN TraceType WHEN check THEN has api_call type
    [Tags]    unit    trace    event    type
    ${result}=    Trace Event Has Type
    Should Be True    ${result}[api_call]

Trace Event Has Timestamp
    [Documentation]    GIVEN TraceEvent WHEN create THEN has timestamp
    [Tags]    unit    trace    event    timestamp
    ${result}=    Trace Event Has Timestamp
    Should Be True    ${result}[has_timestamp]

Trace Event Has Message
    [Documentation]    GIVEN TraceEvent WHEN create THEN has message
    [Tags]    unit    trace    event    message
    ${result}=    Trace Event Has Message
    Should Be True    ${result}[has_get]

# =============================================================================
# Trace Store Design Tests
# =============================================================================

Trace Store Has Events
    [Documentation]    GIVEN TraceStore WHEN create THEN has events list
    [Tags]    unit    trace    store    events
    ${result}=    Trace Store Has Events
    Should Be True    ${result}[has_events]
    Should Be True    ${result}[max_100]

Trace Store Limits Events
    [Documentation]    GIVEN TraceStore WHEN add many THEN limits to max
    [Tags]    unit    trace    store    limits
    ${result}=    Trace Store Limits Events
    Should Be True    ${result}[limited]

# =============================================================================
# Module Import Tests
# =============================================================================

Import Trace Event
    [Documentation]    GIVEN trace_bar module WHEN import THEN TraceEvent exists
    [Tags]    unit    trace    import    event
    ${result}=    Import Trace Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]
    Should Be True    ${result}[message_set]

Import Trace Store
    [Documentation]    GIVEN trace_bar module WHEN import THEN TraceStore exists
    [Tags]    unit    trace    import    store
    ${result}=    Import Trace Store
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]
    Should Be True    ${result}[max_100]

Import Trace Transforms
    [Documentation]    GIVEN trace_bar module WHEN import THEN transforms exist
    [Tags]    unit    trace    import    transform
    ${result}=    Import Trace Transforms
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[add_api_callable]

Initial Trace State
    [Documentation]    GIVEN get_initial_trace_state WHEN call THEN structure
    [Tags]    unit    trace    initial    state
    ${result}=    Initial Trace State
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_visible]
    Should Be True    ${result}[has_events]
    Should Be True    ${result}[visible_true]

Initial State Includes Traces
    [Documentation]    GIVEN get_initial_state WHEN call THEN has traces
    [Tags]    unit    trace    initial    integration
    ${result}=    Initial State Includes Traces
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_visible]
    Should Be True    ${result}[has_events]

# =============================================================================
# Trace Event Operations Tests
# =============================================================================

Trace Event To Dict
    [Documentation]    GIVEN TraceEvent WHEN to_dict THEN dict correct
    [Tags]    unit    trace    serialize    dict
    ${result}=    Trace Event To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[endpoint]
    Should Be True    ${result}[duration]

Trace Event Format Display
    [Documentation]    GIVEN TraceEvent WHEN format_display THEN formatted
    [Tags]    unit    trace    format    display
    ${result}=    Trace Event Format Display
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_get]
    Should Be True    ${result}[has_endpoint]
    Should Be True    ${result}[has_duration]

Trace Event Is Error
    [Documentation]    GIVEN TraceEvent WHEN check is_error THEN correct
    [Tags]    unit    trace    event    error
    ${result}=    Trace Event Is Error
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[success_not_error]
    Should Be True    ${result}[error_is_error]

# =============================================================================
# Transform Function Tests
# =============================================================================

Add Api Trace Mock
    [Documentation]    GIVEN mock state WHEN add_api_trace THEN updated
    [Tags]    unit    trace    transform    api
    ${result}=    Add Api Trace Mock
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_events]
    Should Be True    ${result}[endpoint_set]

Add Ui Action Trace Mock
    [Documentation]    GIVEN mock state WHEN add_ui_action_trace THEN updated
    [Tags]    unit    trace    transform    ui
    ${result}=    Add Ui Action Trace Mock
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_events]
    Should Be True    ${result}[is_ui_action]

Clear Traces Mock
    [Documentation]    GIVEN mock state WHEN clear_traces THEN cleared
    [Tags]    unit    trace    transform    clear
    ${result}=    Clear Traces Mock
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[cleared]

Toggle Trace Bar Mock
    [Documentation]    GIVEN mock state WHEN toggle_trace_bar THEN toggled
    [Tags]    unit    trace    transform    toggle
    ${result}=    Toggle Trace Bar Mock
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[first_toggle]
    Should Be True    ${result}[second_toggle]
