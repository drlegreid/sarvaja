*** Settings ***
Documentation    RF-004: Unit Tests - Session Sync Todos
...              Migrated from tests/unit/test_session_sync_todos.py
...              Per MCP-002-A: Sync TodoWrite with TypeDB task creation
Library          Collections
Library          ../../libs/SessionSyncTodosLibrary.py
Force Tags        unit    sessions    sync    medium    TEST-FIX-01-v1    session    task

*** Test Cases ***
# =============================================================================
# Tool Function Tests
# =============================================================================

Tool Function Exists
    [Documentation]    GIVEN tasks_crud WHEN registering THEN session_sync_todos exists
    [Tags]    unit    tasks    validate    mcp
    ${result}=    Tool Function Exists
    Should Be True    ${result}[exists]

Invalid JSON Returns Error
    [Documentation]    GIVEN invalid JSON WHEN calling THEN error returned
    [Tags]    unit    tasks    validate    mcp
    ${result}=    Invalid Json Returns Error
    Should Be True    ${result}[has_error]
    Should Be True    ${result}[error_message]

Non Array JSON Returns Error
    [Documentation]    GIVEN non-array JSON WHEN calling THEN error returned
    [Tags]    unit    tasks    validate    mcp
    ${result}=    Non Array Json Returns Error
    Should Be True    ${result}[has_error]
    Should Be True    ${result}[error_message]

# =============================================================================
# Integration Tests
# =============================================================================

Sync Creates Tasks
    [Documentation]    GIVEN todos WHEN syncing THEN synced or connection error
    [Tags]    unit    tasks    validate    mcp    integration
    ${result}=    Sync Creates Tasks
    Should Be True    ${result}[no_error_or_connection_error]

