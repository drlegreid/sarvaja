*** Settings ***
Documentation    RF-004: Unit Tests - MCP Output Format
...              Migrated from tests/unit/test_mcp_output.py
...              Per GAP-DATA-001: TOON format implementation
Library          Collections
Library          ../../libs/MCPOutputLibrary.py
Force Tags        unit    mcp    output    medium    ARCH-MCP-02-v1    validate

*** Test Cases ***
# =============================================================================
# OutputFormat Tests
# =============================================================================

Output Format Enum Values
    [Documentation]    GIVEN OutputFormat WHEN checking values THEN expected
    [Tags]    unit    mcp    validate    output
    ${result}=    Output Format Values
    Should Be Equal    ${result}[json]    json
    Should Be Equal    ${result}[toon]    toon
    Should Be Equal    ${result}[auto]    auto

# =============================================================================
# format_output Tests
# =============================================================================

Format Output JSON Default
    [Documentation]    GIVEN data WHEN format as JSON THEN valid JSON
    [Tags]    unit    mcp    validate    output
    ${result}=    Format Output Json Default
    Should Be True    ${result}[valid_json]
    Should Be True    ${result}[data_matches]

Format Output Handles Nested
    [Documentation]    GIVEN nested data WHEN formatting THEN preserved
    [Tags]    unit    mcp    validate    output
    ${result}=    Format Output Handles Nested
    Should Be Equal As Integers    ${result}[summary_total]    50
    Should Be Equal As Integers    ${result}[items_count]    2

Format Output Handles Datetime
    [Documentation]    GIVEN datetime WHEN formatting THEN serialized
    [Tags]    unit    mcp    validate    output
    ${result}=    Format Output Handles Datetime
    Should Be True    ${result}[no_error]
    Should Be True    ${result}[contains_year]

# =============================================================================
# parse_input Tests
# =============================================================================

Parse Input JSON
    [Documentation]    GIVEN JSON string WHEN parsing THEN dict returned
    [Tags]    unit    mcp    validate    output
    ${result}=    Parse Input Json
    Should Be Equal As Integers    ${result}[rules]    50
    Should Be True    ${result}[is_dict]

Parse Input Auto Tries JSON First
    [Documentation]    GIVEN AUTO format WHEN parsing JSON THEN succeeds
    [Tags]    unit    mcp    validate    output
    ${result}=    Parse Input Auto Tries Json First
    Should Be Equal As Integers    ${result}[rules]    50
    Should Be True    ${result}[is_dict]

Parse Input Invalid JSON Raises
    [Documentation]    GIVEN invalid JSON WHEN parsing THEN raises error
    [Tags]    unit    mcp    validate    output
    ${result}=    Parse Input Invalid Json Raises
    Should Be True    ${result}[raised_error]

# =============================================================================
# estimate_token_savings Tests
# =============================================================================

Estimate Token Savings Returns Fields
    [Documentation]    GIVEN data WHEN estimating THEN returns fields
    [Tags]    unit    mcp    validate    output
    ${result}=    Estimate Token Savings
    Should Be True    ${result}[has_json_chars]
    Should Be True    ${result}[json_chars_positive]
    Should Be True    ${result}[has_toon_available]

# =============================================================================
# TOON Integration Tests
# =============================================================================

TOON Format Output
    [Documentation]    GIVEN data WHEN TOON format THEN shorter
    [Tags]    unit    mcp    validate    output    toon
    ${result}=    Toon Format Output
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    toons not installed
    Should Be True    ${result}[toon_shorter_or_equal]

TOON Roundtrip
    [Documentation]    GIVEN data WHEN encode/decode THEN preserved
    [Tags]    unit    mcp    validate    output    toon
    ${result}=    Toon Roundtrip
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    toons not installed
    Should Be True    ${result}[roundtrip_successful]

Estimate Shows Savings
    [Documentation]    GIVEN large data WHEN estimating THEN shows savings
    [Tags]    unit    mcp    validate    output    toon
    ${result}=    Estimate Shows Savings
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    toons not installed
    Should Be True    ${result}[toon_available]
    Should Be True    ${result}[toon_smaller]

# =============================================================================
# Fallback Behavior Tests
# =============================================================================

TOON Format Fallback To JSON
    [Documentation]    GIVEN toons unavailable WHEN TOON format THEN JSON fallback
    [Tags]    unit    mcp    validate    output    fallback
    ${result}=    Toon Format Fallback To Json
    Should Be True    ${result}[valid_json]
    Should Be True    ${result}[data_matches]

# =============================================================================
# MCP Tool Helper Tests
# =============================================================================

Format MCP Result Exists
    [Documentation]    GIVEN common module WHEN importing THEN function exists
    [Tags]    unit    mcp    validate    output
    ${result}=    Format Mcp Result Exists
    Should Be True    ${result}[callable]

Format MCP Result JSON Explicit
    [Documentation]    GIVEN JSON env WHEN formatting THEN JSON output
    [Tags]    unit    mcp    validate    output
    ${result}=    Format Mcp Result Json Explicit
    Should Be True    ${result}[valid_json]
    Should Be True    ${result}[data_matches]

Format MCP Result Handles Datetime
    [Documentation]    GIVEN datetime WHEN formatting THEN serialized
    [Tags]    unit    mcp    validate    output
    ${result}=    Format Mcp Result Handles Datetime
    Should Be True    ${result}[contains_year]

Format MCP Result With List
    [Documentation]    GIVEN list WHEN formatting THEN list preserved
    [Tags]    unit    mcp    validate    output
    ${result}=    Format Mcp Result With List
    Should Be Equal As Integers    ${result}[list_length]    2
    Should Be Equal    ${result}[first_id]    GAP-001

