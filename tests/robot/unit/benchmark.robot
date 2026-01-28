*** Settings ***
Documentation    RF-004: Unit Tests - Benchmark Framework
...              Migrated from tests/test_benchmark.py
...              Per P3.5: Governance benchmark framework
Library          Collections
Library          ../../libs/BenchmarkLibrary.py
Force Tags        unit    benchmark    performance    low    validate    TEST-COMP-01-v1

*** Test Cases ***
# =============================================================================
# Module Tests
# =============================================================================

Benchmark Module Exists
    [Documentation]    GIVEN governance dir WHEN checking THEN benchmark.py exists
    [Tags]    unit    benchmark    module    file
    ${result}=    Benchmark Module Exists
    Should Be True    ${result}[exists]

Benchmark Result Dataclass Works
    [Documentation]    GIVEN BenchmarkResult WHEN creating THEN fields correct
    [Tags]    unit    benchmark    dataclass    result
    ${result}=    Benchmark Result Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[iterations_correct]
    Should Be True    ${result}[success_rate_correct]

Benchmark Suite Dataclass Works
    [Documentation]    GIVEN BenchmarkSuite WHEN creating THEN fields correct
    [Tags]    unit    benchmark    dataclass    suite
    ${result}=    Benchmark Suite Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[results_empty]

Benchmark Suite To Dict Works
    [Documentation]    GIVEN BenchmarkSuite WHEN to_dict THEN serializable
    [Tags]    unit    benchmark    dataclass    serialize
    ${result}=    Benchmark Suite To Dict Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[results_count]
    Should Be True    ${result}[result_name]
    Should Be True    ${result}[json_serializable]

Governance Benchmark Class Works
    [Documentation]    GIVEN GovernanceBenchmark WHEN creating THEN configurable
    [Tags]    unit    benchmark    class    governance
    ${result}=    Governance Benchmark Class Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[iterations_correct]
    Should Be True    ${result}[results_empty]

Measure Function Times Correctly
    [Documentation]    GIVEN _measure WHEN timing function THEN correct time
    [Tags]    unit    benchmark    measure    timing
    ${result}=    Measure Function Times Correctly
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[mean_time_correct]
    Should Be True    ${result}[iterations_correct]
    Should Be True    ${result}[success_rate_correct]

Measure Function Tracks Errors
    [Documentation]    GIVEN failing function WHEN _measure THEN tracks errors
    [Tags]    unit    benchmark    measure    errors
    ${result}=    Measure Function Tracks Errors
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[success_rate_zero]
    Should Be True    ${result}[has_errors]

Measure Function Passes Args
    [Documentation]    GIVEN function with args WHEN _measure THEN passes args
    [Tags]    unit    benchmark    measure    args
    ${result}=    Measure Function Passes Args
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[success_rate_correct]

# =============================================================================
# CLI Tests
# =============================================================================

Main Function Exists
    [Documentation]    GIVEN __main__.py WHEN importing THEN main exists
    [Tags]    unit    benchmark    cli    main
    ${result}=    Main Function Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[callable]

Benchmark Module Has Required Exports
    [Documentation]    GIVEN benchmark module WHEN importing THEN has exports
    [Tags]    unit    benchmark    module    exports
    ${result}=    Benchmark Module Has Required Exports
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_governance]
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[has_suite]

# =============================================================================
# Performance Target Tests
# =============================================================================

Benchmark Result Supports Metadata
    [Documentation]    GIVEN BenchmarkResult WHEN metadata THEN stores target
    [Tags]    unit    benchmark    metadata    target
    ${result}=    Benchmark Result Supports Metadata
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_target]
    Should Be True    ${result}[target_correct]

Performance Thresholds Are Reasonable
    [Documentation]    GIVEN performance targets WHEN checking THEN reasonable
    [Tags]    unit    benchmark    performance    thresholds
    ${result}=    Performance Thresholds Are Reasonable
    Should Be True    ${result}[connect_reasonable]
    Should Be True    ${result}[inference_reasonable]
    Should Be True    ${result}[hybrid_reasonable]
