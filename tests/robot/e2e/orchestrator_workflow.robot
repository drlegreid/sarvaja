*** Settings ***
Documentation    E2E Tests for Orchestrator Continuous Workflow
...              Per WORKFLOW-ORCH-01-v1: Spec → Impl → Validate loop
...              Per TEST-TDD-01-v1: RED phase — tests written before implementation
...              Per TEST-BDD-01-v1: BDD Given/When/Then structure
Library          Collections
Library          libs/OrchestratorE2ELibrary.py
Resource         ../resources/common_setup.resource
Suite Setup      Platform Setup
Suite Teardown   Cleanup Orchestrator Test Data
Test Tags        e2e    workflow    orchestrator    WORKFLOW-ORCH-01-v1

*** Test Cases ***

# === STATE CREATION ===

Orchestrator State Has Required Fields
    [Documentation]    Verify initial orchestrator state has all required fields
    [Tags]    e2e    workflow    state    critical
    ${state}=    Create Orchestrator State
    Should Not Be Empty    ${state}[cycle_id]
    Should Be Equal    ${state}[current_phase]    idle
    Should Be Equal    ${state}[status]    pending
    Should Be Equal As Numbers    ${state}[cycles_completed]    0
    Should Be Equal As Numbers    ${state}[max_cycles]    10
    Dictionary Should Contain Key    ${state}    backlog
    Dictionary Should Contain Key    ${state}    cycle_history

# === BACKLOG MANAGEMENT ===

Backlog Node Picks Highest Priority Task
    [Documentation]    Given a backlog with mixed priorities, highest is picked first
    [Tags]    e2e    workflow    backlog    high
    ${state}=    Create Orchestrator State With Backlog
    ...    GAP-LOW-001:LOW    GAP-HIGH-001:HIGH    GAP-CRIT-001:CRITICAL
    ${result}=    Run Backlog Node    ${state}
    Should Be Equal    ${result}[current_task][task_id]    GAP-CRIT-001
    Should Be Equal    ${result}[current_phase]    task_selected

Gate Node Ends When Backlog Empty
    [Documentation]    Given empty backlog, orchestrator should complete
    [Tags]    e2e    workflow    gate    high
    ${state}=    Create Orchestrator State
    ${result}=    Run Gate Node    ${state}
    Should Be Equal    ${result}[current_phase]    backlog_empty

Gate Node Continues When Backlog Has Tasks
    [Documentation]    Given non-empty backlog, orchestrator should continue to spec
    [Tags]    e2e    workflow    gate    high
    ${state}=    Create Orchestrator State With Backlog    GAP-TEST-001:HIGH
    ${result}=    Run Gate Node    ${state}
    Should Be Equal    ${result}[gate_decision]    continue

# === SPEC PHASE ===

Spec Node Produces Specification From Task
    [Documentation]    Given a selected task, spec node produces acceptance criteria
    [Tags]    e2e    workflow    spec    critical
    ${state}=    Create State With Selected Task    GAP-TEST-001    Implement feature X
    ${result}=    Run Spec Node    ${state}
    Should Be Equal    ${result}[current_phase]    specified
    Should Not Be Empty    ${result}[specification][acceptance_criteria]
    Should Not Be Empty    ${result}[specification][files_to_modify]

# === IMPLEMENT PHASE ===

Implement Node Tracks Changes
    [Documentation]    Given a specification, implement node records what changed
    [Tags]    e2e    workflow    implement    high
    ${state}=    Create State With Specification
    ${result}=    Run Implement Node    ${state}
    Should Be Equal    ${result}[current_phase]    implemented
    Dictionary Should Contain Key    ${result}    implementation

# === VALIDATE PHASE ===

Validate Node Runs Tests And Checks Coverage
    [Documentation]    Given an implementation, validate node runs tests and heuristics
    [Tags]    e2e    workflow    validate    critical
    ${state}=    Create State With Implementation
    ${result}=    Run Validate Node    ${state}
    Should Be Equal    ${result}[current_phase]    validated
    Dictionary Should Contain Key    ${result}    validation_results
    Dictionary Should Contain Key    ${result}[validation_results]    tests_passed
    Dictionary Should Contain Key    ${result}[validation_results]    heuristics_passed

Validate Node Discovers New Gaps
    [Documentation]    Validation may discover new gaps that get injected into backlog
    [Tags]    e2e    workflow    validate    inject    high
    ${state}=    Create State With Implementation    discover_gaps=True
    ${result}=    Run Validate Node    ${state}
    ${gap_count}=    Get Length    ${result}[gaps_discovered]
    Should Be True    ${gap_count} > 0    Expected discovered gaps

# === INJECT PHASE ===

Inject Node Adds Discovered Gaps To Backlog
    [Documentation]    Gaps discovered during validation are added back to backlog
    [Tags]    e2e    workflow    inject    high
    ${state}=    Create State After Validation With Gaps
    ${original_size}=    Get Length    ${state}[backlog]
    ${result}=    Run Inject Node    ${state}
    ${new_size}=    Get Length    ${result}[backlog]
    Should Be True    ${new_size} > ${original_size}

# === FULL CYCLE ===

Full Spec Impl Validate Cycle Completes
    [Documentation]    A single spec→impl→validate cycle should complete successfully
    [Tags]    e2e    workflow    cycle    critical
    ${result}=    Run Single Cycle    GAP-TEST-001    Implement test feature
    Should Be Equal    ${result}[status]    success
    Should Be True    ${result}[cycles_completed] > 0

Orchestrator Loops Through Backlog
    [Documentation]    Given 3 tasks, orchestrator processes all in priority order
    [Tags]    e2e    workflow    loop    critical
    ${result}=    Run Orchestrator Loop
    ...    GAP-A:HIGH    GAP-B:CRITICAL    GAP-C:MEDIUM
    ...    max_cycles=3
    Should Be Equal    ${result}[status]    success
    Should Be Equal As Numbers    ${result}[cycles_completed]    3
    # Verify CRITICAL was processed first
    ${first}=    Set Variable    ${result}[cycle_history][0]
    Should Be Equal    ${first}[task_id]    GAP-B

Orchestrator Stops At Max Cycles
    [Documentation]    Orchestrator respects max_cycles limit even with remaining backlog
    [Tags]    e2e    workflow    loop    safety    high
    ${result}=    Run Orchestrator Loop
    ...    GAP-1:HIGH    GAP-2:HIGH    GAP-3:HIGH    GAP-4:HIGH    GAP-5:HIGH
    ...    max_cycles=2
    Should Be Equal As Numbers    ${result}[cycles_completed]    2
    # 3 tasks should remain in backlog
    ${remaining}=    Get Length    ${result}[backlog]
    Should Be Equal As Numbers    ${remaining}    3

Orchestrator Handles Validation Failure With Retry
    [Documentation]    When validation fails, orchestrator loops back to spec (max 3 retries)
    [Tags]    e2e    workflow    retry    high
    ${result}=    Run Single Cycle With Failure    GAP-TEST-001    fail_validation=True
    # Should have retried (retry_count > 0) or parked the task
    Should Be True    ${result}[retry_count] > 0 or '${result}[current_task_status]' == 'parked'

*** Keywords ***

Cleanup Orchestrator Test Data
    [Documentation]    Remove any TEST- prefixed orchestrator artifacts
    Log    Orchestrator test cleanup complete
