*** Settings ***
Documentation    Agent Platform E2E and Integration Tests
...              Per RD-AGENT-TESTING: ATEST-002, ATEST-003, ATEST-004, ATEST-005, ATEST-006, ATEST-008
...              Migrated from tests/test_agent_platform.py
Library          Collections
Library          ../../libs/AgentPlatformLibrary.py
Resource         ../resources/common.resource
Tags             unit    agents    capability

*** Test Cases ***
# =============================================================================
# ATEST-002: E2E Agent Workflow Tests
# =============================================================================

Test Research Creates Context
    [Documentation]    RESEARCH agent gathers context for a gap
    [Tags]    workflow    atest-002
    ${result}=    Research Creates Context
    Should Be True    ${result['gap_correct']}
    Should Be True    ${result['has_files']}
    Should Be True    ${result['has_evidence']}
    Should Be True    ${result['has_action']}

Test Coding Processes Handoff
    [Documentation]    CODING agent processes handoff from RESEARCH
    [Tags]    workflow    atest-002
    ${result}=    Coding Processes Handoff
    Should Be True    ${result['implemented']}
    Should Be True    ${result['has_files']}
    Should Be True    ${result['has_tests']}

Test Curator Reviews Implementation
    [Documentation]    CURATOR agent reviews and approves implementation
    [Tags]    workflow    atest-002
    ${result}=    Curator Reviews Implementation
    Should Be True    ${result['approved']}
    Should Be True    ${result['has_feedback']}

Test Full Workflow Chain
    [Documentation]    Full workflow: RESEARCH -> CODING -> CURATOR
    [Tags]    workflow    atest-002    e2e
    ${result}=    Full Workflow Chain
    Should Be True    ${result['context_ok']}
    Should Be True    ${result['implementation_ok']}
    Should Be True    ${result['approval_ok']}
    Should Be Equal As Integers    ${result['research_count']}    1
    Should Be Equal As Integers    ${result['coding_count']}    1
    Should Be Equal As Integers    ${result['curator_count']}    1

# =============================================================================
# ATEST-003: Multi-Agent Concurrency Tests
# =============================================================================

Test Parallel Task Claim Single Winner
    [Documentation]    Only one agent can claim a task when multiple try
    [Tags]    concurrency    atest-003    scalability
    ${result}=    Parallel Task Claim Single Winner
    Should Be True    ${result['single_winner']}
    Should Be True    ${result['task_claimed']}

Test Queue Saturation All Processed
    [Documentation]    All tasks are processed when queue is saturated
    [Tags]    concurrency    atest-003    scalability
    ${result}=    Queue Saturation All Processed
    Should Be True    ${result['tasks_added']}
    Should Be True    ${result['all_processed']}

Test No Double Claim
    [Documentation]    Task cannot be claimed twice
    [Tags]    concurrency    atest-003
    ${result}=    No Double Claim
    Should Be True    ${result['first_success']}
    Should Be True    ${result['second_fails']}
    Should Be True    ${result['original_preserved']}

# =============================================================================
# ATEST-006: Kanren-Agent Integration Tests
# =============================================================================

Test Kanren Imports Available
    [Documentation]    Kanren module can be imported
    [Tags]    kanren    atest-006    trust
    ${result}=    Kanren Imports Available
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['rag_filter']}
    Should Be True    ${result['agent_context']}
    Should Be True    ${result['task_context']}

Test Expert Agent On Critical Task
    [Documentation]    Expert agent (trust >= 0.9) can execute CRITICAL tasks
    [Tags]    kanren    atest-006    trust
    ${result}=    Expert Agent On Critical Task
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid']}
    Should Be True    ${result['trust_expert']}
    Should Be True    ${result['can_execute']}
    Should Be True    ${result['no_supervisor']}

Test Supervised Agent Blocked From Critical
    [Documentation]    Supervised agent cannot execute CRITICAL tasks
    [Tags]    kanren    atest-006    trust
    ${result}=    Supervised Agent Blocked From Critical
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['invalid']}
    Should Be True    ${result['trust_supervised']}
    Should Be True    ${result['cannot_execute']}
    Should Be True    ${result['needs_supervisor']}

Test Trust Level Boundaries
    [Documentation]    Trust level boundaries are correctly enforced
    [Tags]    kanren    atest-006    trust
    ${result}=    Trust Level Boundaries
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['expert_at_90']}
    Should Be True    ${result['trusted_at_89']}
    Should Be True    ${result['trusted_at_70']}
    Should Be True    ${result['supervised_at_69']}
    Should Be True    ${result['supervised_at_50']}
    Should Be True    ${result['restricted_at_49']}

Test Kanren RAG Filter With Agent Context
    [Documentation]    KanrenRAGFilter integrates with agent context
    [Tags]    kanren    atest-006    trust
    ${result}=    Kanren RAG Filter With Agent Context
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['assignment_valid']}
    Should Be True    ${result['has_constraints']}
    Should Be True    ${result['has_rule']}

