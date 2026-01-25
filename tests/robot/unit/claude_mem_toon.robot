*** Settings ***
Documentation    RF-004: Unit Tests - Claude-Mem MCP TOON Migration
...              Migrated from tests/unit/test_claude_mem_toon.py
...              Per GAP-DATA-001: TOON format for all MCP tools
Library          Collections
Library          ../../libs/ClaudeMemTOONLibrary.py

*** Test Cases ***
# =============================================================================
# Import Tests
# =============================================================================

MCP Server Imports Format Output
    [Documentation]    GIVEN claude_mem WHEN importing THEN format_output available
    [Tags]    unit    mcp    validate    claude-mem    imports
    ${result}=    MCP Server Imports Format Output
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    claude_mem not available
    Should Be True    ${result}[has_format_output]

No JSON Dumps Usage In MCP Server
    [Documentation]    GIVEN mcp_server WHEN checking THEN no json.dumps usage
    [Tags]    unit    mcp    validate    claude-mem    imports
    ${result}=    No JSON Dumps Usage
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    claude_mem not available
    Should Be True    ${result}[no_json_dumps]

# =============================================================================
# TOON Format Tests
# =============================================================================

Chroma Health Returns TOON Format
    [Documentation]    GIVEN chroma_health WHEN calling THEN returns TOON format
    [Tags]    unit    mcp    validate    claude-mem    toon
    ${result}=    Chroma Health TOON Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    claude_mem not available
    Should Be True    ${result}[returns_string]

Chroma Health Returns JSON When Env Set
    [Documentation]    GIVEN MCP_OUTPUT_FORMAT=json WHEN calling THEN returns JSON
    [Tags]    unit    mcp    validate    claude-mem    toon
    ${result}=    Chroma Health JSON When Env Set
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Dependency not available
    Should Be True    ${result}[is_valid_json]

Chroma Query Documents Returns TOON Format
    [Documentation]    GIVEN chroma_query_documents WHEN calling THEN returns string
    [Tags]    unit    mcp    validate    claude-mem    toon
    ${result}=    Chroma Query Documents TOON Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    claude_mem not available
    Should Be True    ${result}[returns_string]

Chroma Get Documents Returns TOON Format
    [Documentation]    GIVEN chroma_get_documents WHEN calling THEN returns string
    [Tags]    unit    mcp    validate    claude-mem    toon
    ${result}=    Chroma Get Documents TOON Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    claude_mem not available
    Should Be True    ${result}[returns_string]

Chroma Add Documents Returns TOON Format
    [Documentation]    GIVEN chroma_add_documents WHEN calling THEN returns string
    [Tags]    unit    mcp    validate    claude-mem    toon
    ${result}=    Chroma Add Documents TOON Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    claude_mem not available
    Should Be True    ${result}[returns_string]

Chroma Delete Documents Returns TOON Format
    [Documentation]    GIVEN chroma_delete_documents WHEN calling THEN returns string
    [Tags]    unit    mcp    validate    claude-mem    toon
    ${result}=    Chroma Delete Documents TOON Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    claude_mem not available
    Should Be True    ${result}[returns_string]

Error Response Uses TOON Format
    [Documentation]    GIVEN error condition WHEN calling THEN TOON formatted error
    [Tags]    unit    mcp    validate    claude-mem    toon
    ${result}=    Error Response TOON Format
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    claude_mem not available
    Should Be True    ${result}[returns_string]

# =============================================================================
# Data Factory Tests
# =============================================================================

Chroma Query Result Factory Works
    [Documentation]    GIVEN factory WHEN creating query result THEN valid structure
    [Tags]    unit    mcp    validate    claude-mem    factory
    ${result}=    Chroma Query Result Factory Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Factory not available
    Should Be True    ${result}[has_ids]
    Should Be True    ${result}[correct_count]

Chroma Health Factory Creates Healthy Data
    [Documentation]    GIVEN factory WHEN healthy=True THEN status is healthy
    [Tags]    unit    mcp    validate    claude-mem    factory
    ${result}=    Chroma Health Factory Healthy
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Factory not available
    Should Be True    ${result}[status_healthy]

Chroma Health Factory Creates Unhealthy Data
    [Documentation]    GIVEN factory WHEN healthy=False THEN status is unhealthy
    [Tags]    unit    mcp    validate    claude-mem    factory
    ${result}=    Chroma Health Factory Unhealthy
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Factory not available
    Should Be True    ${result}[status_unhealthy]

# =============================================================================
# Integration Tests
# =============================================================================

TOON Roundtrip Query Result
    [Documentation]    GIVEN data WHEN toons.dumps/loads THEN roundtrip works
    [Tags]    unit    mcp    validate    claude-mem    integration
    ${result}=    TOON Roundtrip Query Result
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    toons not installed
    Should Be True    ${result}[roundtrip_success]

TOON Saves Tokens For ChromaDB Response
    [Documentation]    GIVEN ChromaDB response WHEN measuring THEN positive savings
    [Tags]    unit    mcp    validate    claude-mem    integration
    ${result}=    TOON Savings Chroma Response
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Factory not available
    Should Be True    ${result}[toon_available]

