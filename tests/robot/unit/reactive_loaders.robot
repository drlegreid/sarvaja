*** Settings ***
Documentation    RF-004: Unit Tests - Reactive Loaders with Trace Status
...              Migrated from tests/test_reactive_loaders.py
...              Per GAP-UI-047: Reactive loaders with trace status
Library          Collections
Library          ../../libs/ReactiveLoadersLibrary.py

*** Test Cases ***
# =============================================================================
# Loader State Design Tests
# =============================================================================

Loader State Has Is Loading
    [Documentation]    GIVEN LoaderState WHEN check THEN has is_loading
    [Tags]    unit    loaders    state    design
    ${result}=    Loader State Has Is Loading
    Should Be True    ${result}[has_attr]
    Should Be True    ${result}[default_false]

Loader State Has Error Tracking
    [Documentation]    GIVEN LoaderState WHEN check THEN has error tracking
    [Tags]    unit    loaders    state    error
    ${result}=    Loader State Has Error Tracking
    Should Be True    ${result}[has_error]
    Should Be True    ${result}[has_message]

Loader State Has Trace Metadata
    [Documentation]    GIVEN LoaderState WHEN check THEN has trace metadata
    [Tags]    unit    loaders    state    trace
    ${result}=    Loader State Has Trace Metadata
    Should Be True    ${result}[has_start]
    Should Be True    ${result}[has_end]
    Should Be True    ${result}[has_duration]
    Should Be True    ${result}[has_endpoint]

# =============================================================================
# Loader Module Tests
# =============================================================================

State Initial Has Loader Fields
    [Documentation]    GIVEN state/initial.py WHEN check THEN has loader fields
    [Tags]    unit    loaders    module    initial
    ${result}=    State Initial Has Loader Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    File not found
    Should Be True    ${result}[has_loading]

Import Loader State
    [Documentation]    GIVEN loaders module WHEN import THEN LoaderState exists
    [Tags]    unit    loaders    import    state
    ${result}=    Import Loader State
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]
    Should Be True    ${result}[not_loading]

Import API Trace
    [Documentation]    GIVEN loaders module WHEN import THEN APITrace exists
    [Tags]    unit    loaders    import    trace
    ${result}=    Import API Trace
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]
    Should Be True    ${result}[endpoint_set]

Import Loader Transforms
    [Documentation]    GIVEN loaders module WHEN import THEN transforms exist
    [Tags]    unit    loaders    import    transform
    ${result}=    Import Loader Transforms
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[start_callable]
    Should Be True    ${result}[complete_callable]

Initial Loader States
    [Documentation]    GIVEN get_initial_loader_states WHEN call THEN structure
    [Tags]    unit    loaders    initial    states
    ${result}=    Initial Loader States
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_rules_loader]
    Should Be True    ${result}[has_rules_loading]
    Should Be True    ${result}[rules_not_loading]

Initial State Includes Loaders
    [Documentation]    GIVEN get_initial_state WHEN call THEN has loaders
    [Tags]    unit    loaders    initial    integration
    ${result}=    Initial State Includes Loaders
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_rules_loader]
    Should Be True    ${result}[has_sessions_loader]

# =============================================================================
# Loader State Operations Tests
# =============================================================================

Loader State To Dict
    [Documentation]    GIVEN LoaderState WHEN to_dict THEN dict correct
    [Tags]    unit    loaders    serialize    dict
    ${result}=    Loader State To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_loading]
    Should Be True    ${result}[items_count]

Loader State From Dict
    [Documentation]    GIVEN dict WHEN from_dict THEN LoaderState correct
    [Tags]    unit    loaders    deserialize    dict
    ${result}=    Loader State From Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_loading]
    Should Be True    ${result}[items_count]

API Trace To Dict
    [Documentation]    GIVEN APITrace WHEN to_dict THEN dict correct
    [Tags]    unit    loaders    serialize    trace
    ${result}=    API Trace To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[endpoint]
    Should Be True    ${result}[method]

# =============================================================================
# Transform Function Tests
# =============================================================================

Set Loading Start Mock
    [Documentation]    GIVEN mock state WHEN set_loading_start THEN updated
    [Tags]    unit    loaders    transform    start
    ${result}=    Set Loading Start Mock
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rules_loading]
    Should Be True    ${result}[has_trace]

Set Loading Complete Mock
    [Documentation]    GIVEN mock state WHEN set_loading_complete THEN updated
    [Tags]    unit    loaders    transform    complete
    ${result}=    Set Loading Complete Mock
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_loading]
    Should Be True    ${result}[items_count]

Format Trace Status
    [Documentation]    GIVEN LoaderState WHEN format_trace_status THEN formatted
    [Tags]    unit    loaders    transform    format
    ${result}=    Format Trace Status
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_get]
    Should Be True    ${result}[has_endpoint]
    Should Be True    ${result}[has_duration]
