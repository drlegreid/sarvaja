*** Settings ***
Documentation    RF-004: Unit Tests - Rules Curator Agent
...              Migrated from tests/test_curator_agent.py
...              Per ORCH-005: Rules curator agent
Library          Collections
Library          ../../libs/CuratorAgentLibrary.py
Library          ../../libs/CuratorAgentAdvancedLibrary.py
Force Tags        unit    agents    curator    medium    agent    validate    GOV-RULE-01-v1

*** Test Cases ***
# =============================================================================
# Import Tests
# =============================================================================

Import Rules Curator Agent
    [Documentation]    GIVEN curator module WHEN importing THEN RulesCuratorAgent available
    [Tags]    unit    curator    import    agent
    ${result}=    Import Rules Curator Agent
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Curation Action Enum
    [Documentation]    GIVEN curator module WHEN importing THEN CurationAction enum correct
    [Tags]    unit    curator    import    enum
    ${result}=    Import Curation Action Enum
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[analyze_correct]
    Should Be True    ${result}[resolve_correct]
    Should Be True    ${result}[find_correct]

Import Issue Severity Enum
    [Documentation]    GIVEN curator module WHEN importing THEN IssueSeverity enum correct
    [Tags]    unit    curator    import    enum
    ${result}=    Import Issue Severity Enum
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[critical_correct]
    Should Be True    ${result}[high_correct]
    Should Be True    ${result}[medium_correct]
    Should Be True    ${result}[low_correct]

Import Curation Result Dataclass
    [Documentation]    GIVEN curator module WHEN importing THEN CurationResult works
    [Tags]    unit    curator    import    dataclass
    ${result}=    Import Curation Result Dataclass
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[success_true]
    Should Be True    ${result}[action_correct]

Import Rule Issue Dataclass
    [Documentation]    GIVEN curator module WHEN importing THEN RuleIssue works
    [Tags]    unit    curator    import    dataclass
    ${result}=    Import Rule Issue Dataclass
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rule_id_correct]
    Should Be True    ${result}[resolved_false]

Import Create Curator Agent Factory
    [Documentation]    GIVEN curator module WHEN importing THEN factory works
    [Tags]    unit    curator    import    factory
    ${result}=    Import Create Curator Agent Factory
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]

# =============================================================================
# Agent Info Tests
# =============================================================================

Curator Agent Has Correct ID
    [Documentation]    GIVEN RulesCuratorAgent WHEN checking THEN ID correct
    [Tags]    unit    curator    agent    id
    ${result}=    Curator Agent Has Correct ID
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]

Curator Agent Has Correct Name
    [Documentation]    GIVEN RulesCuratorAgent WHEN checking THEN name correct
    [Tags]    unit    curator    agent    name
    ${result}=    Curator Agent Has Correct Name
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[name_correct]

Curator Agent Has Correct Trust Score
    [Documentation]    GIVEN RulesCuratorAgent WHEN checking THEN trust score correct
    [Tags]    unit    curator    agent    trust
    ${result}=    Curator Agent Has Correct Trust Score
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[trust_correct]

Curator Agent Get Info Returns Agent Info
    [Documentation]    GIVEN curator WHEN get_agent_info THEN returns correct info
    [Tags]    unit    curator    agent    info
    ${result}=    Curator Agent Get Info Returns Agent Info
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[role_correct]
    Should Be True    ${result}[trust_correct]

# =============================================================================
# Issue Management Tests
# =============================================================================

Get Issues Returns Empty Initially
    [Documentation]    GIVEN new curator WHEN get_issues THEN empty list
    [Tags]    unit    curator    issues    empty
    ${result}=    Get Issues Returns Empty Initially
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_empty]

Get Issues Filters By Severity
    [Documentation]    GIVEN issues WHEN filter by severity THEN filtered
    [Tags]    unit    curator    issues    filter
    ${result}=    Get Issues Filters By Severity
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[count_correct]
    Should Be True    ${result}[rule_correct]

Get Issues Filters By Resolved
    [Documentation]    GIVEN issues WHEN filter by resolved THEN filtered
    [Tags]    unit    curator    issues    resolved
    ${result}=    Get Issues Filters By Resolved
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[count_correct]
    Should Be True    ${result}[rule_correct]

Get Summary Returns Correct Data
    [Documentation]    GIVEN issues WHEN get_summary THEN correct counts
    [Tags]    unit    curator    issues    summary
    ${result}=    Get Summary Returns Correct Data
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[agent_id_correct]
    Should Be True    ${result}[total_issues_correct]
    Should Be True    ${result}[open_issues_correct]
    Should Be True    ${result}[critical_correct]
    Should Be True    ${result}[high_correct]
    Should Be True    ${result}[medium_correct]

# =============================================================================
# Curation Action Tests
# =============================================================================

Validate Rule Not Found Returns Error
    [Documentation]    GIVEN missing rule WHEN validate THEN error
    [Tags]    unit    curator    validate    error
    ${result}=    Validate Rule Not Found Returns Error
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success_false]
    Should Be True    ${result}[has_not_found]

Validate Rule Detects Missing Fields
    [Documentation]    GIVEN incomplete rule WHEN validate THEN issues found
    [Tags]    unit    curator    validate    fields
    ${result}=    Validate Rule Detects Missing Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success_true]
    Should Be True    ${result}[has_issues]

Validate Rule Passes For Complete Rule
    [Documentation]    GIVEN complete rule WHEN validate THEN no issues
    [Tags]    unit    curator    validate    complete
    ${result}=    Validate Rule Passes For Complete Rule
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success_true]
    Should Be True    ${result}[no_issues]

Propose Change Fails Without MCP Client
    [Documentation]    GIVEN no MCP client WHEN propose THEN fails
    [Tags]    unit    curator    propose    error
    ${result}=    Propose Change Fails Without MCP Client
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success_false]
    Should Be True    ${result}[has_mcp_required]

# =============================================================================
# Integration Tests
# =============================================================================

Analyze Quality With MCP Returns Results
    [Documentation]    GIVEN MCP client WHEN analyze_quality THEN returns issues
    [Tags]    unit    curator    mcp    quality
    ${result}=    Analyze Quality With MCP Returns Results
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success_true]
    Should Be True    ${result}[has_issue]
    Should Be True    ${result}[rule_correct]

Find Conflicts With MCP Returns Results
    [Documentation]    GIVEN MCP client WHEN find_conflicts THEN returns conflicts
    [Tags]    unit    curator    mcp    conflicts
    ${result}=    Find Conflicts With MCP Returns Results
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success_true]
    Should Be True    ${result}[has_issue]
    Should Be True    ${result}[type_correct]

Propose Change With MCP Returns Success
    [Documentation]    GIVEN MCP client WHEN propose_change THEN succeeds
    [Tags]    unit    curator    mcp    propose
    ${result}=    Propose Change With MCP Returns Success
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success_true]
    Should Be True    ${result}[has_proposed]

Run Full Audit Returns All Results
    [Documentation]    GIVEN MCP client WHEN run_full_audit THEN all results
    [Tags]    unit    curator    mcp    audit
    ${result}=    Run Full Audit Returns All Results
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_quality]
    Should Be True    ${result}[has_conflicts]
    Should Be True    ${result}[has_orphans]
    Should Be True    ${result}[all_success]
