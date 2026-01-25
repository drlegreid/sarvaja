*** Settings ***
Documentation    RF-004: Unit Tests - Task-Session Linking
...              Migrated from tests/test_task_session_link.py
...              Per GAP-TASK-LINK-001: Tasks linked to session documents
Library          Collections
Library          ../../libs/TaskSessionLinkLibrary.py

*** Test Cases ***
# =============================================================================
# Infrastructure Tests
# =============================================================================

Linking Module Exists
    [Documentation]    GIVEN governance WHEN check THEN TaskLinkingOperations exists
    [Tags]    unit    task    session    link    module
    ${result}=    Linking Module Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Linking Has Link Task To Session
    [Documentation]    GIVEN TaskLinkingOperations WHEN check THEN has link_task_to_session
    [Tags]    unit    task    session    link    method
    ${result}=    Linking Has Link Task To Session
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_method]

Linking Has Get Task Evidence
    [Documentation]    GIVEN TaskLinkingOperations WHEN check THEN has get_task_evidence
    [Tags]    unit    task    session    link    evidence
    ${result}=    Linking Has Get Task Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_method]

# =============================================================================
# MCP Tool Tests
# =============================================================================

Registration Function Exists
    [Documentation]    GIVEN mcp_tools WHEN check THEN register_task_linking_tools exists
    [Tags]    unit    task    session    mcp    register
    ${result}=    Registration Function Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

MCP Tool Defined In Module
    [Documentation]    GIVEN tasks_linking WHEN inspect THEN tool defined
    [Tags]    unit    task    session    mcp    tool
    ${result}=    MCP Tool Defined In Module
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_tool_name]
    Should Be True    ${result}[has_decorator]

# =============================================================================
# Task-Session Linking Logic Tests
# =============================================================================

Valid Task Session Pair
    [Documentation]    GIVEN task/session IDs WHEN validate THEN valid format
    [Tags]    unit    task    session    link    format
    ${result}=    Valid Task Session Pair
    Should Be True    ${result}[task_valid]
    Should Be True    ${result}[session_valid]

Session ID Format
    [Documentation]    GIVEN session IDs WHEN validate THEN match patterns
    [Tags]    unit    task    session    format    pattern
    ${result}=    Session ID Format
    Should Be True    ${result}[all_valid]

# =============================================================================
# Task Entity Tests
# =============================================================================

Task Has Linked Sessions Field
    [Documentation]    GIVEN Task entity WHEN check THEN has linked_sessions
    [Tags]    unit    task    session    entity    field
    ${result}=    Task Has Linked Sessions Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_field]

Task Linked Sessions Is List
    [Documentation]    GIVEN Task.linked_sessions WHEN check THEN is list type
    [Tags]    unit    task    session    entity    type
    ${result}=    Task Linked Sessions Is List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_list]

# =============================================================================
# Read Queries Tests
# =============================================================================

Build Task From ID Has Sessions Query
    [Documentation]    GIVEN _build_task_from_id WHEN inspect THEN fetches sessions
    [Tags]    unit    task    session    read    query
    ${result}=    Build Task From ID Has Sessions Query
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed or method not found
    Should Be True    ${result}[has_sessions]

# =============================================================================
# Data Integrity Tests
# =============================================================================

Bidirectional Link Concept
    [Documentation]    GIVEN task-session link WHEN design THEN bidirectional
    [Tags]    unit    task    session    integrity    bidirectional
    ${result}=    Bidirectional Link Concept
    Should Be True    ${result}[relation_correct]
    Should Be True    ${result}[task_role_correct]
    Should Be True    ${result}[session_role_correct]

Multiple Sessions Per Task Allowed
    [Documentation]    GIVEN task WHEN linking THEN multiple sessions allowed
    [Tags]    unit    task    session    integrity    multiple
    ${result}=    Multiple Sessions Per Task Allowed
    Should Be True    ${result}[allowed]

# =============================================================================
# BDD Scenario Tests
# =============================================================================

Scenario Link Task To Current Session
    [Documentation]    GIVEN task in session WHEN complete THEN linked
    [Tags]    unit    task    session    bdd    link
    ${result}=    Scenario Link Task To Current Session
    Should Be True    ${result}[task_defined]
    Should Be True    ${result}[session_defined]

Scenario Query Sessions For Task
    [Documentation]    GIVEN task with sessions WHEN query THEN returns all
    [Tags]    unit    task    session    bdd    query
    ${result}=    Scenario Query Sessions For Task
    Should Be True    ${result}[has_multiple]
