*** Settings ***
Documentation    RF-004: Unit Tests - Quality Analyzer Split Module
...              Migrated from tests/test_quality_analyzer_split.py
...              Per DOC-SIZE-01-v1: Files under 400 lines
Library          Collections
Library          ../../libs/QualityAnalyzerSplitLibrary.py
Force Tags        unit    rules    quality    low    rule    validate    TEST-QUAL-01-v1

*** Test Cases ***
# =============================================================================
# Module Structure Tests
# =============================================================================

Analyzer Module Exists
    [Documentation]    Verify analyzer.py exists in quality directory
    [Tags]    unit    structure    quality    analyzer
    ${exists}=    Analyzer Module Exists
    Should Be True    ${exists}    analyzer.py must exist

Impact Module Exists
    [Documentation]    Verify impact.py extraction exists
    [Tags]    unit    structure    quality    impact
    ${exists}=    Impact Module Exists
    Should Be True    ${exists}    impact.py should be extracted

Analyzer Module Under 400 Lines
    [Documentation]    Per DOC-SIZE-01-v1: analyzer.py should be under 400 lines
    [Tags]    unit    structure    quality    doc-size
    ${result}=    File Under Limit    analyzer.py    400
    Should Be True    ${result}[under_limit]    analyzer.py has ${result}[lines] lines, should be <400

# =============================================================================
# Backward Compatibility Tests
# =============================================================================

Import RuleQualityAnalyzer Class
    [Documentation]    Verify RuleQualityAnalyzer can still be imported
    [Tags]    unit    compatibility    quality    import
    ${success}=    Import Rule Quality Analyzer
    Should Be True    ${success}    RuleQualityAnalyzer should be importable

Analyzer Has Get Rule Impact Method
    [Documentation]    Verify analyzer still has get_rule_impact method
    [Tags]    unit    compatibility    quality    method
    ${has_method}=    Analyzer Has Get Rule Impact
    Should Be True    ${has_method}    get_rule_impact method should exist

Impact Module Accessible From Package
    [Documentation]    Verify impact module accessible from quality package
    [Tags]    unit    compatibility    quality    package
    ${accessible}=    Impact Module In Quality Init
    Should Be True    ${accessible}    impact module should be accessible from quality package

# =============================================================================
# Impact Module Tests
# =============================================================================

Calculate Rule Impact Function Signature
    [Documentation]    Verify function signature has required params
    [Tags]    unit    impact    quality    signature
    ${result}=    Get Calculate Rule Impact Params
    Should Be True    ${result}[has_rule_id]    Should have rule_id param
    Should Be True    ${result}[has_rule]    Should have rule param
    Should Be True    ${result}[has_dependents_cache]    Should have dependents_cache param

Calculate Rule Impact Returns Dict
    [Documentation]    Verify function returns dictionary with required keys
    [Tags]    unit    impact    quality    return
    ${result}=    Calculate Rule Impact Returns Dict
    Should Be True    ${result}[is_dict]    Should return dictionary
    Should Be True    ${result}[has_rule_id]    Should have rule_id key
    Should Be True    ${result}[has_impact_score]    Should have impact_score key
    Should Be True    ${result}[has_recommendation]    Should have recommendation key

Critical Rule Has High Impact Score
    [Documentation]    Verify CRITICAL priority rule has score >= 60
    [Tags]    unit    impact    quality    score
    ${result}=    Test Critical Rule Impact Score
    Should Be True    ${result}[meets_threshold]    CRITICAL rule should have impact_score >= 60, got ${result}[impact_score]

# =============================================================================
# Integration Tests
# =============================================================================

Analyzer And Impact Integration
    [Documentation]    Verify analyzer and impact modules work together
    [Tags]    unit    integration    quality    full
    ${result}=    Verify Integration
    Should Be True    ${result}[analyzer_import_ok]    Analyzer import failed
    Should Be True    ${result}[impact_import_ok]    Impact import failed
    Should Be True    ${result}[analyzer_has_method]    Analyzer missing get_rule_impact
    Should Be True    ${result}[impact_in_package]    Impact not in quality package
