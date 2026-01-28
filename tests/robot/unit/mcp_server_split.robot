*** Settings ***
Documentation    RF-004: Integration Tests - MCP Server Split
...              Migrated from tests/test_mcp_server_split.py
...              Per 4-Server Split Architecture (2026-01-03)
Library          Collections
Library          ../../libs/McpServerSplitLibrary.py
Force Tags        unit    mcp    server    medium    DOC-SIZE-01-v1    validate

*** Test Cases ***
# =============================================================================
# Server Import Tests
# =============================================================================

Core Server Module Imports
    [Documentation]    Core server module must import without errors
    [Tags]    integration    mcp    server    core
    ${result}=    Test Core Server Imports
    Should Be True    ${result}[success]    Import failed: ${result}[stderr]

Agents Server Module Imports
    [Documentation]    Agents server module must import without errors
    [Tags]    integration    mcp    server    agents
    ${result}=    Test Agents Server Imports
    Should Be True    ${result}[success]    Import failed: ${result}[stderr]

Sessions Server Module Imports
    [Documentation]    Sessions server module must import without errors
    [Tags]    integration    mcp    server    sessions
    ${result}=    Test Sessions Server Imports
    Should Be True    ${result}[success]    Import failed: ${result}[stderr]

Tasks Server Module Imports
    [Documentation]    Tasks server module must import without errors
    [Tags]    integration    mcp    server    tasks
    ${result}=    Test Tasks Server Imports
    Should Be True    ${result}[success]    Import failed: ${result}[stderr]

Compat Package Exports Legacy Functions
    [Documentation]    Compat package must export all legacy functions
    [Tags]    integration    mcp    compat    legacy
    ${result}=    Test Compat Package Imports
    Should Be True    ${result}[success]    Import failed: ${result}[stderr]

# =============================================================================
# MCP Config Validation Tests
# =============================================================================

MCP Config Has 4 Split Servers
    [Documentation]    MCP config must have 4 split server definitions
    [Tags]    unit    mcp    config    servers
    ${result}=    Mcp Config Has 4 Servers
    Should Be True    ${result}[has_all]    Missing servers: ${result}[missing]
    Should Not Be True    ${result}[has_deprecated_monolith]    Deprecated monolith should be removed

Each Server Has Required Fields
    [Documentation]    Each governance server config must have required fields
    [Tags]    unit    mcp    config    fields
    ${result}=    Each Server Has Required Fields
    Should Be True    ${result}[all_valid]    Issues: ${result}[issues]

# =============================================================================
# Modularized Files Tests
# =============================================================================

Rules Orchestrator Under 50 Lines
    [Documentation]    rules.py must be a thin orchestrator
    [Tags]    unit    mcp    orchestrator    rules
    ${result}=    Orchestrator File Under Limit    rules.py    50
    Should Be True    ${result}[exists]    rules.py must exist
    Should Be True    ${result}[under_limit]    rules.py has ${result}[lines] lines, should be <50

Sessions Orchestrator Under 50 Lines
    [Documentation]    sessions.py must be a thin orchestrator
    [Tags]    unit    mcp    orchestrator    sessions
    ${result}=    Orchestrator File Under Limit    sessions.py    50
    Should Be True    ${result}[exists]    sessions.py must exist
    Should Be True    ${result}[under_limit]    sessions.py has ${result}[lines] lines, should be <50

Tasks Orchestrator Under 50 Lines
    [Documentation]    tasks.py must be a thin orchestrator
    [Tags]    unit    mcp    orchestrator    tasks
    ${result}=    Orchestrator File Under Limit    tasks.py    50
    Should Be True    ${result}[exists]    tasks.py must exist
    Should Be True    ${result}[under_limit]    tasks.py has ${result}[lines] lines, should be <50

Split Module Files Exist
    [Documentation]    Split module files must exist
    [Tags]    unit    mcp    modules    existence
    ${result}=    Split Modules Exist
    Should Be True    ${result}[all_exist]    Missing: ${result}[missing]

Split Modules Under 315 Lines
    [Documentation]    Split modules must be under 315 lines per RULE-032
    [Tags]    unit    mcp    modules    doc-size
    ${result}=    Split Modules Under 315 Lines
    Should Be True    ${result}[all_under_limit]    Over limit: ${result}[over_limit]
