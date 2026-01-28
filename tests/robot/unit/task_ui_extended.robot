*** Settings ***
Documentation    RF-004: Task UI Extended Tests (EventTypes, Execution, Router, Store)
...              Migrated from test_task_ui.py
...              Per RF-007 Robot Framework Migration
Library          ../../libs/TaskUIEventTypesLibrary.py
Library          ../../libs/TaskUIExecutionLibrary.py
Library          ../../libs/TaskUIRouterLibrary.py
Library          ../../libs/TaskUIStoreLibrary.py
Library          Collections
Resource         ../resources/common.resource
Force Tags             unit    task-ui    extended    tasks    low    task    read    TASK-LIFE-01-v1

*** Test Cases ***
# =============================================================================
# Event Types Tests
# =============================================================================

AGUI Event Types Defined
    [Documentation]    Test: AGUI Event Types Defined
    ${result}=    AGUI Event Types Defined
    Skip If Import Failed    ${result}

Task Status Defined
    [Documentation]    Test: Task Status Defined
    ${result}=    Task Status Defined
    Skip If Import Failed    ${result}

AGUI Event Creation
    [Documentation]    Test: AGUI Event Creation
    ${result}=    AGUI Event Creation
    Skip If Import Failed    ${result}

AGUI Event With Data
    [Documentation]    Test: AGUI Event With Data
    ${result}=    AGUI Event With Data
    Skip If Import Failed    ${result}

AGUI Event To SSE
    [Documentation]    Test: AGUI Event To SSE
    ${result}=    AGUI Event To SSE
    Skip If Import Failed    ${result}

SSE Format Valid
    [Documentation]    Test: SSE Format Valid
    ${result}=    SSE Format Valid
    Skip If Import Failed    ${result}

SSE Escapes Special Chars
    [Documentation]    Test: SSE Escapes Special Chars
    ${result}=    SSE Escapes Special Chars
    Skip If Import Failed    ${result}

# =============================================================================
# Execution Tests
# =============================================================================

Task Store Emit Event
    [Documentation]    Test: Task Store Emit Event
    ${result}=    Task Store Emit Event
    Skip If Import Failed    ${result}

Task Store Get Events Yields
    [Documentation]    Test: Task Store Get Events Yields
    ${result}=    Task Store Get Events Yields
    Skip If Import Failed    ${result}

Execute Task Emits Run Started
    [Documentation]    Test: Execute Task Emits Run Started
    ${result}=    Execute Task Emits Run Started
    Skip If Import Failed    ${result}

Execute Task Handles Missing Agent
    [Documentation]    Test: Execute Task Handles Missing Agent
    ${result}=    Execute Task Handles Missing Agent
    Skip If Import Failed    ${result}

# =============================================================================
# Router Tests
# =============================================================================

Create Task Router
    [Documentation]    Test: Create Task Router
    ${result}=    Create Task Router
    Skip If Import Failed    ${result}

Router Has Endpoints
    [Documentation]    Test: Router Has Endpoints
    ${result}=    Router Has Endpoints
    Skip If Import Failed    ${result}

Integrate Task UI
    [Documentation]    Test: Integrate Task UI
    ${result}=    Integrate Task UI
    Skip If Import Failed    ${result}

CORS Middleware Added
    [Documentation]    Test: CORS Middleware Added
    ${result}=    CORS Middleware Added
    Skip If Import Failed    ${result}

Task Response Fields
    [Documentation]    Test: Task Response Fields
    ${result}=    Task Response Fields
    Skip If Import Failed    ${result}

Task Result Fields
    [Documentation]    Test: Task Result Fields
    ${result}=    Task Result Fields
    Skip If Import Failed    ${result}

Task Result Defaults
    [Documentation]    Test: Task Result Defaults
    ${result}=    Task Result Defaults
    Skip If Import Failed    ${result}

# =============================================================================
# Store Tests
# =============================================================================

Valid Task Submission
    [Documentation]    Test: Valid Task Submission
    ${result}=    Valid Task Submission
    Skip If Import Failed    ${result}

Task Submission Defaults
    [Documentation]    Test: Task Submission Defaults
    ${result}=    Task Submission Defaults
    Skip If Import Failed    ${result}

Task Submission With Context
    [Documentation]    Test: Task Submission With Context
    ${result}=    Task Submission With Context
    Skip If Import Failed    ${result}

Empty Prompt Rejected
    [Documentation]    Test: Empty Prompt Rejected
    ${result}=    Empty Prompt Rejected
    Skip If Import Failed    ${result}

Task Store Create Task
    [Documentation]    Test: Task Store Create Task
    ${result}=    Task Store Create Task
    Skip If Import Failed    ${result}

Task Store Unique IDs
    [Documentation]    Test: Task Store Unique IDs
    ${result}=    Task Store Unique IDs
    Skip If Import Failed    ${result}

Task Store Get Task
    [Documentation]    Test: Task Store Get Task
    ${result}=    Task Store Get Task
    Skip If Import Failed    ${result}

Task Store Get Nonexistent
    [Documentation]    Test: Task Store Get Nonexistent
    ${result}=    Task Store Get Nonexistent
    Skip If Import Failed    ${result}

Task Store Update Task
    [Documentation]    Test: Task Store Update Task
    ${result}=    Task Store Update Task
    Skip If Import Failed    ${result}

Task Store List Tasks
    [Documentation]    Test: Task Store List Tasks
    ${result}=    Task Store List Tasks
    Skip If Import Failed    ${result}

Task Store List Order
    [Documentation]    Test: Task Store List Order
    ${result}=    Task Store List Order
    Skip If Import Failed    ${result}
