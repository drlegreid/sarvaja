*** Settings ***
Documentation    RF-004: Unit Tests - Portable Configuration
...              Migrated from tests/test_portable_config.py
...              Per RULE-040: Portable Configuration Patterns
Library          Collections
Library          ../../libs/PortableConfigLibrary.py
Force Tags        unit    config    portable    low    validate    ARCH-INFRA-02-v1

*** Test Cases ***
# =============================================================================
# Shell Script Tests
# =============================================================================

Scripts Have LF Line Endings
    [Documentation]    GIVEN scripts/*.sh WHEN check THEN LF line endings
    [Tags]    unit    config    portable    scripts    eol
    ${result}=    Scripts Have LF Line Endings
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No scripts directory
    Should Be True    ${result}[no_crlf]

# =============================================================================
# MCP Config Tests
# =============================================================================

MCP Config No Absolute Home Paths
    [Documentation]    GIVEN .mcp.json WHEN check THEN no hardcoded paths
    [Tags]    unit    config    portable    mcp    paths
    ${result}=    MCP Config No Absolute Home Paths
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No .mcp.json found
    Should Be True    ${result}[no_linux_paths]
    Should Be True    ${result}[no_windows_paths]

MCP Runner Script Exists
    [Documentation]    GIVEN scripts/ WHEN check THEN mcp-runner.sh exists
    [Tags]    unit    config    portable    mcp    runner
    ${result}=    MCP Runner Script Exists
    Should Be True    ${result}[exists]

MCP Runner Uses Home Variable
    [Documentation]    GIVEN mcp-runner.sh WHEN check THEN uses $HOME
    [Tags]    unit    config    portable    mcp    home
    ${result}=    MCP Runner Uses Home Variable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No mcp-runner.sh
    Should Be True    ${result}[uses_home]

MCP Runner Sets PYTHONPATH
    [Documentation]    GIVEN mcp-runner.sh WHEN check THEN sets PYTHONPATH
    [Tags]    unit    config    portable    mcp    pythonpath
    ${result}=    MCP Runner Sets PYTHONPATH
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No mcp-runner.sh
    Should Be True    ${result}[sets_pythonpath]

MCP Config Uses Workspace Folder
    [Documentation]    GIVEN .mcp.json WHEN check THEN uses ${workspaceFolder}
    [Tags]    unit    config    portable    mcp    workspace
    ${result}=    MCP Config Uses Workspace Folder
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No .mcp.json found
    Should Be True    ${result}[uses_workspace_folder]

# =============================================================================
# Venv Portability Tests
# =============================================================================

Venv Activation Conditional
    [Documentation]    GIVEN mcp-runner.sh WHEN check THEN conditional venv
    [Tags]    unit    config    portable    venv    conditional
    ${result}=    Venv Activation Conditional
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No mcp-runner.sh
    Should Be True    ${result}[conditional]
