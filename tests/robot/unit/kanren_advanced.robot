*** Settings ***
Documentation    RF-004: Unit Tests - Kanren Advanced Features
...              Split from kanren_constraints.robot per DOC-SIZE-01-v1
...              Covers: Rule Conflict Detection, KAN-004 TypeDB Loader, KAN-005 Benchmark
Library          Collections
Library          ../../libs/KanrenAdvancedLibrary.py
Force Tags        unit    kanren    advanced    high    rule    validate    TEST-TDD-01-v1

*** Test Cases ***
# =============================================================================
# Rule Conflict Detection Tests
# =============================================================================

Conflicting Priorities Detected
    [Documentation]    GIVEN same category different priority WHEN conflicting_priorities THEN detected
    [Tags]    unit    kanren    conflict    priorities
    ${result}=    Conflicting Priorities Detected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_conflict]

No Conflict Different Category
    [Documentation]    GIVEN different category WHEN conflicting_priorities THEN no conflict
    [Tags]    unit    kanren    conflict    category
    ${result}=    No Conflict Different Category
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[no_conflict]

No Conflict Same Priority
    [Documentation]    GIVEN same priority WHEN conflicting_priorities THEN no conflict
    [Tags]    unit    kanren    conflict    same
    ${result}=    No Conflict Same Priority
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[no_conflict]

Find All Conflicts
    [Documentation]    GIVEN rule set WHEN find_rule_conflicts THEN all conflicts found
    [Tags]    unit    kanren    conflict    find
    ${result}=    Find All Conflicts
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[conflict_count]

# =============================================================================
# KAN-004: TypeDB -> Kanren Loader Tests
# =============================================================================

Loader Imports
    [Documentation]    Loader module can be imported
    [Tags]    unit    kanren    kan-004    import
    ${result}=    Loader Imports
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[rule_constraint]
    Should Be True    ${result}[bridge]
    Should Be True    ${result}[load_func]

Rule Constraint From Dict
    [Documentation]    RuleConstraint creates from TypeDB query result
    [Tags]    unit    kanren    kan-004    constraint
    ${result}=    Rule Constraint From Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[rule_id]
    Should Be True    ${result}[semantic_id]
    Should Be True    ${result}[priority]
    Should Be True    ${result}[rule_type]

Load Rules From JSON
    [Documentation]    load_rules_from_typedb parses JSON correctly
    [Tags]    unit    kanren    kan-004    json
    ${result}=    Load Rules From JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[count]
    Should Be True    ${result}[first_id]
    Should Be True    ${result}[first_priority]
    Should Be True    ${result}[second_id]
    Should Be True    ${result}[second_priority]

Load Rules Empty Input
    [Documentation]    load_rules_from_typedb handles empty input
    [Tags]    unit    kanren    kan-004    empty
    ${result}=    Load Rules Empty Input
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[none_empty]
    Should Be True    ${result}[str_empty]
    Should Be True    ${result}[invalid_empty]

Populate Kanren Facts
    [Documentation]    populate_kanren_facts creates Kanren relations
    [Tags]    unit    kanren    kan-004    facts
    ${result}=    Populate Kanren Facts
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[priority_count]
    Should Be True    ${result}[critical_count]
    Should Be True    ${result}[rule_type_count]
    Should Be True    ${result}[category_count]

TypeDB Kanren Bridge Lifecycle
    [Documentation]    TypeDBKanrenBridge manages load/validate lifecycle
    [Tags]    unit    kanren    kan-004    bridge
    ${result}=    TypeDB Kanren Bridge Lifecycle
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[initially_not_loaded]
    Should Be True    ${result}[validation_fails_unloaded]
    Should Be True    ${result}[loaded_after]
    Should Be True    ${result}[priority_count]
    Should Be True    ${result}[rules_count]

Validate Rule Compliance Expert
    [Documentation]    Expert agent can comply with any rule
    [Tags]    unit    kanren    kan-004    compliance    expert
    ${result}=    Validate Rule Compliance Expert
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[compliant]
    Should Be True    ${result}[trust_level]

Validate Rule Compliance Low Trust
    [Documentation]    Low trust agent cannot comply with CRITICAL rules
    [Tags]    unit    kanren    kan-004    compliance    low
    ${result}=    Validate Rule Compliance Low Trust
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[not_compliant]
    Should Be True    ${result}[has_violation]

Validate Rule Missing Evidence
    [Documentation]    Missing evidence causes compliance failure for CRITICAL rules
    [Tags]    unit    kanren    kan-004    compliance    evidence
    ${result}=    Validate Rule Missing Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[not_compliant]
    Should Be True    ${result}[has_evidence_violation]

Get Rules By Category
    [Documentation]    Bridge filters rules by category
    [Tags]    unit    kanren    kan-004    category
    ${result}=    Get Rules By Category
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[gov_count]
    Should Be True    ${result}[test_count]
    Should Be True    ${result}[all_gov]

# =============================================================================
# KAN-005: Performance Benchmark Tests
# =============================================================================

Benchmark Imports
    [Documentation]    Benchmark module can be imported
    [Tags]    unit    kanren    kan-005    import
    ${result}=    Benchmark Imports
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[result]
    Should Be True    ${result}[run_func]

Benchmark Result Dataclass
    [Documentation]    BenchmarkResult has correct fields
    [Tags]    unit    kanren    kan-005    dataclass
    ${result}=    Benchmark Result Dataclass
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[avg_correct]
    Should Be True    ${result}[passed]
    Should Be True    ${result}[has_pass]

Run All Benchmarks Returns Results
    [Documentation]    run_all_benchmarks returns list of results
    [Tags]    unit    kanren    kan-005    benchmark
    ${result}=    Run All Benchmarks Returns Results
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[is_list]
    Should Be True    ${result}[has_benchmarks]

All Benchmarks Pass
    [Documentation]    All benchmarks should pass their targets
    [Tags]    unit    kanren    kan-005    pass
    ${result}=    All Benchmarks Pass
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[all_passed]

Kanren Under 100ms Target
    [Documentation]    Total Kanren validation time is under 100ms
    [Tags]    unit    kanren    kan-005    performance
    ${result}=    Kanren Under 100ms Target
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[under_target]

Compare Returns Overhead
    [Documentation]    compare_kanren_vs_direct returns overhead metrics
    [Tags]    unit    kanren    kan-005    overhead
    ${result}=    Compare Returns Overhead
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_trust_level]
    Should Be True    ${result}[has_kanren_ms]
    Should Be True    ${result}[has_direct_ms]
    Should Be True    ${result}[has_overhead]

Benchmark Summary Pass
    [Documentation]    Benchmark summary should show all passed
    [Tags]    unit    kanren    kan-005    summary
    ${result}=    Benchmark Summary Pass
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[all_passed]
