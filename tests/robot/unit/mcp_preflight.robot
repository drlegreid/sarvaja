*** Settings ***
Documentation    RF-004: Unit Tests - MCP Pre-flight Validation
...              Migrated from tests/unit/test_mcp_preflight.py
...              Per GAP-CONTEXT-EFFICIENCY-001, TACTIC-2-C: Test duplicate tools
Library          Collections
Library          ../../libs/MCPPreflightLibrary.py
Force Tags        unit    mcp    preflight    critical    ARCH-INFRA-01-v1    validate

*** Test Cases ***
# =============================================================================
# MCPPreflightChecker Tests
# =============================================================================

Checker Initializes With Project Root
    [Documentation]    GIVEN MCPPreflightChecker WHEN initializing THEN project root is set
    [Tags]    unit    mcp    validate    hooks
    ${result}=    Checker Initializes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Hooks not available
    Should Be True    ${result}[project_root_matches]

No Duplicate Tool Registrations
    [Documentation]    GIVEN MCP modules WHEN scanning THEN no duplicate tools
    [Tags]    unit    mcp    validate    hooks    critical
    ${result}=    Find Duplicate Tools
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Hooks not available
    Should Be True    ${result}[no_duplicates]    Found duplicates: ${result}[duplicates]

Module Syntax Is Valid
    [Documentation]    GIVEN MCP modules WHEN checking syntax THEN no errors
    [Tags]    unit    mcp    validate    hooks
    ${result}=    Check Module Syntax
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Hooks not available
    Should Be True    ${result}[no_errors]    Found errors: ${result}[errors]

Preflight Check Passes
    [Documentation]    GIVEN full pre-flight WHEN running THEN passes
    [Tags]    unit    mcp    validate    hooks    critical
    ${result}=    Preflight Check Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Hooks not available
    Should Be True    ${result}[success]    ${result}[message]

Tool Extraction From File
    [Documentation]    GIVEN Python file with tools WHEN extracting THEN tools found
    [Tags]    unit    mcp    validate    hooks
    ${result}=    Tool Extraction From File
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Hooks not available
    Should Be True    ${result}[has_decorated_tool]
    Should Be True    ${result}[has_convention_tool]
    Should Be True    ${result}[excludes_regular]

Duplicate Detection Across Files
    [Documentation]    GIVEN duplicate tools WHEN scanning THEN detected
    [Tags]    unit    mcp    validate    hooks
    ${result}=    Duplicate Detection
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Hooks not available
    Should Be True    ${result}[detected_duplicate]
    Should Be Equal As Integers    ${result}[file_count]    2

# =============================================================================
# Integration Tests
# =============================================================================

All MCP Modules Exist
    [Documentation]    GIVEN configured modules WHEN checking THEN all exist
    [Tags]    unit    mcp    validate    hooks    integration
    ${result}=    All Mcp Modules Exist
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Hooks not available
    Should Be True    ${result}[no_critical_missing]    Missing: ${result}[critical_missing]

Tool Count Is Reasonable
    [Documentation]    GIVEN MCP modules WHEN counting tools THEN reasonable count
    [Tags]    unit    mcp    validate    hooks    integration
    ${result}=    Tool Count Reasonable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Hooks not available
    Should Be True    ${result}[has_tools]    No tools found
    Should Be True    ${result}[count_reasonable]    Too many tools: ${result}[tool_count]

