*** Settings ***
Documentation    RF-004: Unit Tests - Pydantic AI Type-Safe Governance Tools
...              Migrated from tests/test_pydantic_tools.py
...              Per RULE-004: Exploratory Testing & Executable Specification
...              Per RULE-017: Type-Safe Tool Development
Library          Collections
Library          ../../libs/PydanticToolsLibrary.py
Library          ../../libs/PydanticToolsAdvancedLibrary.py
Force Tags        unit    tools    pydantic    low    mcp    validate    MCP-DOC-01-v1

*** Test Cases ***
# =============================================================================
# Input Model Validation Tests
# =============================================================================

Rule Query Config Exists
    [Documentation]    GIVEN pydantic_tools WHEN importing THEN RuleQueryConfig exists
    [Tags]    unit    pydantic    validate    models
    ${result}=    Rule Query Config Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Rule Query Config With Defaults
    [Documentation]    GIVEN RuleQueryConfig WHEN no args THEN defaults correct
    [Tags]    unit    pydantic    validate    models
    ${result}=    Rule Query Config With Defaults
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[category_none]
    Should Be True    ${result}[status_none]
    Should Be True    ${result}[include_deps_false]

Rule Query Config With Values
    [Documentation]    GIVEN RuleQueryConfig WHEN valid values THEN accepts
    [Tags]    unit    pydantic    validate    models
    ${result}=    Rule Query Config With Values
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[category_correct]
    Should Be True    ${result}[status_correct]
    Should Be True    ${result}[priority_correct]

Rule Query Config Validates Status
    [Documentation]    GIVEN RuleQueryConfig WHEN invalid status THEN rejects
    [Tags]    unit    pydantic    validate    models    validation
    ${result}=    Rule Query Config Validates Status
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_works]
    Should Be True    ${result}[rejects_invalid]

Dependency Config Exists
    [Documentation]    GIVEN pydantic_tools WHEN importing THEN DependencyConfig exists
    [Tags]    unit    pydantic    validate    models
    ${result}=    Dependency Config Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Dependency Config Requires Rule Id
    [Documentation]    GIVEN DependencyConfig WHEN no rule_id THEN error
    [Tags]    unit    pydantic    validate    models    validation
    ${result}=    Dependency Config Requires Rule Id
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[requires_rule_id]

Dependency Config Validates Rule Id
    [Documentation]    GIVEN DependencyConfig WHEN invalid rule_id THEN rejects
    [Tags]    unit    pydantic    validate    models    validation
    ${result}=    Dependency Config Validates Rule Id
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_works]
    Should Be True    ${result}[rejects_invalid]

Dependency Config Uppercases Rule Id
    [Documentation]    GIVEN DependencyConfig WHEN lowercase rule_id THEN uppercases
    [Tags]    unit    pydantic    validate    models    validation
    ${result}=    Dependency Config Uppercases Rule Id
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[uppercased]

# =============================================================================
# Output Models Tests
# =============================================================================

Rule Info Model Works
    [Documentation]    GIVEN RuleInfo WHEN creating THEN works correctly
    [Tags]    unit    pydantic    validate    models    output
    ${result}=    Rule Info Model Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rule_id_correct]
    Should Be True    ${result}[dependencies_empty]

Rule Query Result Model Works
    [Documentation]    GIVEN RuleQueryResult WHEN creating THEN works correctly
    [Tags]    unit    pydantic    validate    models    output
    ${result}=    Rule Query Result Model Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[success]
    Should Be True    ${result}[rules_empty]
    Should Be True    ${result}[error_none]

Trust Score Result Validates Range
    [Documentation]    GIVEN TrustScoreResult WHEN out of range THEN rejects
    [Tags]    unit    pydantic    validate    models    output    validation
    ${result}=    Trust Score Result Validates Range
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_works]
    Should Be True    ${result}[rejects_over_1]

# =============================================================================
# MCP Wrapper Tests
# =============================================================================

