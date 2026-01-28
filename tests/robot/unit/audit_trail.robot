*** Settings ***
Documentation    RF-004: Unit Tests - Audit Trail Debugability
...              Migrated from tests/test_audit_trail.py
...              Tests correlation_id and applied_rules tracking
Library          Collections
Library          ../../libs/AuditTrailLibrary.py
Force Tags        unit    audit    trail    medium    GOV-TRANSP-01-v1    GAP-MONITOR-IPC-001    session    read

*** Test Cases ***
# =============================================================================
# Session Collector correlation_id Tests
# =============================================================================

Capture Tool Call Accepts correlation_id
    [Documentation]    capture_tool_call method accepts correlation_id parameter
    [Tags]    unit    audit    correlation    signature
    ${has_param}=    Test Capture Tool Call Has Correlation Id
    Should Be True    ${has_param}    correlation_id parameter missing

Capture Tool Call Stores correlation_id
    [Documentation]    capture_tool_call stores correlation_id in event
    [Tags]    unit    audit    correlation    storage
    ${result}=    Test Capture Tool Call Stores Correlation Id
    Should Be True    ${result}[stored]    correlation_id not stored in event

correlation_id Propagates Through Tool Calls
    [Documentation]    Same correlation_id links multiple tool calls
    [Tags]    unit    audit    correlation    propagation
    ${result}=    Test Correlation Id Propagates
    Should Be Equal As Integers    ${result}[event_count]    2
    Should Be True    ${result}[both_have_corr_id]

# =============================================================================
# Session Collector applied_rules Tests
# =============================================================================

Capture Tool Call Accepts applied_rules
    [Documentation]    capture_tool_call method accepts applied_rules parameter
    [Tags]    unit    audit    rules    signature
    ${has_param}=    Test Capture Tool Call Has Applied Rules
    Should Be True    ${has_param}    applied_rules parameter missing

Capture Tool Call Stores applied_rules
    [Documentation]    capture_tool_call stores applied_rules in event
    [Tags]    unit    audit    rules    storage
    ${result}=    Test Capture Tool Call Stores Applied Rules
    Should Be True    ${result}[stored]    applied_rules not stored in event

# =============================================================================
# Session Core MCP Structure Tests
# =============================================================================

Register Session Core Tools Exists
    [Documentation]    register_session_core_tools function exists
    [Tags]    unit    audit    mcp    registration
    ${exists}=    Test Register Session Core Tools Exists
    Should Be True    ${exists}    register_session_core_tools not found

Session Tool Call In Source
    [Documentation]    session_tool_call defined with expected params
    [Tags]    unit    audit    mcp    source
    ${result}=    Test Session Tool Call In Source
    Should Be True    ${result}[has_function]    session_tool_call not defined
    Should Be True    ${result}[has_correlation_id]    correlation_id not in source
    Should Be True    ${result}[has_applied_rules]    applied_rules not in source
    Should Be True    ${result}[has_mcp_decorator]    @mcp.tool() not used

# =============================================================================
# Session Visibility Integration Tests
# =============================================================================

Session Visibility Tracks Rules
    [Documentation]    Session visibility tracks rules applied per task
    [Tags]    unit    audit    visibility    rules
    ${result}=    Test Session Visibility Tracks Rules
    Skip If    '${result.get("skip", False)}' == 'True'    ${result.get("reason", "skipped")}
    Should Be Equal    ${result}[task_id]    TASK-001
    Should Be True    ${result}[has_rule_001]
    Should Be True    ${result}[has_rule_021]

Session Visibility Tracks Tool Calls
    [Documentation]    Session visibility tracks tool calls per task
    [Tags]    unit    audit    visibility    tools
    ${result}=    Test Session Visibility Tracks Tool Calls
    Skip If    '${result.get("skip", False)}' == 'True'    ${result.get("reason", "skipped")}
    Should Be True    ${result}[tool_calls] >= 1
    Should Be True    ${result}[has_rule_021]

# =============================================================================
# End-to-End Audit Trail Tests
# =============================================================================

Full Audit Trail Flow
    [Documentation]    Complete flow: session -> task -> tool call -> rules
    [Tags]    unit    audit    e2e    flow
    ${result}=    Test Full Audit Trail Flow
    Skip If    '${result.get("skip", False)}' == 'True'    ${result.get("reason", "skipped")}
    Should Be True    ${result}[session_id_match]
    Should Be True    ${result}[task_completed]
    Should Be True    ${result}[visibility_has_session]

# =============================================================================
# Commit Info Tracking Tests
# =============================================================================

Commit Info Functions Exist
    [Documentation]    record_commit_info and get_task_commit_info exist
    [Tags]    unit    audit    commit    functions
    ${result}=    Test Commit Info Functions Exist
    Should Be True    ${result}[record_commit_info]    record_commit_info not found
    Should Be True    ${result}[get_task_commit_info]    get_task_commit_info not found
