*** Settings ***
Documentation    RF-004: Unit Tests - Agents Module Split
...              Migrated from tests/test_agents_split.py
...              Per GAP-FILE-028: routes/agents.py split
Library          Collections
Library          ../../libs/AgentsSplitLibrary.py
Force Tags        unit    agents    split    medium    DOC-SIZE-01-v1    agent    validate

*** Test Cases ***
# =============================================================================
# Module Structure Tests
# =============================================================================

Agents Module Exists
    [Documentation]    GIVEN routes dir WHEN checking THEN agents module exists
    [Tags]    unit    agents    split    module
    ${result}=    Agents Module Exists
    Should Be True    ${result}[exists]

Agents Under 300 Lines
    [Documentation]    GIVEN agents module WHEN checking THEN under 300 lines
    [Tags]    unit    agents    split    size
    ${result}=    Agents Under 300 Lines
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    agents module not found
    Should Be True    ${result}[under_300]

Observability Module Exists
    [Documentation]    GIVEN routes dir WHEN checking THEN observability.py exists
    [Tags]    unit    agents    split    observability
    ${result}=    Observability Module Exists
    Should Be True    ${result}[exists]

Visibility Module Exists
    [Documentation]    GIVEN routes dir WHEN checking THEN visibility.py exists
    [Tags]    unit    agents    split    visibility
    ${result}=    Visibility Module Exists
    Should Be True    ${result}[exists]

# =============================================================================
# Backward Compatibility Tests
# =============================================================================

Import Router From Agents
    [Documentation]    GIVEN agents module WHEN import router THEN succeeds
    [Tags]    unit    agents    split    import
    ${result}=    Import Router From Agents
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Router Has Agents Routes
    [Documentation]    GIVEN agents router WHEN checking THEN has /agents routes
    [Tags]    unit    agents    split    routes
    ${result}=    Router Has Agents Routes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_agents]

# =============================================================================
# Module Function Tests
# =============================================================================

Observability Has Status Route
    [Documentation]    GIVEN observability module WHEN checking THEN has status route
    [Tags]    unit    agents    split    status
    ${result}=    Observability Has Status Route
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Observability module not yet split
    Should Be True    ${result}[has_status]

Visibility Has Visibility Route
    [Documentation]    GIVEN visibility module WHEN checking THEN has visibility route
    [Tags]    unit    agents    split    visibility
    ${result}=    Visibility Has Visibility Route
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Visibility module not yet split
    Should Be True    ${result}[has_visibility]
