*** Settings ***
Documentation    RF-004: Unit Tests - Rule Impact Analyzer
...              Migrated from tests/test_rule_impact.py
...              Per P9.4: Rule dependency analysis and impact visualization
Library          Collections
Library          ../../libs/RuleImpactLibrary.py

*** Test Cases ***
# =============================================================================
# Module Existence Tests
# =============================================================================

Rule Impact Module Exists
    [Documentation]    GIVEN agent/ WHEN checking THEN rule_impact.py exists
    [Tags]    unit    rule-impact    validate    module
    ${result}=    Rule Impact Module Exists
    Should Be True    ${result}[exists]

Rule Impact Class Importable
    [Documentation]    GIVEN rule_impact WHEN importing THEN RuleImpactAnalyzer available
    [Tags]    unit    rule-impact    validate    module
    ${result}=    Rule Impact Class Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[instantiable]

Analyzer Has Required Methods
    [Documentation]    GIVEN analyzer WHEN checking THEN has required methods
    [Tags]    unit    rule-impact    validate    module
    ${result}=    Analyzer Has Required Methods
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_analyze_dependencies]
    Should Be True    ${result}[has_get_impact_graph]
    Should Be True    ${result}[has_simulate_change]
    Should Be True    ${result}[has_get_affected_rules]

# =============================================================================
# Dependency Analysis Tests
# =============================================================================

Analyze Dependencies Works
    [Documentation]    GIVEN rule_id WHEN analyze_dependencies THEN returns dict
    [Tags]    unit    rule-impact    validate    analysis
    ${result}=    Analyze Dependencies Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_rule_id]

Find Dependent Rules Works
    [Documentation]    GIVEN rule_id WHEN get_dependent_rules THEN returns list
    [Tags]    unit    rule-impact    validate    analysis
    ${result}=    Find Dependent Rules Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

Find Required Rules Works
    [Documentation]    GIVEN rule_id WHEN get_required_rules THEN returns list
    [Tags]    unit    rule-impact    validate    analysis
    ${result}=    Find Required Rules Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

