*** Settings ***
Documentation    SESSION-METRICS-01-v1: Session Log Analytics Integration Tests
...              Validates JSONL parser, calculator, and MCP tool integration.
Library          Collections
Library          ../../libs/SessionMetricsLibrary.py
Suite Setup      Setup Test Log Directory
Suite Teardown   Cleanup Test Dir
Force Tags       unit    session    metrics    SESSION-METRICS-01-v1    validate

*** Variables ***
${TEST_DIR}      ${EMPTY}
${CORR_DIR}      ${EMPTY}
${SEARCH_DIR}    ${EMPTY}
${AGENT_DIR}     ${EMPTY}
${ERROR_DIR}     ${EMPTY}

*** Test Cases ***
# =============================================================================
# Discovery Tests
# =============================================================================

Discover All Log Files Including Agents
    [Documentation]    GIVEN test dir WHEN discover with agents THEN finds 2 files
    [Tags]    unit    discovery    validate
    ${count}=    Discover Log Files Count    ${TEST_DIR}    include_agents=${TRUE}
    Should Be Equal As Integers    ${count}    2

Discover Main Log Files Only
    [Documentation]    GIVEN test dir WHEN discover without agents THEN finds 1 file
    [Tags]    unit    discovery    validate
    ${count}=    Discover Log Files Count    ${TEST_DIR}    include_agents=${FALSE}
    Should Be Equal As Integers    ${count}    1

Discover Empty Directory Returns Zero
    [Documentation]    GIVEN empty dir WHEN discover THEN returns 0
    [Tags]    unit    discovery    validate
    ${count}=    Discover Log Files Count    /tmp/nonexistent_session_metrics_test
    Should Be Equal As Integers    ${count}    0

# =============================================================================
# Parser Tests
# =============================================================================

Parse Log Returns All Entries
    [Documentation]    GIVEN test JSONL WHEN parse THEN correct count
    [Tags]    unit    parser    validate
    ${count}=    Parse Log Entries Count    ${TEST_DIR}
    Should Be Equal As Integers    ${count}    5

Parse Log Extracts Tool Names
    [Documentation]    GIVEN test JSONL WHEN parse THEN tool names extracted
    [Tags]    unit    parser    validate
    ${names}=    Parse Log Tool Names    ${TEST_DIR}
    Should Contain    ${names}    Read
    Should Contain    ${names}    mcp__gov-core__health_check

# =============================================================================
# Calculator Tests
# =============================================================================

Calculate Metrics Splits Sessions
    [Documentation]    GIVEN entries with 40min gap WHEN calculate THEN 2 sessions
    [Tags]    unit    calculator    validate
    ${result}=    Calculate Metrics From Dir    ${TEST_DIR}    idle_threshold=30
    ${session_count}=    Set Variable    ${result}[totals][session_count]
    Should Be Equal As Integers    ${session_count}    2

Calculate Metrics Counts Tools
    [Documentation]    GIVEN entries with tools WHEN calculate THEN correct count
    [Tags]    unit    calculator    validate
    ${result}=    Calculate Metrics From Dir    ${TEST_DIR}
    ${tool_calls}=    Set Variable    ${result}[totals][tool_calls]
    Should Be Equal As Integers    ${tool_calls}    2

Calculate Metrics Counts MCP Calls
    [Documentation]    GIVEN entries with MCP tool WHEN calculate THEN mcp_calls=1
    [Tags]    unit    calculator    validate
    ${result}=    Calculate Metrics From Dir    ${TEST_DIR}
    ${mcp_calls}=    Set Variable    ${result}[totals][mcp_calls]
    Should Be Equal As Integers    ${mcp_calls}    1

Calculate Metrics Has Tool Breakdown
    [Documentation]    GIVEN entries WHEN calculate THEN tool_breakdown populated
    [Tags]    unit    calculator    validate
    ${result}=    Calculate Metrics From Dir    ${TEST_DIR}
    Dictionary Should Contain Key    ${result}[tool_breakdown]    Read
    Dictionary Should Contain Key    ${result}[tool_breakdown]    mcp__gov-core__health_check

Calculate Metrics Active Duration
    [Documentation]    GIVEN 2 sessions (10min + 5min) WHEN calculate THEN 15 total
    [Tags]    unit    calculator    validate
    ${result}=    Calculate Metrics From Dir    ${TEST_DIR}
    ${active}=    Set Variable    ${result}[totals][active_minutes]
    Should Be Equal As Integers    ${active}    15

# =============================================================================
# MCP Tool Integration Tests
# =============================================================================

MCP Tool Returns Valid Structure
    [Documentation]    GIVEN test dir WHEN MCP tool THEN has days/totals/metadata
    [Tags]    unit    mcp    validate
    ${result}=    MCP Tool With Test Dir    ${TEST_DIR}
    Dictionary Should Contain Key    ${result}    days
    Dictionary Should Contain Key    ${result}    totals
    Dictionary Should Contain Key    ${result}    tool_breakdown
    Dictionary Should Contain Key    ${result}    metadata

