*** Settings ***
Documentation    RF-004: Unit Tests - Session Tool Logger Hook
...              Migrated from tests/unit/test_session_tool_logger.py
...              Per GAP-SESSION-THOUGHT-001: Hook integration for auto-logging
Library          Collections
Library          ../../libs/SessionToolLoggerLibrary.py

*** Test Cases ***
# =============================================================================
# Module Import Tests
# =============================================================================

Session Tool Logger Module Imports
    [Documentation]    GIVEN session_tool_logger module WHEN importing THEN succeeds
    [Tags]    unit    hooks    read    import
    ${result}=    Module Imports Successfully
    Should Be True    ${result}

# =============================================================================
# Input Parsing Tests
# =============================================================================

Parse Tool Input From Env Valid JSON
    [Documentation]    GIVEN CLAUDE_TOOL_INPUT with JSON WHEN parsing THEN returns parsed dict
    [Tags]    unit    hooks    validate    input
    ${json_str}=    Set Variable    {"command": "ls -la", "timeout": 30000}
    ${result}=    Parse Tool Input With Env    ${json_str}
    Should Be Equal    ${result}[command]    ls -la
    Should Be Equal As Integers    ${result}[timeout]    30000

Parse Tool Input Empty Returns Empty Dict
    [Documentation]    GIVEN empty CLAUDE_TOOL_INPUT WHEN parsing THEN returns empty dict
    [Tags]    unit    hooks    validate    input
    ${result}=    Parse Tool Input Empty
    ${length}=    Get Length    ${result}
    Should Be Equal As Integers    ${length}    0

Parse Tool Input Invalid JSON Returns Raw
    [Documentation]    GIVEN invalid JSON WHEN parsing THEN returns dict with raw value
    [Tags]    unit    hooks    validate    input
    ${result}=    Parse Tool Input Invalid    not-json
    Should Be Equal    ${result}[raw]    not-json

Get Tool Name From Env
    [Documentation]    GIVEN CLAUDE_TOOL_NAME env var WHEN getting THEN returns name
    [Tags]    unit    hooks    validate    input
    ${result}=    Get Tool Name With Env    Bash
    Should Be Equal    ${result}    Bash

# =============================================================================
# Session Detection Tests
# =============================================================================

Get Active Session From State
    [Documentation]    GIVEN active session in state WHEN getting THEN returns session ID
    [Tags]    unit    hooks    sessions    validate
    ${result}=    Get Active Session With State    SESSION-2026-01-21-QUALITY
    Should Be Equal    ${result}    SESSION-2026-01-21-QUALITY

No Active Session Returns None
    [Documentation]    GIVEN no active session WHEN getting THEN returns None
    [Tags]    unit    hooks    sessions    validate
    ${result}=    Get Active Session No State
    Should Be Equal    ${result}    ${None}

# =============================================================================
# Tool Call Logging Tests
# =============================================================================

Log Tool Call Success
    [Documentation]    GIVEN active session WHEN logging tool call THEN returns True
    [Tags]    unit    hooks    sessions    create
    ${result}=    Log Tool Call Success
    Should Be True    ${result}

Log Tool Call No Session Returns False
    [Documentation]    GIVEN no active session WHEN logging THEN returns False without error
    [Tags]    unit    hooks    sessions    validate
    ${result}=    Log Tool Call No Session
    Should Be True    ${result}

Log Tool Call TypeDB Down Returns False
    [Documentation]    GIVEN TypeDB unavailable WHEN logging THEN returns False without raising
    [Tags]    unit    hooks    sessions    validate    reliability
    ${result}=    Log Tool Call Typedb Down
    Should Be True    ${result}

# =============================================================================
# Performance Tests
# =============================================================================

Hook Completes Under 500ms
    [Documentation]    GIVEN normal conditions WHEN hook executes THEN completes in under 500ms
    [Tags]    unit    hooks    performance    validate
    ${result}=    Hook Completes Under 500ms
    Should Be True    ${result}[passed]    Hook took ${result}[elapsed_ms]ms, exceeds 500ms limit

# =============================================================================
# Integration Tests
# =============================================================================

Full Flow Captures All Fields
    [Documentation]    GIVEN active session WHEN logging tool call THEN captures all required fields
    [Tags]    integration    hooks    sessions    validate
    ${result}=    Full Flow Captures All Fields
    Should Be True    ${result}[all_present]