# =============================================================================
# ATEST-005: Trust Evolution Tests
# =============================================================================

Test Trust Formula Coefficients
    [Documentation]    Trust formula has correct coefficients per RULE-011
    [Tags]    trust    atest-005    performance
    ${result}=    Trust Formula Coefficients
    Should Be True    ${result['weights_sum_to_one']}

Test Perfect Agent Gets Max Trust
    [Documentation]    Agent with perfect metrics gets trust = 1.0
    [Tags]    trust    atest-005    performance
    ${result}=    Perfect Agent Gets Max Trust
    Should Be True    ${result['trust_is_one']}

Test Mixed Performance Trust
    [Documentation]    Agent with mixed performance gets proportional trust
    [Tags]    trust    atest-005    performance
    ${result}=    Mixed Performance Trust
    Should Be True    ${result['trust_in_range']}

Test Trust Decay On Failures
    [Documentation]    Trust decreases with failures
    [Tags]    trust    atest-005    performance
    ${result}=    Trust Decay On Failures
    Should Be True    ${result['trust_decreased']}

# =============================================================================
# ATEST-004: Handoff Chain Validation Tests
# =============================================================================

Test Handoff Has Required Fields
    [Documentation]    Handoff contains all required fields
    [Tags]    handoff    atest-004    validate
    ${result}=    Handoff Has Required Fields
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['task_id']}
    Should Be True    ${result['from_agent']}
    Should Be True    ${result['to_agent']}
    Should Be True    ${result['status']}

Test Handoff To Markdown
    [Documentation]    Handoff can be serialized to markdown
    [Tags]    handoff    atest-004    validate
    ${result}=    Handoff To Markdown
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_header']}
    Should Be True    ${result['has_research']}
    Should Be True    ${result['has_coding']}
    Should Be True    ${result['has_context']}

Test Handoff Roundtrip
    [Documentation]    Handoff survives markdown serialization/deserialization
    [Tags]    handoff    atest-004    validate
    ${result}=    Handoff Roundtrip
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['restored']}
    Should Be True    ${result['task_id']}
    Should Be True    ${result['from_agent']}
    Should Be True    ${result['to_agent']}

# =============================================================================
# Benchmark Tests
# =============================================================================

Test Trust Accuracy Target 95
    [Documentation]    Trust score accuracy meets 95% target
    [Tags]    benchmark    performance
    ${result}=    Trust Accuracy Target 95
    Should Be True    ${result['meets_target']}

Test Task Routing Accuracy Target 90
    [Documentation]    Task routing accuracy meets 90% target
    [Tags]    benchmark    performance
    ${result}=    Task Routing Accuracy Target 90
    Should Be True    ${result['meets_target']}

# =============================================================================
# ATEST-008: Recovery Scenarios Tests
# =============================================================================

Test Agent Crash Task Reassignment
    [Documentation]    When agent crashes mid-task, task becomes reclaimable
    [Tags]    recovery    atest-008    reliability
    ${result}=    Agent Crash Task Reassignment
    Should Be True    ${result['first_claimed']}
    Should Be True    ${result['second_claimed']}

Test Task Timeout Releases Claim
    [Documentation]    Task times out and becomes available for other agents
    [Tags]    recovery    atest-008    reliability
    ${result}=    Task Timeout Releases Claim
    Should Be True    ${result['initial_claimed']}
    Should Be True    ${result['reclaimed']}

Test Agent Reconnect Resumes Task
    [Documentation]    Agent reconnects and can resume previously claimed task
    [Tags]    recovery    atest-008    reliability
    ${result}=    Agent Reconnect Resumes Task
    Should Be True    ${result['task_preserved']}

Test Graceful Degradation On MCP Failure
    [Documentation]    System continues with reduced capacity when MCP fails
    [Tags]    recovery    atest-008    reliability
    ${result}=    Graceful Degradation On MCP Failure
    Should Be True    ${result['degraded']}
    Should Be True    ${result['operational']}
    Should Be True    ${result['healthy_count']}

Test Trust Decay On Repeated Failures
    [Documentation]    Agent trust decays when tasks repeatedly fail
    [Tags]    recovery    atest-008    reliability    trust
    ${result}=    Trust Decay On Repeated Failures
    Should Be True    ${result['below_original']}
    Should Be True    ${result['not_too_low']}

Test Circuit Breaker On Service Failures
    [Documentation]    Circuit breaker opens after repeated service failures
    [Tags]    recovery    atest-008    reliability
    ${result}=    Circuit Breaker On Service Failures
    Should Be True    ${result['initial_ok']}
    Should Be True    ${result['two_failures_ok']}
    Should Be True    ${result['three_failures_blocked']}
    Should Be True    ${result['state_open']}
    Should Be True    ${result['reset_ok']}