MCP Tool Metadata Has Log Info
    [Documentation]    GIVEN test dir WHEN MCP tool THEN metadata has log_dir
    [Tags]    unit    mcp    validate
    ${result}=    MCP Tool With Test Dir    ${TEST_DIR}
    Dictionary Should Contain Key    ${result}[metadata]    log_dir
    Dictionary Should Contain Key    ${result}[metadata]    log_files
    Dictionary Should Contain Key    ${result}[metadata]    total_entries_parsed

# =============================================================================
# Correlation Tests (GAP-SESSION-METRICS-CORRELATION)
# =============================================================================

Correlate Tool Calls Returns Matches
    [Documentation]    GIVEN log with tool_use+result WHEN correlate THEN finds 2 pairs
    [Tags]    unit    correlation    validate
    ${correlated}=    Correlate From Dir    ${CORR_DIR}
    Length Should Be    ${correlated}    2

Correlated Call Has Tool Name
    [Documentation]    GIVEN correlated calls WHEN check THEN tool names present
    [Tags]    unit    correlation    validate
    ${correlated}=    Correlate From Dir    ${CORR_DIR}
    ${names}=    Evaluate    [c['tool_name'] for c in $correlated]
    Should Contain    ${names}    Read
    Should Contain    ${names}    mcp__gov-core__health_check

Correlated Call Has Latency
    [Documentation]    GIVEN correlated calls WHEN check THEN latency_ms >= 0
    [Tags]    unit    correlation    validate
    ${correlated}=    Correlate From Dir    ${CORR_DIR}
    FOR    ${call}    IN    @{correlated}
        Should Be True    ${call}[latency_ms] >= 0
    END

Correlated Read Latency Is 500ms
    [Documentation]    GIVEN Read tool_use+result WHEN correlate THEN 500ms latency
    [Tags]    unit    correlation    validate
    ${correlated}=    Correlate From Dir    ${CORR_DIR}
    ${read_call}=    Evaluate    [c for c in $correlated if c['tool_name'] == 'Read'][0]
    Should Be Equal As Integers    ${read_call}[latency_ms]    500

Correlated MCP Has Server Name
    [Documentation]    GIVEN MCP tool_result with mcpMeta WHEN correlate THEN server_name set
    [Tags]    unit    correlation    validate
    ${correlated}=    Correlate From Dir    ${CORR_DIR}
    ${mcp_call}=    Evaluate    [c for c in $correlated if c['is_mcp']][0]
    Should Be Equal    ${mcp_call}[server_name]    gov-core

Correlation Summary Has Stats
    [Documentation]    GIVEN correlated calls WHEN summarize THEN has totals/per_server
    [Tags]    unit    correlation    validate
    ${summary}=    Summarize Correlation From Dir    ${CORR_DIR}
    Should Be Equal As Integers    ${summary}[total_correlated]    2
    Dictionary Should Contain Key    ${summary}    avg_latency_ms
    Dictionary Should Contain Key    ${summary}    per_server
    Dictionary Should Contain Key    ${summary}    per_tool

Correlation Summary Per Server
    [Documentation]    GIVEN MCP calls WHEN summarize THEN per_server has gov-core
    [Tags]    unit    correlation    validate
    ${summary}=    Summarize Correlation From Dir    ${CORR_DIR}
    Dictionary Should Contain Key    ${summary}[per_server]    gov-core
    Should Be Equal As Integers    ${summary}[per_server][gov-core][count]    1

# =============================================================================
# Content Search Tests (GAP-SESSION-METRICS-CONTENT)
# =============================================================================

Search Finds Text Match
    [Documentation]    GIVEN log with text WHEN search 'authentication' THEN finds match
    [Tags]    unit    search    validate
    ${results}=    Search Entries From Dir    ${SEARCH_DIR}    query=authentication
    ${len}=    Get Length    ${results}
    Should Be True    ${len} >= 1

Search Is Case Insensitive
    [Documentation]    GIVEN log WHEN search 'DECISION' THEN finds match (case insensitive)
    [Tags]    unit    search    validate
    ${results}=    Search Entries From Dir    ${SEARCH_DIR}    query=DECISION
    ${len}=    Get Length    ${results}
    Should Be True    ${len} >= 1

Search By Session ID
    [Documentation]    GIVEN log WHEN filter session_id=sess-A THEN only sess-A entries
    [Tags]    unit    search    validate
    ${results}=    Search Entries From Dir    ${SEARCH_DIR}    session_id=sess-A
    ${len}=    Get Length    ${results}
    Should Be True    ${len} >= 1
    FOR    ${r}    IN    @{results}
        Should Be Equal    ${r}[session_id]    sess-A
    END

