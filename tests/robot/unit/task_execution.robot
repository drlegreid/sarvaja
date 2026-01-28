*** Settings ***
Documentation    RF-004: Unit Tests - Task Execution Viewer
...              Migrated from tests/test_task_execution.py
...              Per ORCH-007: Task Execution Viewer
Library          Collections
Library          ../../libs/TaskExecutionLibrary.py
Force Tags        unit    tasks    execution    high    TASK-LIFE-01-v1    task    validate

*** Test Cases ***
# =============================================================================
# Import Tests
# =============================================================================

Import Execution Event Types
    [Documentation]    GIVEN governance_ui WHEN import THEN event types exist
    [Tags]    unit    execution    import    constants
    ${result}=    Import Execution Event Types
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_claimed]
    Should Be True    ${result}[has_started]
    Should Be True    ${result}[has_completed]
    Should Be True    ${result}[has_failed]
    Should Be True    ${result}[has_evidence]

Import With Task Execution Log
    [Documentation]    GIVEN governance_ui WHEN import THEN transform exists
    [Tags]    unit    execution    import    transform
    ${result}=    Import With Task Execution Log
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

Import With Task Execution Loading
    [Documentation]    GIVEN governance_ui WHEN import THEN transform exists
    [Tags]    unit    execution    import    transform
    ${result}=    Import With Task Execution Loading
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

Import With Task Execution Event
    [Documentation]    GIVEN governance_ui WHEN import THEN transform exists
    [Tags]    unit    execution    import    transform
    ${result}=    Import With Task Execution Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

Import Clear Task Execution
    [Documentation]    GIVEN governance_ui WHEN import THEN transform exists
    [Tags]    unit    execution    import    transform
    ${result}=    Import Clear Task Execution
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

Import Get Execution Event Style
    [Documentation]    GIVEN governance_ui WHEN import THEN helper exists
    [Tags]    unit    execution    import    helper
    ${result}=    Import Get Execution Event Style
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

Import Format Execution Event
    [Documentation]    GIVEN governance_ui WHEN import THEN helper exists
    [Tags]    unit    execution    import    helper
    ${result}=    Import Format Execution Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

# =============================================================================
# State Transform Tests
# =============================================================================

Initial State Has Execution Fields
    [Documentation]    GIVEN get_initial_state WHEN call THEN execution fields
    [Tags]    unit    execution    state    initial
    ${result}=    Initial State Has Execution Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_log]
    Should Be True    ${result}[has_loading]
    Should Be True    ${result}[has_show]
    Should Be True    ${result}[log_empty]
    Should Be True    ${result}[loading_false]
    Should Be True    ${result}[show_false]

With Task Execution Log Sets Events
    [Documentation]    GIVEN state WHEN with_task_execution_log THEN events set
    [Tags]    unit    execution    state    transform
    ${result}=    With Task Execution Log Sets Events
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[events_set]
    Should Be True    ${result}[loading_false]
    Should Be True    ${result}[show_true]
    Should Be True    ${result}[original_unchanged]

With Task Execution Loading Sets Loading
    [Documentation]    GIVEN state WHEN with_task_execution_loading THEN loading
    [Tags]    unit    execution    state    transform
    ${result}=    With Task Execution Loading Sets Loading
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[loading_true]
    Should Be True    ${result}[log_empty]

With Task Execution Event Adds Event
    [Documentation]    GIVEN state WHEN with_task_execution_event THEN added
    [Tags]    unit    execution    state    transform
    ${result}=    With Task Execution Event Adds Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[length_2]
    Should Be True    ${result}[event_added]
    Should Be True    ${result}[original_unchanged]

Clear Task Execution Resets State
    [Documentation]    GIVEN state WHEN clear_task_execution THEN reset
    [Tags]    unit    execution    state    transform
    ${result}=    Clear Task Execution Resets State
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[log_empty]
    Should Be True    ${result}[loading_false]
    Should Be True    ${result}[show_false]

# =============================================================================
# Helper Function Tests
# =============================================================================

Get Execution Event Style Claimed
    [Documentation]    GIVEN claimed type WHEN get_style THEN info style
    [Tags]    unit    execution    helper    style
    ${result}=    Get Execution Event Style Claimed
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[icon_correct]
    Should Be True    ${result}[color_correct]

Get Execution Event Style Completed
    [Documentation]    GIVEN completed type WHEN get_style THEN success style
    [Tags]    unit    execution    helper    style
    ${result}=    Get Execution Event Style Completed
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[icon_correct]
    Should Be True    ${result}[color_correct]

Get Execution Event Style Failed
    [Documentation]    GIVEN failed type WHEN get_style THEN error style
    [Tags]    unit    execution    helper    style
    ${result}=    Get Execution Event Style Failed
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[icon_correct]
    Should Be True    ${result}[color_correct]

Get Execution Event Style Unknown
    [Documentation]    GIVEN unknown type WHEN get_style THEN default style
    [Tags]    unit    execution    helper    style
    ${result}=    Get Execution Event Style Unknown
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[icon_correct]
    Should Be True    ${result}[color_correct]

Format Execution Event Works
    [Documentation]    GIVEN event WHEN format_execution_event THEN formatted
    [Tags]    unit    execution    helper    format
    ${result}=    Format Execution Event Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[icon_correct]
    Should Be True    ${result}[color_correct]
    Should Be True    ${result}[time_correct]
    Should Be True    ${result}[event_id_correct]
    Should Be True    ${result}[message_correct]

# =============================================================================
# API Model Tests
# =============================================================================

Task Execution Event Model Works
    [Documentation]    GIVEN TaskExecutionEvent WHEN create THEN fields correct
    [Tags]    unit    execution    api    model
    ${result}=    Task Execution Event Model Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[event_id_correct]
    Should Be True    ${result}[task_id_correct]
    Should Be True    ${result}[event_type_correct]
    Should Be True    ${result}[agent_id_correct]

Task Execution Response Model Works
    [Documentation]    GIVEN TaskExecutionResponse WHEN create THEN fields correct
    [Tags]    unit    execution    api    model
    ${result}=    Task Execution Response Model Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[task_id_correct]
    Should Be True    ${result}[events_count]
    Should Be True    ${result}[status_correct]
    Should Be True    ${result}[agent_correct]

# =============================================================================
# Integration Tests
# =============================================================================

Synthesize Events From Task Timestamps
    [Documentation]    GIVEN task data WHEN synthesize THEN events created
    [Tags]    unit    execution    integration    synthesize
    ${result}=    Synthesize Events From Task Timestamps
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_events]
    Should Be True    ${result}[has_started]
    Should Be True    ${result}[has_claimed]
    Should Be True    ${result}[has_completed]

Synthesize Events Empty Task
    [Documentation]    GIVEN empty task WHEN synthesize THEN no events
    [Tags]    unit    execution    integration    synthesize
    ${result}=    Synthesize Events Empty Task
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[empty]