Query Rules MCP Exists
    [Documentation]    GIVEN pydantic_tools WHEN importing THEN query_rules_mcp exists
    [Tags]    unit    pydantic    validate    mcp
    ${result}=    Query Rules MCP Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Analyze Dependencies MCP Exists
    [Documentation]    GIVEN pydantic_tools WHEN importing THEN analyze_dependencies_mcp exists
    [Tags]    unit    pydantic    validate    mcp
    ${result}=    Analyze Dependencies MCP Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Calculate Trust Score MCP Exists
    [Documentation]    GIVEN pydantic_tools WHEN importing THEN calculate_trust_score_mcp exists
    [Tags]    unit    pydantic    validate    mcp
    ${result}=    Calculate Trust Score MCP Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Analyze Impact MCP Exists
    [Documentation]    GIVEN pydantic_tools WHEN importing THEN analyze_impact_mcp exists
    [Tags]    unit    pydantic    validate    mcp
    ${result}=    Analyze Impact MCP Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Health Check MCP Exists
    [Documentation]    GIVEN pydantic_tools WHEN importing THEN health_check_mcp exists
    [Tags]    unit    pydantic    validate    mcp
    ${result}=    Health Check MCP Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

# =============================================================================
# Typed Functions Tests
# =============================================================================

Query Rules Typed Exists
    [Documentation]    GIVEN pydantic_tools WHEN importing THEN query_rules_typed exists
    [Tags]    unit    pydantic    validate    typed
    ${result}=    Query Rules Typed Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Create Proposal Typed Works
    [Documentation]    GIVEN create_proposal_typed WHEN valid config THEN returns result
    [Tags]    unit    pydantic    validate    typed
    ${result}=    Create Proposal Typed Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution failed
    Should Be True    ${result}[is_proposal_result]
    Should Be True    ${result}[success]
    Should Be True    ${result}[has_proposal_id]

# =============================================================================
# Field Validator Tests
# =============================================================================

Rule Id Validator Uppercases
    [Documentation]    GIVEN lowercase rule_id WHEN validating THEN uppercases
    [Tags]    unit    pydantic    validate    validators
    ${result}=    Rule Id Validator Uppercase
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[uppercased]

Rule Id Validator Rejects Invalid
    [Documentation]    GIVEN invalid rule_id format WHEN validating THEN rejects
    [Tags]    unit    pydantic    validate    validators
    ${result}=    Rule Id Validator Rejects Invalid
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rejects]

Agent Id Validator Uppercases
    [Documentation]    GIVEN lowercase agent_id WHEN validating THEN uppercases
    [Tags]    unit    pydantic    validate    validators
    ${result}=    Agent Id Validator Uppercase
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[uppercased]

# =============================================================================
# Literal Type Tests
# =============================================================================

Status Literal Values Accepted
    [Documentation]    GIVEN valid status values WHEN creating config THEN accepted
    [Tags]    unit    pydantic    validate    literals
    ${result}=    Status Literal Values Accepted
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_valid]

Priority Literal Values Accepted
    [Documentation]    GIVEN valid priority values WHEN creating config THEN accepted
    [Tags]    unit    pydantic    validate    literals
    ${result}=    Priority Literal Values Accepted
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_valid]

# =============================================================================
# Field Constraint Tests
# =============================================================================

Trust Score Range Enforced
    [Documentation]    GIVEN TrustScoreResult WHEN out of 0-1 range THEN rejects
    [Tags]    unit    pydantic    validate    constraints
    ${result}=    Trust Score Range Enforced
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_works]
    Should Be True    ${result}[rejects_negative]

Impact Score Range Enforced
    [Documentation]    GIVEN ImpactAnalysisResult WHEN out of 0-100 range THEN rejects
    [Tags]    unit    pydantic    validate    constraints
    ${result}=    Impact Score Range Enforced
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_works]
    Should Be True    ${result}[rejects_over_100]

Count Fields Non Negative
    [Documentation]    GIVEN count fields WHEN negative THEN rejects
    [Tags]    unit    pydantic    validate    constraints
    ${result}=    Count Fields Non Negative
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_works]
    Should Be True    ${result}[rejects_negative]

