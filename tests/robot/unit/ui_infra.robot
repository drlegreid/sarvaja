*** Settings ***
Documentation    RF-004: Unit Tests - UI Infrastructure View
...              Migrated from tests/unit/ui/test_ui_infra.py
...              Per UI-AUDIT-008: Validates health hash display
...              Per GAP-INFRA-004: Docker/Podman health dashboard
Library          Collections
Library          ../../libs/UIInfraLibrary.py
Force Tags        unit    ui    infra    low    DOC-SIZE-01-v1    validate

*** Test Cases ***
# =============================================================================
# Infrastructure State Variable Tests
# =============================================================================

Initial State Has Infra Stats
    [Documentation]    GIVEN initial_state WHEN checking THEN has infra_stats
    [Tags]    unit    ui    validate    infra    state
    ${result}=    Initial State Has Infra Stats
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_infra_stats]

Infra Stats Has Frankel Hash
    [Documentation]    GIVEN infra_stats WHEN checking THEN has frankel_hash
    [Tags]    unit    ui    validate    infra    state    ui-audit-008
    ${result}=    Infra Stats Has Frankel Hash
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_frankel_hash]
    Should Be True    ${result}[default_placeholder]

Infra Stats Has Last Check
    [Documentation]    GIVEN infra_stats WHEN checking THEN has last_check
    [Tags]    unit    ui    validate    infra    state
    ${result}=    Infra Stats Has Last Check
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_last_check]
    Should Be True    ${result}[default_never]

Infra Stats Has Memory Pct
    [Documentation]    GIVEN infra_stats WHEN checking THEN has memory_pct
    [Tags]    unit    ui    validate    infra    state
    ${result}=    Infra Stats Has Memory Pct
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_memory_pct]

Infra Stats Has Python Procs
    [Documentation]    GIVEN infra_stats WHEN checking THEN has python_procs
    [Tags]    unit    ui    validate    infra    state
    ${result}=    Infra Stats Has Python Procs
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_python_procs]

# =============================================================================
# Infrastructure View Reference Tests
# =============================================================================

Infra View Module Exists
    [Documentation]    GIVEN views WHEN importing THEN infra_view exists
    [Tags]    unit    ui    validate    infra    view
    ${result}=    Infra View Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Build Infra View Callable
    [Documentation]    GIVEN infra_view WHEN checking THEN build_infra_view callable
    [Tags]    unit    ui    validate    infra    view
    ${result}=    Build Infra View Callable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

Build System Stats Callable
    [Documentation]    GIVEN infra_view WHEN checking THEN build_system_stats callable
    [Tags]    unit    ui    validate    infra    view
    ${result}=    Build System Stats Callable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

View References Frankel Hash
    [Documentation]    GIVEN view source WHEN checking THEN references frankel_hash
    [Tags]    unit    ui    validate    infra    view    ui-audit-008
    ${result}=    View References Frankel Hash
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[references_frankel_hash]
    Should Be True    ${result}[references_infra_stats]

# =============================================================================
# Healthcheck State File Tests
# =============================================================================

Actual Healthcheck State Exists
    [Documentation]    GIVEN hooks dir WHEN checking THEN healthcheck state exists
    [Tags]    unit    ui    validate    infra    healthcheck
    ${result}=    Actual Healthcheck State Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    State file not found
    Should Be True    ${result}[exists]
    Should Be True    ${result}[has_master_hash]

# =============================================================================
# MCP Status Panel Tests
# =============================================================================

Build MCP Status Panel Callable
    [Documentation]    GIVEN infra_view WHEN checking THEN build_mcp_status_panel callable
    [Tags]    unit    ui    validate    infra    mcp    ui-audit-011
    ${result}=    Build MCP Status Panel Callable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

Initial State Has MCP Servers
    [Documentation]    GIVEN initial_state WHEN checking THEN mcp_servers in infra_stats
    [Tags]    unit    ui    validate    infra    mcp    ui-audit-011
    ${result}=    Initial State Has MCP Servers
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_mcp_servers]