Search By Git Branch
    [Documentation]    GIVEN log WHEN filter branch=feature/dashboard THEN only that branch
    [Tags]    unit    search    validate
    ${results}=    Search Entries From Dir    ${SEARCH_DIR}    git_branch=feature/dashboard
    ${len}=    Get Length    ${results}
    Should Be True    ${len} >= 1
    FOR    ${r}    IN    @{results}
        Should Be Equal    ${r}[git_branch]    feature/dashboard
    END

Search Combined Query And Branch
    [Documentation]    GIVEN log WHEN search 'React' on feature/dashboard THEN match
    [Tags]    unit    search    validate
    ${results}=    Search Entries From Dir    ${SEARCH_DIR}    query=React    git_branch=feature/dashboard
    ${len}=    Get Length    ${results}
    Should Be True    ${len} >= 1

Search No Match Returns Empty
    [Documentation]    GIVEN log WHEN search nonexistent term THEN empty list
    [Tags]    unit    search    validate
    ${results}=    Search Entries From Dir    ${SEARCH_DIR}    query=zzz_no_match_zzz
    Length Should Be    ${results}    0

# =============================================================================
# Agent Subprocess Tests (GAP-SESSION-METRICS-AGENTS)
# =============================================================================

Agent Metrics Counts Agents
    [Documentation]    GIVEN dir with 1 agent file WHEN calculate THEN agent_count=1
    [Tags]    unit    agents    validate
    ${result}=    Agent Metrics From Dir    ${AGENT_DIR}
    Should Be Equal As Integers    ${result}[agent_count]    1

Agent Metrics Has Tool Calls
    [Documentation]    GIVEN agent with 1 tool call WHEN calculate THEN total_tool_calls=1
    [Tags]    unit    agents    validate
    ${result}=    Agent Metrics From Dir    ${AGENT_DIR}
    Should Be Equal As Integers    ${result}[total_tool_calls]    1

Agent Metrics Has Per Agent Breakdown
    [Documentation]    GIVEN 1 agent WHEN calculate THEN per_agent has 1 entry
    [Tags]    unit    agents    validate
    ${result}=    Agent Metrics From Dir    ${AGENT_DIR}
    Length Should Be    ${result}[per_agent]    1
    ${agent}=    Set Variable    ${result}[per_agent][0]
    Should Be Equal    ${agent}[file_name]    agent-explore.jsonl

Agent Metrics Has Tool Breakdown
    [Documentation]    GIVEN agent with Grep call WHEN calculate THEN tool_breakdown has Grep
    [Tags]    unit    agents    validate
    ${result}=    Agent Metrics From Dir    ${AGENT_DIR}
    Dictionary Should Contain Key    ${result}[tool_breakdown]    Grep

# =============================================================================
# Error/Retry Tests (GAP-SESSION-METRICS-ERRORS)
# =============================================================================

Error Metrics Counts API Errors
    [Documentation]    GIVEN log with 2 API errors WHEN calculate THEN api_errors=2
    [Tags]    unit    errors    validate
    ${result}=    Error Metrics From Dir    ${ERROR_DIR}
    Should Be Equal As Integers    ${result}[totals][api_errors]    2

Error Metrics Day Has Errors
    [Documentation]    GIVEN errors on one day WHEN calculate THEN day api_errors=2
    [Tags]    unit    errors    validate
    ${result}=    Error Metrics From Dir    ${ERROR_DIR}
    ${day}=    Set Variable    ${result}[days][0]
    Should Be Equal As Integers    ${day}[api_errors]    2

Error Metrics Has Error Rate
    [Documentation]    GIVEN 2 errors / 6 messages WHEN calculate THEN error_rate ~0.33
    [Tags]    unit    errors    validate
    ${result}=    Error Metrics From Dir    ${ERROR_DIR}
    ${rate}=    Set Variable    ${result}[totals][error_rate]
    Should Be True    ${rate} >= 0.3
    Should Be True    ${rate} <= 0.4

Error Metrics Serializable
    [Documentation]    GIVEN error metrics WHEN to_dict THEN api_errors key exists
    [Tags]    unit    errors    validate
    ${result}=    Error Metrics From Dir    ${ERROR_DIR}
    Dictionary Should Contain Key    ${result}[totals]    api_errors
    Dictionary Should Contain Key    ${result}[totals]    error_rate

*** Keywords ***
Setup Test Log Directory
    [Documentation]    Create temporary test directory with sample JSONL data
    ${dir}=    Create Test Log Dir
    Set Suite Variable    ${TEST_DIR}    ${dir}
    ${corr_dir}=    Create Correlation Test Dir
    Set Suite Variable    ${CORR_DIR}    ${corr_dir}
    ${search_dir}=    Create Search Test Dir
    Set Suite Variable    ${SEARCH_DIR}    ${search_dir}
    ${agent_dir}=    Create Agent Test Dir
    Set Suite Variable    ${AGENT_DIR}    ${agent_dir}
    ${error_dir}=    Create Error Test Dir
    Set Suite Variable    ${ERROR_DIR}    ${error_dir}
