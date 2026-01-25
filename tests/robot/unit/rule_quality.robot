*** Settings ***
Documentation    RF-004: Unit Tests - Rule Quality Analyzer
...              Migrated from tests/test_rule_quality.py
...              Per RULE-004: Exploratory Testing & Executable Spec
Library          Collections
Library          ../../libs/RuleQualityLibrary.py

*** Test Cases ***
# =============================================================================
# Class Tests
# =============================================================================

Rule Quality Analyzer Class Exists
    [Documentation]    GIVEN rule_quality WHEN import THEN class exists
    [Tags]    unit    quality    class    import
    ${result}=    Rule Quality Analyzer Class Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Issue Severity Enum Exists
    [Documentation]    GIVEN IssueSeverity WHEN check THEN has values
    [Tags]    unit    quality    enum    severity
    ${result}=    Issue Severity Enum Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[critical]
    Should Be True    ${result}[high]
    Should Be True    ${result}[medium]
    Should Be True    ${result}[low]

Issue Type Enum Exists
    [Documentation]    GIVEN IssueType WHEN check THEN has values
    [Tags]    unit    quality    enum    type
    ${result}=    Issue Type Enum Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[orphaned]
    Should Be True    ${result}[shallow]
    Should Be True    ${result}[over_connected]
    Should Be True    ${result}[circular]

# =============================================================================
# RuleIssue Dataclass Tests
# =============================================================================

Rule Issue Creation
    [Documentation]    GIVEN RuleIssue WHEN create THEN fields correct
    [Tags]    unit    quality    dataclass    create
    ${result}=    Rule Issue Creation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rule_id_correct]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[severity_correct]

Rule Issue To Dict
    [Documentation]    GIVEN RuleIssue WHEN to_dict THEN dict correct
    [Tags]    unit    quality    dataclass    serialize
    ${result}=    Rule Issue To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rule_id_correct]
    Should Be True    ${result}[issue_type_correct]
    Should Be True    ${result}[severity_correct]

# =============================================================================
# RuleHealthReport Tests
# =============================================================================

Rule Health Report Creation
    [Documentation]    GIVEN RuleHealthReport WHEN create THEN fields correct
    [Tags]    unit    quality    report    create
    ${result}=    Rule Health Report Creation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[total_correct]
    Should Be True    ${result}[issues_correct]
    Should Be True    ${result}[healthy_correct]

Rule Health Report To JSON
    [Documentation]    GIVEN RuleHealthReport WHEN to_json THEN valid JSON
    [Tags]    unit    quality    report    json
    ${result}=    Rule Health Report To JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[total_correct]
    Should Be True    ${result}[issues_correct]

# =============================================================================
# Orphaned Rule Detection Tests
# =============================================================================

Find Orphaned Rules Excludes Foundational
    [Documentation]    GIVEN foundational rules WHEN find_orphaned THEN excluded
    [Tags]    unit    quality    orphaned    foundational
    ${result}=    Find Orphaned Rules Excludes Foundational
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rule_001_not_orphan]
    Should Be True    ${result}[rule_002_not_orphan]

Find Orphaned Rules Flags Non Foundational
    [Documentation]    GIVEN non-foundational WHEN find_orphaned THEN flagged
    [Tags]    unit    quality    orphaned    detect
    ${result}=    Find Orphaned Rules Flags Non Foundational
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[one_issue]
    Should Be True    ${result}[correct_id]
    Should Be True    ${result}[correct_type]

# =============================================================================
# Shallow Rule Detection Tests
# =============================================================================

Find Shallow Rules Detects Missing Attrs
    [Documentation]    GIVEN incomplete rule WHEN find_shallow THEN flagged
    [Tags]    unit    quality    shallow    detect
    ${result}=    Find Shallow Rules Detects Missing Attrs
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[one_issue]
    Should Be True    ${result}[correct_id]
    Should Be True    ${result}[correct_type]
    Should Be True    ${result}[has_missing]

# =============================================================================
# Over-Connected Detection Tests
# =============================================================================

Find Over Connected Rules
    [Documentation]    GIVEN rule with many deps WHEN find_over THEN flagged
    [Tags]    unit    quality    overconnected    detect
    ${result}=    Find Over Connected Rules
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[one_issue]
    Should Be True    ${result}[correct_id]
    Should Be True    ${result}[correct_type]
    Should Be True    ${result}[correct_count]

# =============================================================================
# Circular Dependency Detection Tests
# =============================================================================

Find Circular Dependencies Simple
    [Documentation]    GIVEN A->B->A cycle WHEN find_circular THEN detected
    [Tags]    unit    quality    circular    detect
    ${result}=    Find Circular Dependencies Simple
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_circular]

Find Circular Dependencies None
    [Documentation]    GIVEN acyclic deps WHEN find_circular THEN no issues
    [Tags]    unit    quality    circular    none
    ${result}=    Find Circular Dependencies None
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[no_cycles]

# =============================================================================
# Impact Analysis Tests
# =============================================================================

Get Rule Impact Returns Dict
    [Documentation]    GIVEN rule WHEN get_rule_impact THEN dict returned
    [Tags]    unit    quality    impact    dict
    ${result}=    Get Rule Impact Returns Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_rule_id]
    Should Be True    ${result}[has_impact_score]
    Should Be True    ${result}[has_recommendation]
    Should Be True    ${result}[has_dependents]

Impact Score Includes Priority
    [Documentation]    GIVEN CRITICAL vs LOW WHEN impact THEN CRITICAL higher
    [Tags]    unit    quality    impact    priority
    ${result}=    Impact Score Includes Priority
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[crit_higher]

# =============================================================================
# Full Analysis Tests
# =============================================================================

Analyze Returns Health Report
    [Documentation]    GIVEN analyzer WHEN analyze THEN RuleHealthReport
    [Tags]    unit    quality    analysis    full
    ${result}=    Analyze Returns Health Report
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_report]
    Should Be True    ${result}[total_correct]
    Should Be True    ${result}[has_timestamp]

# =============================================================================
# MCP Tools Tests
# =============================================================================

Governance Analyze Rules Exists
    [Documentation]    GIVEN compat WHEN import THEN tool exists
    [Tags]    unit    quality    mcp    analyze
    ${result}=    Governance Analyze Rules Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

Governance Rule Impact Exists
    [Documentation]    GIVEN compat WHEN import THEN tool exists
    [Tags]    unit    quality    mcp    impact
    ${result}=    Governance Rule Impact Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

Governance Find Issues Exists
    [Documentation]    GIVEN compat WHEN import THEN tool exists
    [Tags]    unit    quality    mcp    issues
    ${result}=    Governance Find Issues Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

# =============================================================================
# Convenience Functions Tests
# =============================================================================

Analyze Rule Quality Returns JSON
    [Documentation]    GIVEN analyze_rule_quality WHEN call THEN valid JSON
    [Tags]    unit    quality    convenience    json
    ${result}=    Analyze Rule Quality Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]

Find Rule Issues Returns JSON
    [Documentation]    GIVEN find_rule_issues WHEN call THEN valid JSON
    [Tags]    unit    quality    convenience    json
    ${result}=    Find Rule Issues Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
