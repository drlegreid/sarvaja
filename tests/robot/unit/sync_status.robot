*** Settings ***
Documentation    RF-004: Unit Tests - Sync Status Tool
...              Migrated from tests/test_sync_status.py
...              Per GAP-SYNC-002: Divergence Validation Workflow
Library          Collections
Library          ../../libs/SyncStatusLibrary.py

*** Test Cases ***
# =============================================================================
# Tool Existence Tests
# =============================================================================

Sync Status Tool Exists
    [Documentation]    GIVEN mcp_tools.workspace WHEN import THEN register_workspace_tools exists
    [Tags]    unit    sync    status    tool    exists
    ${result}=    Sync Status Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Sync Status Tool Returns JSON
    [Documentation]    GIVEN governance_sync_status WHEN call THEN returns valid YAML/JSON
    [Tags]    unit    sync    status    tool    format
    ${result}=    Sync Status Tool Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[has_tool]
    Should Be True    ${result}[result_not_none]
    Should Be True    ${result}[valid_format]

Sync Status Structure Valid
    [Documentation]    GIVEN governance_sync_status WHEN call THEN has expected structure
    [Tags]    unit    sync    status    tool    structure
    ${result}=    Sync Status Structure Valid
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    ${has_error}=    Evaluate    $result.get('has_error', False)
    Skip If    ${has_error}    TypeDB connection error
    Should Be True    ${result}[has_rules]
    Should Be True    ${result}[has_tasks]
    Should Be True    ${result}[has_sessions]
    Should Be True    ${result}[has_sync_needed]
    Should Be True    ${result}[has_timestamp]

# =============================================================================
# Workspace Tools Registration Tests
# =============================================================================

All Workspace Tools Registered
    [Documentation]    GIVEN register_workspace_tools WHEN call THEN 10 tools registered
    [Tags]    unit    sync    workspace    tools    register
    ${result}=    All Workspace Tools Registered
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_registered]
    Should Be True    ${result}[count_correct]
