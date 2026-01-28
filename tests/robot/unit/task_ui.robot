*** Settings ***
Documentation    Task UI Tests
...              Per: Phase 6.1, RULE-019 (UI/UX Design Standards)
...              Migrated from tests/test_task_ui.py
Library          Collections
Library          ../../libs/TaskUILibrary.py
Resource         ../resources/common.resource
Force Tags             unit    task-ui    agui    rule-019    medium    tasks    task    read    TASK-LIFE-01-v1

*** Test Cases ***
# =============================================================================
# AG-UI Event Type Tests
# =============================================================================

Test AGUI Event Types Defined
    [Documentation]    All AG-UI event types are defined
    [Tags]    event-types
    ${result}=    AGUI Event Types Defined
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['run_started']}
    Should Be True    ${result['text_message']}
    Should Be True    ${result['tool_call_start']}
    Should Be True    ${result['tool_call_end']}
    Should Be True    ${result['state_delta']}
    Should Be True    ${result['run_finished']}
    Should Be True    ${result['run_error']}

Test Task Status Defined
    [Documentation]    All task status values are defined
    [Tags]    event-types
    ${result}=    Task Status Defined
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['pending']}
    Should Be True    ${result['running']}
    Should Be True    ${result['completed']}
    Should Be True    ${result['failed']}
    Should Be True    ${result['cancelled']}

# =============================================================================
# AGUIEvent Tests
# =============================================================================

Test AGUI Event Creation
    [Documentation]    AGUIEvent can be created with required fields
    [Tags]    agui-event
    ${result}=    AGUI Event Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['type_correct']}
    Should Be True    ${result['run_id_correct']}
    Should Be True    ${result['timestamp_exists']}

Test AGUI Event With Data
    [Documentation]    AGUIEvent can include data payload
    [Tags]    agui-event
    ${result}=    AGUI Event With Data
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['data_role']}
    Should Be True    ${result['data_content']}

Test AGUI Event To SSE
    [Documentation]    AGUIEvent converts to SSE format correctly
    [Tags]    agui-event    sse
    ${result}=    AGUI Event To SSE
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['starts_with_data']}
    Should Be True    ${result['ends_with_newlines']}
    Should Be True    ${result['type_correct']}
    Should Be True    ${result['run_id_correct']}
    Should Be True    ${result['agent_correct']}
    Should Be True    ${result['has_timestamp']}

# =============================================================================
# SSE Format Tests
# =============================================================================

Test SSE Format Valid
    [Documentation]    SSE format is valid per specification
    [Tags]    sse    format
    ${result}=    SSE Format Valid
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['starts_with_data']}
    Should Be True    ${result['ends_with_newlines']}
    Should Be True    ${result['has_type']}
    Should Be True    ${result['has_run_id']}

Test SSE Escapes Special Chars
    [Documentation]    SSE properly escapes special characters in JSON
    [Tags]    sse    format
    ${result}=    SSE Escapes Special Chars
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['contains_special_chars']}

# =============================================================================
# Task Submission Tests
# =============================================================================

Test Valid Task Submission
    [Documentation]    Valid task submission is accepted
    [Tags]    submission
    ${result}=    Valid Task Submission
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['prompt_correct']}
    Should Be True    ${result['agent_correct']}
    Should Be True    ${result['dry_run_false']}

Test Task Submission Defaults
    [Documentation]    Task submission has correct defaults
    [Tags]    submission
    ${result}=    Task Submission Defaults
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['agent_orchestrator']}
    Should Be True    ${result['context_none']}
    Should Be True    ${result['dry_run_false']}

Test Task Submission With Context
    [Documentation]    Task submission can include context
    [Tags]    submission
    ${result}=    Task Submission With Context
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['context_file']}
    Should Be True    ${result['context_line']}

Test Empty Prompt Rejected
    [Documentation]    Empty prompt is rejected
    [Tags]    submission    validation
    ${result}=    Empty Prompt Rejected
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['raises_error']}

# =============================================================================
# Task Store Tests
# =============================================================================

Test Task Store Create Task
    [Documentation]    TaskStore creates tasks with unique IDs
    [Tags]    store
    ${result}=    Task Store Create Task
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['task_id_prefix']}
    Should Be True    ${result['status_pending']}
    Should Be True    ${result['prompt_correct']}
    Should Be True    ${result['agent_orchestrator']}

