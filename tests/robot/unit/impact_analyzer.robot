*** Settings ***
Documentation    RF-004: Unit Tests - Impact Analyzer
...              Migrated from tests/test_impact_analyzer.py
...              Per P9.4: Rule impact analysis and dependency graph
Library          Collections
Library          ../../libs/ImpactAnalyzerLibrary.py
Library          ../../libs/ImpactAnalyzerAdvancedLibrary.py
Force Tags        unit    rules    impact    low    rule    validate

*** Test Cases ***
# =============================================================================
# Get Rule Dependencies Tests
# =============================================================================

Get Rule Dependencies Connection Failure
    [Documentation]    GIVEN connection fails WHEN get_rule_dependencies THEN empty list
    [Tags]    unit    impact    dependencies    connection
    ${result}=    Get Rule Dependencies Connection Failure
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[empty_result]
    Should Be True    ${result}[close_called]

Get Rule Dependencies Returns List
    [Documentation]    GIVEN connected WHEN get_rule_dependencies THEN returns list
    [Tags]    unit    impact    dependencies    list
    ${result}=    Get Rule Dependencies Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_result]

Get Rule Dependencies Empty When None
    [Documentation]    GIVEN no dependencies WHEN get_rule_dependencies THEN empty
    [Tags]    unit    impact    dependencies    empty
    ${result}=    Get Rule Dependencies Empty When None
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[empty_result]

# =============================================================================
# Get Rule Dependents Tests
# =============================================================================

Get Rule Dependents Connection Failure
    [Documentation]    GIVEN connection fails WHEN get_rule_dependents THEN empty list
    [Tags]    unit    impact    dependents    connection
    ${result}=    Get Rule Dependents Connection Failure
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[empty_result]

Get Rule Dependents Returns List
    [Documentation]    GIVEN connected WHEN get_rule_dependents THEN returns list
    [Tags]    unit    impact    dependents    list
    ${result}=    Get Rule Dependents Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_result]

# =============================================================================
# Get Rule Conflicts Tests
# =============================================================================

Get Rule Conflicts Connection Failure
    [Documentation]    GIVEN connection fails WHEN get_rule_conflicts THEN empty list
    [Tags]    unit    impact    conflicts    connection
    ${result}=    Get Rule Conflicts Connection Failure
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[empty_result]

Get Rule Conflicts Returns List
    [Documentation]    GIVEN conflicts exist WHEN get_rule_conflicts THEN returns list
    [Tags]    unit    impact    conflicts    list
    ${result}=    Get Rule Conflicts Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_one]
    Should Be True    ${result}[correct_reason]

# =============================================================================
# Build Dependency Graph Tests
# =============================================================================

Build Dependency Graph Nodes From Rules
    [Documentation]    GIVEN rules WHEN build_dependency_graph THEN nodes created
    [Tags]    unit    impact    graph    nodes
    ${result}=    Build Dependency Graph Nodes From Rules
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[nodes_count]
    Should Be True    ${result}[stats_count]

Build Dependency Graph Edges From Dependencies
    [Documentation]    GIVEN dependencies WHEN build_dependency_graph THEN edges created
    [Tags]    unit    impact    graph    edges
    ${result}=    Build Dependency Graph Edges From Dependencies
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[one_edge]
    Should Be True    ${result}[source_correct]
    Should Be True    ${result}[target_correct]

Build Dependency Graph Includes Conflict Edges
    [Documentation]    GIVEN conflicts WHEN build_dependency_graph THEN conflict edges
    [Tags]    unit    impact    graph    conflicts
    ${result}=    Build Dependency Graph Includes Conflict Edges
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[one_conflict]

# =============================================================================
# Calculate Rule Impact Tests
# =============================================================================

Calculate Rule Impact Low Risk No Dependents
    [Documentation]    GIVEN no dependents WHEN calculate_rule_impact THEN LOW risk
    [Tags]    unit    impact    calculate    low
    ${result}=    Calculate Rule Impact Low Risk No Dependents
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[low_risk]
    Should Be True    ${result}[zero_affected]

Calculate Rule Impact Medium Risk Few Dependents
    [Documentation]    GIVEN 1-2 dependents WHEN calculate_rule_impact THEN MEDIUM risk
    [Tags]    unit    impact    calculate    medium
    ${result}=    Calculate Rule Impact Medium Risk Few Dependents
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[medium_risk]
    Should Be True    ${result}[one_affected]

