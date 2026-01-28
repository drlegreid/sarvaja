*** Settings ***
Documentation    RF-004: Unit Tests - MCP Status Display
...              Migrated from tests/unit/test_mcp_status_display.py
...              Per UI-AUDIT-011: MCP process status in Infrastructure view
Library          Collections
Library          ../../libs/MCPStatusDisplayLibrary.py
Force Tags        unit    mcp    status    medium    read    SAFETY-HEALTH-01-v1

*** Test Cases ***
# =============================================================================
# MCP Panel in Infra View Tests
# =============================================================================

MCP Panel In Infra View
    [Documentation]    GIVEN infra view WHEN checking THEN MCP panel called
    [Tags]    unit    ui    validate    mcp    infra
    ${result}=    Mcp Panel In Infra View
    Should Be True    ${result}[panel_called]

MCP Panel Function Exists
    [Documentation]    GIVEN infra_view module WHEN checking THEN function exists
    [Tags]    unit    ui    validate    mcp    infra
    ${result}=    Mcp Panel Function Exists
    Should Be True    ${result}[callable]

MCP Testid In Panel
    [Documentation]    GIVEN MCP panel WHEN checking THEN has testid
    [Tags]    unit    ui    validate    mcp    infra
    ${result}=    Mcp Testid In Panel
    Should Be True    ${result}[has_testid]

# =============================================================================
# MCP Status Data Loader Tests
# =============================================================================

MCP Servers In Stats Init
    [Documentation]    GIVEN data_loaders WHEN checking THEN mcp_servers initialized
    [Tags]    unit    ui    validate    mcp    data
    ${result}=    Mcp Servers In Stats Init
    Should Be True    ${result}[has_mcp_servers]

MCP Names Extracted
    [Documentation]    GIVEN data_loaders WHEN checking THEN known MCP names
    [Tags]    unit    ui    validate    mcp    data
    ${result}=    Mcp Names Extracted
    Should Be True    ${result}[has_claude_mem]

Healthcheck State File Exists
    [Documentation]    GIVEN healthcheck state WHEN checking THEN file exists
    [Tags]    unit    ui    validate    mcp    data
    ${result}=    Healthcheck State File Exists
    Should Be True    ${result}[exists]    File not found: ${result}[path]

Healthcheck State Has Components
    [Documentation]    GIVEN healthcheck state WHEN reading THEN has components
    [Tags]    unit    ui    validate    mcp    data
    ${result}=    Healthcheck State Has Components
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    State file not found
    Should Be True    ${result}[has_components]

# =============================================================================
# MCP Status UI Binding Tests
# =============================================================================

Infra Stats MCP Servers Used In View
    [Documentation]    GIVEN infra view WHEN checking THEN mcp_servers used
    [Tags]    unit    ui    validate    mcp    binding
    ${result}=    Infra Stats Mcp Servers Used In View
    Should Be True    ${result}[has_mcp_servers]