Test Task Store Unique IDs
    [Documentation]    Each task gets a unique ID
    [Tags]    store
    ${result}=    Task Store Unique IDs
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['ids_different']}

Test Task Store Get Task
    [Documentation]    TaskStore retrieves task by ID
    [Tags]    store
    ${result}=    Task Store Get Task
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['task_found']}
    Should Be True    ${result['id_matches']}

Test Task Store Get Nonexistent
    [Documentation]    TaskStore returns None for unknown task ID
    [Tags]    store
    ${result}=    Task Store Get Nonexistent
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['returns_none']}

Test Task Store Update Task
    [Documentation]    TaskStore updates task fields
    [Tags]    store
    ${result}=    Task Store Update Task
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_updated']}

Test Task Store List Tasks
    [Documentation]    TaskStore lists recent tasks
    [Tags]    store
    ${result}=    Task Store List Tasks
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['limit_respected']}

Test Task Store List Order
    [Documentation]    Tasks are listed in reverse chronological order
    [Tags]    store
    ${result}=    Task Store List Order
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['first_is_third']}
    Should Be True    ${result['last_is_first']}

# =============================================================================
# API Router Tests
# =============================================================================

Test Create Task Router
    [Documentation]    create_task_router returns APIRouter
    [Tags]    router
    ${result}=    Create Task Router
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_api_router']}
    Should Be True    ${result['prefix_correct']}

Test Router Has Endpoints
    [Documentation]    Router has required endpoints
    [Tags]    router
    ${result}=    Router Has Endpoints
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_tasks']}
    Should Be True    ${result['has_task_id']}
    Should Be True    ${result['has_events']}

# =============================================================================
# Integration Helper Tests
# =============================================================================

Test Integrate Task UI
    [Documentation]    integrate_task_ui adds router to app
    [Tags]    integration
    ${result}=    Integrate Task UI
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['routes_added']}

Test CORS Middleware Added
    [Documentation]    CORS middleware is added for UI development
    [Tags]    integration
    ${result}=    CORS Middleware Added
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['middleware_added']}

# =============================================================================
# Task Response Tests
# =============================================================================

Test Task Response Fields
    [Documentation]    TaskResponse has all required fields
    [Tags]    response
    ${result}=    Task Response Fields
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['task_id_correct']}
    Should Be True    ${result['status_pending']}
    Should Be True    ${result['agent_correct']}
    Should Be True    ${result['message_correct']}

# =============================================================================
# Task Result Tests
# =============================================================================

Test Task Result Fields
    [Documentation]    TaskResult has all required fields
    [Tags]    result
    ${result}=    Task Result Fields
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['task_id_correct']}
    Should Be True    ${result['status_completed']}
    Should Be True    ${result['response_correct']}
    Should Be True    ${result['duration_correct']}

Test Task Result Defaults
    [Documentation]    TaskResult has correct defaults
    [Tags]    result
    ${result}=    Task Result Defaults
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['response_none']}
    Should Be True    ${result['tool_calls_empty']}
    Should Be True    ${result['error_none']}

# =============================================================================
# Async Tests
# =============================================================================

Test Task Store Emit Event
    [Documentation]    TaskStore emits events to queue
    [Tags]    async    store
    ${result}=    Task Store Emit Event
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['event_in_queue']}

Test Task Store Get Events Yields
    [Documentation]    get_events yields emitted events
    [Tags]    async    store
    ${result}=    Task Store Get Events Yields
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['event_count']}
    Should Be True    ${result['event_type']}

# =============================================================================
# Execute Task Tests
# =============================================================================

Test Execute Task Emits Run Started
    [Documentation]    execute_task emits RUN_STARTED event
    [Tags]    execute
    ${result}=    Execute Task Emits Run Started
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['task_finished']}

Test Execute Task Handles Missing Agent
    [Documentation]    execute_task handles missing agent gracefully
    [Tags]    execute    error-handling
    ${result}=    Execute Task Handles Missing Agent
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_failed']}
    Should Be True    ${result['error_not_found']}
