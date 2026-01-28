*** Settings ***
Documentation    RF-004: Unit Tests - MCP Server Configuration
...              Migrated from tests/test_mcp_server_config.py
...              Per RULE-023: Test Before Ship
...              Per ARCH-MCP-02-v1: MCP Split Architecture
Library          Collections
Library          ../../libs/MCPServerConfigLibrary.py
Force Tags        unit    mcp    config    medium    ARCH-INFRA-01-v1    validate

*** Test Cases ***
# =============================================================================
# MCP Server Config Tests
# =============================================================================

MCP JSON Exists
    [Documentation]    GIVEN project WHEN checking THEN .mcp.json exists
    [Tags]    unit    mcp    validate    config
    ${result}=    MCP JSON Exists
    Should Be True    ${result}[exists]

MCP JSON Valid JSON
    [Documentation]    GIVEN .mcp.json WHEN parsing THEN valid JSON
    [Tags]    unit    mcp    validate    config
    ${result}=    MCP JSON Valid JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    .mcp.json not found
    Should Be True    ${result}[valid]
    Should Be True    ${result}[has_mcp_servers]

Split Servers Defined
    [Documentation]    GIVEN .mcp.json WHEN checking THEN all 4 servers defined
    [Tags]    unit    mcp    validate    config    split
    ${result}=    Split Servers Defined
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    .mcp.json not found
    Should Be True    ${result}[has_gov_core]
    Should Be True    ${result}[has_gov_agents]
    Should Be True    ${result}[has_gov_sessions]
    Should Be True    ${result}[has_gov_tasks]
    Should Be True    ${result}[all_defined]

Monolith Removed
    [Documentation]    GIVEN .mcp.json WHEN checking THEN governance monolith removed
    [Tags]    unit    mcp    validate    config    split
    ${result}=    Monolith Removed
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    .mcp.json not found
    Should Be True    ${result}[monolith_removed]

Each Server Has Required Fields
    [Documentation]    GIVEN servers WHEN checking THEN all have required fields
    [Tags]    unit    mcp    validate    config    split
    ${result}=    Each Server Has Required Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Config not accessible
    Should Be True    ${result}[all_valid]