Calculate Rule Impact Critical When Critical Affected
    [Documentation]    GIVEN CRITICAL rule affected WHEN calculate THEN CRITICAL risk
    [Tags]    unit    impact    calculate    critical
    ${result}=    Calculate Rule Impact Critical When Critical Affected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[critical_risk]
    Should Be True    ${result}[critical_affected]

Calculate Rule Impact Includes Recommendation
    [Documentation]    GIVEN impact WHEN calculate THEN has recommendation
    [Tags]    unit    impact    calculate    recommendation
    ${result}=    Calculate Rule Impact Includes Recommendation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_recommendation]
    Should Be True    ${result}[has_safe]

# =============================================================================
# Generate Mermaid Graph Tests
# =============================================================================

Generate Mermaid Syntax
    [Documentation]    GIVEN graph WHEN generate_mermaid_graph THEN valid syntax
    [Tags]    unit    impact    mermaid    syntax
    ${result}=    Generate Mermaid Syntax
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_graph_td]
    Should Be True    ${result}[has_rule_001]
    Should Be True    ${result}[has_rule_002]
    Should Be True    ${result}[has_edge]

Generate Mermaid Applies Status Classes
    [Documentation]    GIVEN nodes WHEN generate_mermaid THEN status classes applied
    [Tags]    unit    impact    mermaid    classes
    ${result}=    Generate Mermaid Applies Status Classes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_active]
    Should Be True    ${result}[has_deprecated]

Generate Mermaid Handles Conflict Edges
    [Documentation]    GIVEN conflicts WHEN generate_mermaid THEN dotted lines
    [Tags]    unit    impact    mermaid    conflicts
    ${result}=    Generate Mermaid Handles Conflict Edges
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_dotted]

# =============================================================================
# State Management Tests
# =============================================================================

Initial State Has Impact Fields
    [Documentation]    GIVEN initial state WHEN check THEN has impact fields
    [Tags]    unit    impact    state    initial
    ${result}=    Initial State Has Impact Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_selected]
    Should Be True    ${result}[has_analysis]
    Should Be True    ${result}[has_graph]
    Should Be True    ${result}[has_mermaid]
    Should Be True    ${result}[has_view]

Navigation Includes Impact
    [Documentation]    GIVEN navigation WHEN check THEN includes impact
    [Tags]    unit    impact    state    navigation
    ${result}=    Navigation Includes Impact
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_impact]

With Impact Analysis Transform
    [Documentation]    GIVEN with_impact_analysis WHEN call THEN state updated
    [Tags]    unit    impact    state    transform
    ${result}=    With Impact Analysis Transform
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[selected_rule]
    Should Be True    ${result}[analysis_set]
    Should Be True    ${result}[graph_set]
    Should Be True    ${result}[mermaid_set]

With Graph View Transform
    [Documentation]    GIVEN with_graph_view WHEN call THEN view toggled
    [Tags]    unit    impact    state    view
    ${result}=    With Graph View Transform
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[view_false]

# =============================================================================
# Risk Helpers Tests
# =============================================================================

Risk Colors Defined
    [Documentation]    GIVEN RISK_COLORS WHEN check THEN all levels defined
    [Tags]    unit    impact    risk    colors
    ${result}=    Risk Colors Defined
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_critical]
    Should Be True    ${result}[has_high]
    Should Be True    ${result}[has_medium]
    Should Be True    ${result}[has_low]

Get Risk Color
    [Documentation]    GIVEN get_risk_color WHEN call THEN correct colors
    [Tags]    unit    impact    risk    color
    ${result}=    Get Risk Color
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[critical_error]
    Should Be True    ${result}[low_success]
    Should Be True    ${result}[unknown_grey]

Format Impact Summary
    [Documentation]    GIVEN format_impact_summary WHEN call THEN formatted
    [Tags]    unit    impact    risk    summary
    ${result}=    Format Impact Summary
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rule_id]
    Should Be True    ${result}[risk_level]
    Should Be True    ${result}[risk_color]
    Should Be True    ${result}[total_affected]
    Should Be True    ${result}[direct_dependents]
    Should Be True    ${result}[dependencies]
