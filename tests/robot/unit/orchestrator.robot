*** Settings ***
Documentation    RF-004: Unit Tests - Orchestrator
...              Migrated from tests/test_orchestrator.py
...              Per ORCH-002: Agent orchestrator
Library          Collections
Library          ../../libs/OrchestratorLibrary.py
Library          ../../libs/OrchestratorAdvancedLibrary.py
Force Tags        unit    agents    orchestration    high    agent    validate    WORKFLOW-AUTO-01-v1

*** Test Cases ***
# =============================================================================
# PollableTask Tests
# =============================================================================

Pollable Task From TypeDB Basic
    [Documentation]    GIVEN TypeDB task WHEN converting THEN fields correct
    [Tags]    unit    orchestrator    task    convert
    ${result}=    Pollable Task From TypeDB Basic
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[task_id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[status_correct]
    Should Be True    ${result}[phase_correct]
    Should Be True    ${result}[priority_high]

Pollable Task RD Phase Priority
    [Documentation]    GIVEN RD phase WHEN converting THEN priority MEDIUM
    [Tags]    unit    orchestrator    task    priority
    ${result}=    Pollable Task RD Phase Priority
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[priority_medium]

Pollable Task High Requires Evidence
    [Documentation]    GIVEN HIGH priority THEN requires evidence
    [Tags]    unit    orchestrator    task    evidence
    ${result}=    Pollable Task High Requires Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[requires_evidence]

Pollable Task Medium No Evidence
    [Documentation]    GIVEN MEDIUM priority THEN no evidence required
    [Tags]    unit    orchestrator    task    evidence
    ${result}=    Pollable Task Medium No Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[no_evidence_required]

# =============================================================================
# TaskPriorityQueue Tests
# =============================================================================

Queue Push And Pop
    [Documentation]    GIVEN queue WHEN push and pop THEN works correctly
    [Tags]    unit    orchestrator    queue    basic
    ${result}=    Queue Push And Pop
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[push_success]
    Should Be True    ${result}[size_after_push]
    Should Be True    ${result}[popped_id_correct]
    Should Be True    ${result}[size_after_pop]

Queue Priority Ordering
    [Documentation]    GIVEN mixed priorities WHEN pop THEN highest first
    [Tags]    unit    orchestrator    queue    priority
    ${result}=    Queue Priority Ordering
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[first_critical]
    Should Be True    ${result}[second_high]
    Should Be True    ${result}[third_low]

Queue Duplicate Rejection
    [Documentation]    GIVEN duplicate WHEN push THEN rejected
    [Tags]    unit    orchestrator    queue    dedupe
    ${result}=    Queue Duplicate Rejection
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[first_push_success]
    Should Be True    ${result}[second_push_rejected]
    Should Be True    ${result}[size_is_one]

Queue Peek Without Remove
    [Documentation]    GIVEN queue WHEN peek THEN task not removed
    [Tags]    unit    orchestrator    queue    peek
    ${result}=    Queue Peek Without Remove
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[peeked_id_correct]
    Should Be True    ${result}[still_in_queue]

Queue Remove Specific Task
    [Documentation]    GIVEN task ID WHEN remove THEN task removed
    [Tags]    unit    orchestrator    queue    remove
    ${result}=    Queue Remove Specific Task
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[remove_success]
    Should Be True    ${result}[size_is_one]
    Should Be True    ${result}[remaining_task]

Queue Get By Priority
    [Documentation]    GIVEN mixed priorities WHEN filter THEN correct count
    [Tags]    unit    orchestrator    queue    filter
    ${result}=    Queue Get By Priority
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[high_count]

Queue Max Size Enforcement
    [Documentation]    GIVEN max size WHEN exceeded THEN rejected
    [Tags]    unit    orchestrator    queue    limit
    ${result}=    Queue Max Size Enforcement
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[third_rejected]
    Should Be True    ${result}[size_is_two]

Queue Create From Tasks
    [Documentation]    GIVEN task list WHEN create_queue THEN prioritized
    [Tags]    unit    orchestrator    queue    factory
    ${result}=    Queue Create From Tasks
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[size_correct]
    Should Be True    ${result}[high_first]

# =============================================================================
# AgentInfo Tests
# =============================================================================

Agent Trust Level Expert
    [Documentation]    GIVEN score >= 0.9 THEN expert level
    [Tags]    unit    orchestrator    agent    trust
    ${result}=    Agent Trust Level Expert
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_expert]

Agent Trust Level Trusted
    [Documentation]    GIVEN score >= 0.7 THEN trusted level
    [Tags]    unit    orchestrator    agent    trust
    ${result}=    Agent Trust Level Trusted
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_trusted]

Agent Trust Level Supervised
    [Documentation]    GIVEN score >= 0.5 THEN supervised level
    [Tags]    unit    orchestrator    agent    trust
    ${result}=    Agent Trust Level Supervised
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_supervised]

Agent Trust Level Restricted
    [Documentation]    GIVEN score < 0.5 THEN restricted level
    [Tags]    unit    orchestrator    agent    trust
    ${result}=    Agent Trust Level Restricted
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_restricted]

# =============================================================================
# OrchestratorEngine Tests
# =============================================================================

Engine Register Agent
    [Documentation]    GIVEN agent WHEN register THEN success
    [Tags]    unit    orchestrator    engine    register
    ${result}=    Engine Register Agent
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[register_success]
    Should Be True    ${result}[agent_retrievable]

Engine Register Duplicate Fails
    [Documentation]    GIVEN duplicate WHEN register THEN fails
    [Tags]    unit    orchestrator    engine    duplicate
    ${result}=    Engine Register Duplicate Fails
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[duplicate_rejected]

Engine Unregister Agent
    [Documentation]    GIVEN agent WHEN unregister THEN removed
    [Tags]    unit    orchestrator    engine    unregister
    ${result}=    Engine Unregister Agent
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[unregister_success]
    Should Be True    ${result}[agent_gone]

Engine Get Available Agents
    [Documentation]    GIVEN agents WHEN get available THEN filtered
    [Tags]    unit    orchestrator    engine    filter
    ${result}=    Engine Get Available Agents
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[all_agents]
    Should Be True    ${result}[coding_only]

Engine Stats
    [Documentation]    GIVEN engine WHEN stats THEN complete
    [Tags]    unit    orchestrator    engine    stats
    ${result}=    Engine Stats
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_running]
    Should Be True    ${result}[has_dispatch_count]
    Should Be True    ${result}[has_queue_stats]
    Should Be True    ${result}[has_agents]
